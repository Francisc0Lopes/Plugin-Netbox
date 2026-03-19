from dcim.models import Interface
from ipam.models import VLAN

def get_vlan(ID_vlan):
    
    try:
        vlan = VLAN.objects.get(id=ID_vlan)
    except VLAN.DoesNotExist:
        return {"Erro": "VLAN não existe"}
    
    interfaces = Interface.objects.filter(untagged_vlan=vlan) | Interface.objects.filter(tagged_vlans=vlan)
    nos = []
    ligacoes = []
    cabos_processados = set()
    
    for interface in interfaces:
        Equip = interface.device
        
        # Adicionar Nó
        if not any(n['id'] == Equip.id for n in nos):
            # Garantir compatibilidade com versões novas do Netbox
            role_obj = getattr(Equip, 'role', getattr(Equip, 'device_role', None))
            nos.append({
                "id": Equip.id,
                "name": Equip.name, 
                "role": role_obj.name if role_obj else "" 
            })
        
        # Processar Cabos e Ligações
        if interface.cable and interface.cable.id not in cabos_processados:
            cabos = interface.cable
            cabos_processados.add(cabos.id)
            
            # Meteu-se para solucionar o erro 500
            remote_interface = None
            for peer in interface.link_peers:
                if isinstance(peer, Interface):
                    remote_interface = peer
                    break
            
            if isinstance(remote_interface, Interface):#Caso o outro lado seja valido
                
                is_remote_access = (remote_interface.untagged_vlan == vlan)
                is_remote_trunk = (vlan in remote_interface.tagged_vlans.all())
                
                if is_remote_access or is_remote_trunk:
                    ligacoes.append({
                        "source" : Equip.id, 
                        "target" : remote_interface.device.id, 
                        "source_port" : interface.name, 
                        "source_mode": "Trunk" if vlan in interface.tagged_vlans.all() else "Access",
                        "target_port": remote_interface.name,
                        "target_mode": "Trunk" if is_remote_trunk else "Access", 
                        "stp_state": "Forwarding" 
                    })       
                    
    return {"vlan": vlan.vid, "nos": nos, "ligacoes": ligacoes}