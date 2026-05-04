from dcim.models import Interface
from ipam.models import VLAN

def get_vlan(vlan_ids, site_id=None):
    try:
        vlans_qs = VLAN.objects.filter(id__in=vlan_ids)
        if not vlans_qs.exists():
            return {"Erro": "VLANs não encontradas"}
        vlans = list(vlans_qs) # Converte para lista para ser mais rápido
    except Exception:
        return {"Erro": "Erro ao procurar VLANs"}
    
    interfaces = (Interface.objects.filter(untagged_vlan__in=vlans) | 
                  Interface.objects.filter(tagged_vlans__in=vlans)).distinct()
    
    nos = []
    ligacoes = []
    cabos_processados = set()
    
    for interface in interfaces:
        Equip = interface.device
        
        if site_id and str(Equip.site.id) != str(site_id):
            continue  # Se o equipamento não for deste site, ignora e salta para o próximo!
        
        
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
                
                # Interseção rigorosa (O que consegue realmente atravessar o cabo?)
                if is_source_trunk and is_remote_trunk:
                    vlans_fisicas = source_vids.intersection(remote_vids)
                elif is_source_trunk and not is_remote_trunk:
                    vlans_fisicas = source_vids.intersection({remote_access_vid}) if remote_access_vid else set()
                elif is_remote_trunk and not is_source_trunk:
                    vlans_fisicas = remote_vids.intersection({source_access_vid}) if source_access_vid else set()
                else:
                    vlans_fisicas = set()
                    
                # Filtrar pelo que o utilizador selecionou no menu do NetBox
                vids_selecionadas = {v.vid for v in vlans}
                vlans_efetivas = vlans_fisicas.intersection(vids_selecionadas)
                
                # Validar se é uma ligação pura de Access (ex: Switch para PC)
                is_pure_access_link = not is_source_trunk and not is_remote_trunk
                passa_access = False
                if is_pure_access_link:
                    if source_access_vid in vids_selecionadas or remote_access_vid in vids_selecionadas:
                        passa_access = True
                
                # Só adiciona a ligação E os equipamentos se a rede passar!
                if len(vlans_efetivas) > 0 or passa_access:
                    cabos_processados.add(cabos.id)
                    
                    vlans_permitidas = [str(vid) for vid in sorted(vlans_efetivas)]
                    
                    # Lógica do Pop-up
                    if len(vlans_permitidas) == 0:
                        vlans_str = "Nenhuma"
                    elif len(vlans_permitidas) == len(vids_selecionadas) and len(vids_selecionadas) > 1:
                        vlans_str = "Todas"
                    elif len(vlans_permitidas) > 3:
                        vlans_str = f"{len(vlans_permitidas)} VLANs"
                    else:
                        vlans_str = ", ".join(vlans_permitidas) if vlans_permitidas else "N/A"

                    # Adiciona a linha (Cabo)
                    ligacoes.append({
                        "source" : Equip.id, 
                        "target" : remote_interface.device.id, 
                        "source_port" : interface.name, 
                        "source_mode": "Trunk" if is_source_trunk else "Access",
                        "target_port": remote_interface.name,
                        "target_mode": "Trunk" if is_remote_trunk else "Access", 
                        "stp_state": "Forwarding",
                        "vlans_trunk": vlans_str  
                    })

                    # Adiciona a máquina de origem (só se ainda não estiver na lista)
                    if not any(n['id'] == Equip.id for n in nos):
                        s_role = getattr(Equip, 'role', getattr(Equip, 'device_role', None))
                        nos.append({
                            "id": Equip.id,
                            "name": Equip.name, 
                            "url": remote_interface.device.get_absolute_url(),
                            "role": s_role.name if s_role else "" 
                        })

                    # Adiciona a máquina de destino (só se ainda não estiver na lista)
                    if not any(n['id'] == remote_interface.device.id for n in nos):
                        r_role = getattr(remote_interface.device, 'role', getattr(remote_interface.device, 'device_role', None))
                        nos.append({
                            "id": remote_interface.device.id,
                            "name": remote_interface.device.name, 
                            "url": remote_interface.device.get_absolute_url(),
                            "role": r_role.name if r_role else "" 
                        })
                    
    nomes_vlans = ", ".join([str(v.vid) for v in vlans])
    return {"vlan": nomes_vlans, "nos": nos, "ligacoes": ligacoes}