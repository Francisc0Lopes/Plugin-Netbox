# stp_algorithm.py - VERSÃO CORRIGIDA E OTIMIZADA
from dcim.models import Device, Interface
from ipam.models import VLAN
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class STPCalculator:
    """
    Calcula a topologia STP para uma determinada VLAN de forma segura e atómica.
    """

    def __init__(self, vlan_id):
        self.vlan_id = vlan_id
        self.vlan = VLAN.objects.filter(id=vlan_id).first()
        self.switches = {}  # device_id -> Device object
        self.links = []  # Lista de conexões entre switches
        self.bridge_macs = {}  # device_id -> MAC address
        self.bridge_priorities = {}  # device_id -> Priority
        self.root_bridge = None
        self.root_paths = {}  # device_id -> cost to root
        self.spanning_tree = defaultdict(list)  # device_id -> lista de devices conectados na árvore
        self.port_roles = {}  # (device_id, remote_device_id) -> 'root' | 'designated' | 'alternate'
        self.port_states = {}  # (device_id, remote_device_id) -> 'forwarding' | 'blocking' | 'learning'

    def extract_topology(self):
        if not self.vlan:
            logger.warning(f"VLAN {self.vlan_id} não encontrada")
            return False

        # Otimização: Carrega já os dispositivos associados para evitar queries em loop
        interfaces = (
            Interface.objects.filter(untagged_vlan=self.vlan) |
            Interface.objects.filter(tagged_vlans=self.vlan)
        ).select_related('device').distinct()

        for interface in interfaces:
            device = interface.device
            if device.id not in self.switches:
                self.switches[device.id] = device

        processed_cables = set()
        for interface in interfaces:
            if not interface.cable:
                continue

            cable_id = interface.cable.id
            if cable_id in processed_cables:
                continue

            # Usar o link_peers de forma segura para evitar overhead m2m recursivo do NetBox
            remote_interface = None
            try:
                peers = interface.link_peers
                for peer in peers:
                    if isinstance(peer, Interface):
                        remote_interface = peer
                        break
            except Exception:
                continue

            if remote_interface and remote_interface.device:
                source_device = interface.device
                target_device = remote_interface.device

                source_vlans = set(interface.tagged_vlans.values_list('id', flat=True))
                if interface.untagged_vlan:
                    source_vlans.add(interface.untagged_vlan.id)

                target_vlans = set(remote_interface.tagged_vlans.values_list('id', flat=True))
                if remote_interface.untagged_vlan:
                    target_vlans.add(remote_interface.untagged_vlan.id)

                if self.vlan_id in source_vlans and self.vlan_id in target_vlans:
                    self.links.append({
                        'source': source_device.id,
                        'target': target_device.id,
                        'source_interface': interface.name,
                        'target_interface': remote_interface.name,
                        'cost': 19  # Default cost para Gigabit Ethernet
                    })
                    processed_cables.add(cable_id)

        return len(self.switches) > 0

    def load_stp_config(self):
        for device_id, device in self.switches.items():
            try:
                cf_priority = device.custom_field_data.get('stp_priority', 32768)
                cf_mac = getattr(device, 'asset_tag', None) or str(device_id)

                self.bridge_priorities[device_id] = int(cf_priority)
                self.bridge_macs[device_id] = cf_mac
            except Exception as e:
                logger.warning(f"Erro ao carregar config STP para {device.name}: {e}")
                self.bridge_priorities[device_id] = 32768
                self.bridge_macs[device_id] = str(device_id)

    def elect_root_bridge(self):
        if not self.switches:
            return None

        candidates = sorted(
            self.switches.keys(),
            key=lambda dev_id: (
                self.bridge_priorities.get(dev_id, 32768),
                self.bridge_macs.get(dev_id, '')
            )
        )

        self.root_bridge = candidates[0]
        logger.info(f"Root Bridge eleito: {self.switches[self.root_bridge].name}")
        return self.root_bridge

    def calculate_path_costs(self):
        if not self.root_bridge:
            return

        queue = deque([(self.root_bridge, 0)])
        visited = {self.root_bridge}
        self.root_paths[self.root_bridge] = 0

        while queue:
            current_id, current_cost = queue.popleft()

            neighbors = set()
            for link in self.links:
                if link['source'] == current_id:
                    neighbors.add((link['target'], link['cost']))
                elif link['target'] == current_id:
                    neighbors.add((link['source'], link['cost']))

            for neighbor_id, link_cost in neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    new_cost = current_cost + link_cost
                    self.root_paths[neighbor_id] = new_cost
                    queue.append((neighbor_id, new_cost))

        for device_id in self.switches:
            if device_id not in self.root_paths:
                self.root_paths[device_id] = float('inf')

    def build_spanning_tree(self):
        if not self.root_bridge:
            return

        for device_id in sorted(self.switches.keys()):
            if device_id == self.root_bridge:
                continue

            best_link = None
            best_cost = float('inf')

            for link in self.links:
                if link['target'] == device_id:
                    source_id = link['source']
                    total_cost = self.root_paths[source_id] + link['cost']
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_link = link
                        
                elif link['source'] == device_id:
                    target_id = link['target']
                    total_cost = self.root_paths[target_id] + link['cost']
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_link = {
                            'source': link['target'],
                            'target': link['source'],
                            'source_interface': link['target_interface'],
                            'target_interface': link['source_interface'],
                            'cost': link['cost']
                        }

            if best_link:
                self.spanning_tree[best_link['source']].append(
                    (best_link['target'], best_link)
                )

    def assign_port_roles(self):
        # Reset roles
        self.port_roles.clear()
        
        # Root ports
        for device_id in self.switches:
            if device_id == self.root_bridge:
                continue

            for neighbor_id, link in self.spanning_tree.get(device_id, []):
                if neighbor_id in self.spanning_tree or neighbor_id == self.root_bridge:
                    self.port_roles[(device_id, neighbor_id)] = 'root'

        # Designated ports
        for link in self.links:
            source_id = link['source']
            target_id = link['target']

            if source_id == self.root_bridge:
                self.port_roles[(source_id, target_id)] = 'designated'
            elif self.root_paths[source_id] < self.root_paths[target_id]:
                self.port_roles[(source_id, target_id)] = 'designated'

        # Alternate ports
        for link in self.links:
            source_id = link['source']
            target_id = link['target']
            
            if (source_id, target_id) not in self.port_roles:
                self.port_roles[(source_id, target_id)] = 'alternate'

    def assign_port_states(self):
        self.port_states.clear()
        for (source_id, target_id), role in self.port_roles.items():
            if role in ['root', 'designated']:
                self.port_states[(source_id, target_id)] = 'forwarding'
            elif role == 'alternate':
                self.port_states[(source_id, target_id)] = 'blocking'
            else:
                self.port_states[(source_id, target_id)] = 'disabled'

    def get_port_state_and_role(self, source_device_id, target_device_id):
        key = (source_device_id, target_device_id)
        return {
            'role': self.port_roles.get(key, 'disabled'),
            'state': self.port_states.get(key, 'disabled')
        }

    def apply_to_netbox(self):
        """
        Salva de forma limpa e atómica os estados teóricos calculados pelo background job.
        """
        try:
            # Atualizar flags de Root Bridge nos Dispositivos do nosso escopo
            for device_id, device in self.switches.items():
                is_root = (device_id == self.root_bridge)
                # Só grava se houver alteração real para evitar locks na BD
                if device.custom_field_data.get('stp_root_bridge') != is_root:
                    device.custom_field_data['stp_root_bridge'] = is_root
                    device.save()

            # Atualizar estados das Interfaces envolvidas nos links
            for link in self.links:
                source_id = link['source']
                target_id = link['target']
                
                # Update Source Port
                try:
                    src_iface = Interface.objects.get(device_id=source_id, name=link['source_interface'])
                    info = self.get_port_state_and_role(source_id, target_id)
                    
                    if (src_iface.custom_field_data.get('stp_port_state') != info['state'] or 
                        src_iface.custom_field_data.get('stp_port_role') != info['role']):
                        
                        src_iface.custom_field_data['stp_port_state'] = info['state']
                        src_iface.custom_field_data['stp_port_role'] = info['role']
                        src_iface.save()
                except Interface.DoesNotExist:
                    pass

                # Update Target Port
                try:
                    tgt_iface = Interface.objects.get(device_id=target_id, name=link['target_interface'])
                    info = self.get_port_state_and_role(target_id, source_id)
                    
                    if (tgt_iface.custom_field_data.get('stp_port_state') != info['state'] or 
                        tgt_iface.custom_field_data.get('stp_port_role') != info['role']):
                        
                        tgt_iface.custom_field_data['stp_port_state'] = info['state']
                        tgt_iface.custom_field_data['stp_port_role'] = info['role']
                        tgt_iface.save()
                except Interface.DoesNotExist:
                    pass

            return True
        except Exception as e:
            logger.error(f"Erro ao aplicar STP ao NetBox: {e}")
            return False

    def calculate(self):
        if not self.extract_topology():
            return False

        self.load_stp_config()
        self.elect_root_bridge()
        self.calculate_path_costs()
        self.build_spanning_tree()
        self.assign_port_roles()
        self.assign_port_states()
        return True

    def get_results(self):
        return {
            'vlan_id': self.vlan_id,
            'root_bridge_id': self.root_bridge,
            'root_paths': self.root_paths,
            'port_roles': {f"{k[0]}-{k[1]}": v for k, v in self.port_roles.items()},
            'port_states': {f"{k[0]}-{k[1]}": v for k, v in self.port_states.items()}
        }


def calculate_stp_for_vlan(vlan_id, apply_to_netbox=False):
    calculator = STPCalculator(vlan_id)
    if not calculator.calculate():
        return None
    if apply_to_netbox:
        calculator.apply_to_netbox()
    return calculator.get_results()


def calculate_stp_for_all_vlans(apply_to_netbox=False):
    vlans = VLAN.objects.all()
    results = {}
    for vlan in vlans:
        result = calculate_stp_for_vlan(vlan.id, apply_to_netbox=apply_to_netbox)
        if result:
            results[vlan.id] = result
    return results