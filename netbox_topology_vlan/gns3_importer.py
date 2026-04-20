import json
import traceback
from django.db import transaction
from dcim.models import Device, DeviceType, Site, Interface, Cable, Manufacturer
from ipam.models import VLAN 

try:
    from dcim.models import DeviceRole as Role
except ImportError:
    from dcim.models import Role

def process_gns3_file(file_content):
    try:
        data = json.loads(file_content)
        nodes = data.get('topology', {}).get('nodes', [])
        links = data.get('topology', {}).get('links', [])
    except json.JSONDecodeError:
        return {"Erro": "O ficheiro enviado não é um GNS3 válido (JSON corrompido)."}

    try:
        with transaction.atomic():
            site, _ = Site.objects.get_or_create(name="Lab GNS3", slug="lab-gns3", defaults={'status': 'active'})
            manufacturer, _ = Manufacturer.objects.get_or_create(name="GNS3 Generic", slug="gns3-generic")
            
            role_router, _ = Role.objects.get_or_create(name="Router", slug="router", defaults={'color': "0000ff"})
            role_switch, _ = Role.objects.get_or_create(name="Switch", slug="switch", defaults={'color': "00ff00"})
            role_pc, _ = Role.objects.get_or_create(name="PC", slug="pc", defaults={'color': "9e9e9e"})
            
            type_router, _ = DeviceType.objects.get_or_create(model="GNS3 Router", slug="gns3-router", manufacturer=manufacturer)
            type_switch, _ = DeviceType.objects.get_or_create(model="GNS3 Switch", slug="gns3-switch", manufacturer=manufacturer)
            type_pc, _ = DeviceType.objects.get_or_create(model="GNS3 PC", slug="gns3-pc", manufacturer=manufacturer)

            #
            vlan_gns3, _ = VLAN.objects.get_or_create(
                vid=1, 
                defaults={'name': 'VLAN GNS3 Auto', 'status': 'active'}
            )

            created_devices = 0
            device_map = {} 

            #CRIAR EQUIPAMENTOS
            for node in nodes:
                node_id = node.get('node_id')
                name = node.get('name')
                node_type = node.get('node_type')

                role = role_router
                dtype = type_router
                if node_type == "ethernet_switch":
                    role = role_switch
                    dtype = type_switch
                elif node_type == "vpcs":
                    role = role_pc
                    dtype = type_pc

                try:
                    device, created = Device.objects.get_or_create(
                        name=name, site=site, defaults={'role': role, 'device_type': dtype, 'status': 'active'}
                    )
                except Exception:
                    device, created = Device.objects.get_or_create(
                        name=name, site=site, defaults={'device_role': role, 'device_type': dtype, 'status': 'active'}
                    )

                if created:
                    created_devices += 1
                
                device_map[node_id] = device

            created_cables = 0
            
            #CRIAR INTERFACES, CABOS E ATRIBUIR VLAN
            for link in links:
                link_nodes = link.get('nodes', [])
                if len(link_nodes) == 2:
                    node1_data = link_nodes[0]
                    node2_data = link_nodes[1]

                    dev1 = device_map.get(node1_data.get('node_id'))
                    dev2 = device_map.get(node2_data.get('node_id'))
                    
                    if dev1 and dev2:
                        iface1_name = node1_data.get('label', {}).get('text', f"port{node1_data.get('port_number')}")
                        iface2_name = node2_data.get('label', {}).get('text', f"port{node2_data.get('port_number')}")

                        iface1, _ = Interface.objects.get_or_create(
                            device=dev1, name=iface1_name, 
                            defaults={'type': '1000base-t', 'mode': 'access', 'untagged_vlan': vlan_gns3}
                        )
                        iface2, _ = Interface.objects.get_or_create(
                            device=dev2, name=iface2_name, 
                            defaults={'type': '1000base-t', 'mode': 'access', 'untagged_vlan': vlan_gns3}
                        )

                        # Se as interfaces já existiam mas não tinham VLAN, forçamos a VLAN agora
                        if not iface1.untagged_vlan:
                            iface1.mode = 'access'
                            iface1.untagged_vlan = vlan_gns3
                            iface1.save()
                        
                        if not iface2.untagged_vlan:
                            iface2.mode = 'access'
                            iface2.untagged_vlan = vlan_gns3
                            iface2.save()

                        # Liga os cabos
                        if not iface1.cable and not iface2.cable:
                            try:
                                Cable.objects.create(a_terminations=[iface1], b_terminations=[iface2])
                                created_cables += 1
                            except Exception:
                                pass 

            return {"status": "sucesso", "criados": created_devices, "cabos": created_cables}

    except Exception as e:
        error_msg = str(e)
        print(f"ERRO CRÍTICO NO IMPORT: {error_msg}")
        traceback.print_exc()
        return {"Erro": f"Falha ao criar no NetBox: {error_msg}"}