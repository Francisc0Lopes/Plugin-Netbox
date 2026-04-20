from dcim.models import Interface
from ipam.models import VLAN

def get_vlan(vlan_ids, site_id=None):
    try:
        vlans = VLAN.objects.filter(id__in=vlan_ids)
        if not vlans.exists():
            return {"Erro": "VLANs não encontradas"}
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
        
        
        if not any(n['id'] == Equip.id for n in nos):
            role_obj = getattr(Equip, 'role', getattr(Equip, 'device_role', None))
            nos.append({
                "id": Equip.id,
                "name": Equip.name, 
                "role": role_obj.name if role_obj else "" ,
                "url" : Equip.get_absolute_url()
            })
        
        if interface.cable and interface.cable.id not in cabos_processados:
            cabos = interface.cable
            cabos_processados.add(cabos.id)
            
            remote_interface = None
            for peer in interface.link_peers:
                if isinstance(peer, Interface):
                    remote_interface = peer
                    break
            
            if isinstance(remote_interface, Interface):
                is_remote_access = remote_interface.untagged_vlan in vlans
                is_remote_trunk = any(v in remote_interface.tagged_vlans.all() for v in vlans)
                is_source_trunk = any(v in interface.tagged_vlans.all() for v in vlans)
                
                if is_remote_access or is_remote_trunk:
                    vlans_permitidas = []
                    if is_source_trunk:
                        vlans_permitidas = [str(v.vid) for v in interface.tagged_vlans.all()]
                    elif is_remote_trunk:
                        vlans_permitidas = [str(v.vid) for v in remote_interface.tagged_vlans.all()]
                    
                    vlans_str = ", ".join(vlans_permitidas) if vlans_permitidas else "N/A"

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
                    
    nomes_vlans = ", ".join([str(v.vid) for v in vlans])
    return {"vlan": nomes_vlans, "nos": nos, "ligacoes": ligacoes}