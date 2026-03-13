from dcim.models import Interface, Cable
from ipam.models import VLAN

def get_vlan(ID_vlan):
    
    try:
        vlan = VLAN.objects.get(id= ID_vlan)
    except VLAN.DoesNotExist:
        return {"Erro": "VLAN não existe"}
    
    interfaces = Interface.objects.filter(untagged_vlan=vlan) | Interface.objects.filter(tagged_vlans=vlan)
    nos = []
    ligacoes = []
    cabos_processados = set()
    
    for interface in interfaces:
        Equip = interface.device
        
        if not any
    
    