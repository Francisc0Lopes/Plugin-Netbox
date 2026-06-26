from dcim.models import Interface
from ipam.models import VLAN

def get_vlan(vlan_ids, site_id=None):
    try:
        vlans_qs = VLAN.objects.filter(id__in=vlan_ids)
        if not vlans_qs.exists():
            return {"Erro": "VLANs não encontradas"}
        vlans = list(vlans_qs)
    except Exception:
        return {"Erro": "Erro ao procurar VLANs"}
    
    # Otimização de Queries com select_related e prefetch_related para evitar o problema de N+1 queries
    interfaces = Interface.objects.filter(
        untagged_vlan__in=vlans
    ) | Interface.objects.filter(
        tagged_vlans__in=vlans
    )
    interfaces = interfaces.select_related('device', 'cable').prefetch_related('tagged_vlans', 'untagged_vlan').distinct()
    
    nos = []
    ligacoes = []
    cabos_processados = set()
    
    for interface in interfaces:
        Equip = interface.device
        
        if site_id and str(Equip.site.id) != str(site_id):
            continue
        
        if interface.cable and interface.cable.id not in cabos_processados:
            cabos = interface.cable
            
            remote_interface = None
            for peer in interface.link_peers:
                if isinstance(peer, Interface):
                    remote_interface = peer
                    break
            
            if isinstance(remote_interface, Interface):
                source_vids = {v.vid for v in interface.tagged_vlans.all()}
                remote_vids = {v.vid for v in remote_interface.tagged_vlans.all()}
                
                source_access_vid = interface.untagged_vlan.vid if interface.untagged_vlan else None
                remote_access_vid = remote_interface.untagged_vlan.vid if remote_interface.untagged_vlan else None
                
                is_source_trunk = len(source_vids) > 0
                is_remote_trunk = len(remote_vids) > 0
                
                if is_source_trunk and is_remote_trunk:
                    vlans_fisicas = source_vids.intersection(remote_vids)
                elif is_source_trunk and not is_remote_trunk:
                    vlans_fisicas = source_vids.intersection({remote_access_vid}) if remote_access_vid else set()
                elif is_remote_trunk and not is_source_trunk:
                    vlans_fisicas = remote_vids.intersection({source_access_vid}) if source_access_vid else set()
                else:
                    vlans_fisicas = set()
                
                vids_selecionadas = {v.vid for v in vlans}
                vlans_efetivas = vlans_fisicas.intersection(vids_selecionadas)
                
                is_pure_access_link = not is_source_trunk and not is_remote_trunk
                passa_access = False
                if is_pure_access_link:
                    if source_access_vid in vids_selecionadas or remote_access_vid in vids_selecionadas:
                        passa_access = True
                
                if len(vlans_efetivas) > 0 or passa_access:
                    cabos_processados.add(cabos.id)
                    
                    vlans_permitidas = [str(vid) for vid in sorted(vlans_efetivas)]
                    
                    if len(vlans_permitidas) == 0:
                        vlans_str = "Nenhuma"
                    elif len(vlans_permitidas) == len(vids_selecionadas) and len(vids_selecionadas) > 1:
                        vlans_str = "Todas"
                    elif len(vlans_permitidas) > 4:
                        vlans_str = f"{len(vlans_permitidas)} VLANs"
                    else:
                        vlans_str = ", ".join(vlans_permitidas) if vlans_permitidas else "N/A"
                        
                    stp_state = interface.custom_field_data.get('stp_port_state') or "forwarding"
        
                    ligacoes.append({
                        "source" : Equip.id, 
                        "target" : remote_interface.device.id, 
                        "source_port" : interface.name, 
                        "source_mode": "Trunk" if is_source_trunk else "Access",
                        "target_port": remote_interface.name,
                        "target_mode": "Trunk" if is_remote_trunk else "Access", 
                        "stp_state": stp_state.capitalize(), 
                        "vlans_trunk": vlans_str, 
                        "vlan_access": str(source_access_vid) if source_access_vid else "N/A"
                    })

                    if not any(n['id'] == Equip.id for n in nos):
                        s_role = getattr(Equip, 'role', getattr(Equip, 'device_role', None))
                        is_root = Equip.custom_field_data.get('stp_root_bridge', False)
                        nos.append({
                            "id": Equip.id,
                            "name": Equip.name, 
                            "url": Equip.get_absolute_url(),
                            "role": s_role.name if s_role else "" ,
                            "is_root_bridge": is_root
                        })

                    if not any(n['id'] == remote_interface.device.id for n in nos):
                        r_device = remote_interface.device
                        r_role = getattr(remote_interface.device, 'role', getattr(remote_interface.device, 'device_role', None))
                        is_root_remote = r_device.custom_field_data.get('stp_root_bridge', False)
                        nos.append({
                            "id": remote_interface.device.id,
                            "name": remote_interface.device.name, 
                            "url": remote_interface.device.get_absolute_url(),
                            "role": r_role.name if r_role else "" ,
                            "is_root_bridge": is_root_remote
                        })
                    
    nomes_vlans = ", ".join([str(v.vid) for v in vlans])
    return {"vlan": nomes_vlans, "nos": nos, "ligacoes": ligacoes}