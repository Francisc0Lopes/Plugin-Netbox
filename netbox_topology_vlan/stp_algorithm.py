from dcim.models import Device, Interface
from ipam.models import VLAN
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class STPCalculator:
    """
    Calcula a topologia STP para uma determinada VLAN.
    """

    def __init__(self, vlan_id):
        """
        Inicializa o calculador STP para uma VLAN específica.
        
        Args:
            vlan_id: ID da VLAN a processar
        """
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
        """
        Extrai a topologia da VLAN - encontra todos os switches e ligações.
        """
        if not self.vlan:
            logger.warning(f"VLAN {self.vlan_id} não encontrada")
            return False

        # Encontrar todas as interfaces dessa VLAN
        interfaces = (
            Interface.objects.filter(untagged_vlan=self.vlan) |
            Interface.objects.filter(tagged_vlans=self.vlan)
        ).select_related('device').distinct()

        # Extrair switches únicos
        for interface in interfaces:
            device = interface.device
            if device.id not in self.switches:
                self.switches[device.id] = device

        # Extrair ligações (cabos) entre switches
        processed_cables = set()
        for interface in interfaces:
            if not interface.cable:
                continue

            cable_id = interface.cable.id
            if cable_id in processed_cables:
                continue

            # Encontrar a interface remota
            remote_interface = None
            for peer in interface.link_peers:
                if isinstance(peer, Interface):
                    remote_interface = peer
                    break

            if remote_interface and remote_interface.device:
                source_device = interface.device
                target_device = remote_interface.device

                # Verificar se ambos estão na VLAN
                source_vlans = set(interface.tagged_vlans.values_list('id', flat=True))
                if interface.untagged_vlan:
                    source_vlans.add(interface.untagged_vlan.id)

                target_vlans = set(remote_interface.tagged_vlans.values_list('id', flat=True))
                if remote_interface.untagged_vlan:
                    target_vlans.add(remote_interface.untagged_vlan.id)

                # Só add se ambos têm a VLAN
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
        """
        Carrega a configuração STP dos custom fields.
        """
        for device_id, device in self.switches.items():
            try:
                # Obter custom field values
                cf_priority = device.custom_field_data.get('stp_priority', 32768)
                cf_mac = getattr(device, 'asset_tag', None) or str(device_id)

                self.bridge_priorities[device_id] = int(cf_priority)
                self.bridge_macs[device_id] = cf_mac
            except Exception as e:
                logger.warning(f"Erro ao carregar config STP para {device.name}: {e}")
                # Defaults
                self.bridge_priorities[device_id] = 32768
                self.bridge_macs[device_id] = str(device_id)

    def elect_root_bridge(self):
        """
        Elege o Root Bridge usando o algoritmo STP:
        1. Menor prioridade
        2. Se empate, menor MAC address
        """
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
        logger.info(f"Root Bridge eleito: {self.switches[self.root_bridge].name} (ID: {self.root_bridge})")
        return self.root_bridge

    def calculate_path_costs(self):
        """
        Calcula o custo do caminho para o root bridge usando BFS.
        """
        if not self.root_bridge:
            return

        # BFS para calcular custos
        queue = deque([(self.root_bridge, 0)])
        visited = {self.root_bridge}
        self.root_paths[self.root_bridge] = 0

        while queue:
            current_id, current_cost = queue.popleft()

            # Encontrar vizinhos
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

        # Switches não alcançados ficam com custo infinito
        for device_id in self.switches:
            if device_id not in self.root_paths:
                self.root_paths[device_id] = float('inf')

    def build_spanning_tree(self):
        """
        Constrói a árvore spanning usando o algoritmo de menor custo.
        """
        if not self.root_bridge:
            return

        # Para cada switch (exceto root), encontra a melhor porta para o root
        for device_id in sorted(self.switches.keys()):
            if device_id == self.root_bridge:
                continue

            best_link = None
            best_cost = float('inf')

            # Procurar links onde este device é o destino
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

            # Adicionar à árvore spanning
            if best_link:
                self.spanning_tree[best_link['source']].append(
                    (best_link['target'], best_link)
                )

    def assign_port_roles(self):
        """
        Atribui os roles de porta: Root, Designated, Alternate.
        """
        # Root ports
        for device_id in self.switches:
            if device_id == self.root_bridge:
                continue

            for neighbor_id, link in self.spanning_tree.get(device_id, []):
                # A porta que aponta para o root é "root port"
                if neighbor_id in self.spanning_tree or neighbor_id == self.root_bridge:
                    key = (device_id, neighbor_id)
                    self.port_roles[key] = 'root'

        # Designated ports (no root bridge)
        for link in self.links:
            source_id = link['source']
            target_id = link['target']

            # Se source é root ou está na árvore com custo menor para target
            if source_id == self.root_bridge:
                key = (source_id, target_id)
                self.port_roles[key] = 'designated'
            elif self.root_paths[source_id] < self.root_paths[target_id]:
                key = (source_id, target_id)
                self.port_roles[key] = 'designated'

        # Alternate ports (não estão na árvore, têm custo maior)
        for link in self.links:
            source_id = link['source']
            target_id = link['target']
            key = (source_id, target_id)

            if key not in self.port_roles:
                self.port_roles[key] = 'alternate'

    def assign_port_states(self):
        """
        Atribui os estados de porta baseado nos roles.
        Estados: forwarding, blocking, learning, disabled
        """
        for (source_id, target_id), role in self.port_roles.items():
            key = (source_id, target_id)

            if role == 'root' or role == 'designated':
                self.port_states[key] = 'forwarding'
            elif role == 'alternate':
                self.port_states[key] = 'blocking'
            else:
                self.port_states[key] = 'disabled'

    def get_port_state_and_role(self, source_device_id, target_device_id):
        """
        Obtém o estado e role de uma porta específica.
        """
        key = (source_device_id, target_device_id)
        return {
            'role': self.port_roles.get(key, 'disabled'),
            'state': self.port_states.get(key, 'disabled')
        }

    def apply_to_netbox(self):
        """
        Aplica os resultados ao NetBox atualizando os custom fields.
        """
        try:
            # Atualizar Root Bridge
            if self.root_bridge:
                root_device = self.switches[self.root_bridge]
                root_device.custom_field_data['stp_root_bridge'] = True
                root_device.save()
                logger.info(f"✅ Root Bridge definido: {root_device.name}")

            # Atualizar non-root switches
            for device_id in self.switches:
                if device_id != self.root_bridge:
                    device = self.switches[device_id]
                    device.custom_field_data['stp_root_bridge'] = False
                    device.save()

            # Atualizar interfaces
            for link in self.links:
                source_id = link['source']
                target_id = link['target']
                
                # Interface de source
                try:
                    source_interface = Interface.objects.get(
                        device_id=source_id,
                        name=link['source_interface']
                    )
                    port_info = self.get_port_state_and_role(source_id, target_id)
                    source_interface.custom_field_data['stp_port_state'] = port_info['state']
                    source_interface.custom_field_data['stp_port_role'] = port_info['role']
                    source_interface.save()
                except Interface.DoesNotExist:
                    pass

                # Interface de target
                try:
                    target_interface = Interface.objects.get(
                        device_id=target_id,
                        name=link['target_interface']
                    )
                    port_info = self.get_port_state_and_role(target_id, source_id)
                    target_interface.custom_field_data['stp_port_state'] = port_info['state']
                    target_interface.custom_field_data['stp_port_role'] = port_info['role']
                    target_interface.save()
                except Interface.DoesNotExist:
                    pass

            logger.info(f"✅ Configuração STP aplicada ao NetBox para VLAN {self.vlan_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao aplicar STP ao NetBox: {e}")
            return False

    def calculate(self):
        """
        Executa o algoritmo STP completo.
        """
        logger.info(f"🔄 Iniciando cálculo STP para VLAN {self.vlan_id}...")

        if not self.extract_topology():
            logger.error(f"Nenhuma topologia encontrada para VLAN {self.vlan_id}")
            return False

        self.load_stp_config()
        self.elect_root_bridge()
        self.calculate_path_costs()
        self.build_spanning_tree()
        self.assign_port_roles()
        self.assign_port_states()
        
        logger.info(f"✅ Cálculo STP concluído para VLAN {self.vlan_id}")
        return True

    def get_results(self):
        """
        Retorna os resultados do cálculo STP.
        """
        return {
            'vlan_id': self.vlan_id,
            'root_bridge': self.switches[self.root_bridge].name if self.root_bridge else None,
            'root_bridge_id': self.root_bridge,
            'root_paths': self.root_paths,
            'port_roles': self.port_roles,
            'port_states': self.port_states,
            'spanning_tree_links': [
                (self.switches[src].name, self.switches[tgt].name)
                for src in self.spanning_tree
                for tgt, _ in self.spanning_tree[src]
            ]
        }


def calculate_stp_for_vlan(vlan_id, apply_to_netbox=False):
    """
    Função conveniência para calcular STP de uma VLAN.
    
    Args:
        vlan_id: ID da VLAN
        apply_to_netbox: Se True, atualiza os custom fields no NetBox
        
    Returns:
        dict com resultados STP
    """
    calculator = STPCalculator(vlan_id)
    
    if not calculator.calculate():
        return None
    
    if apply_to_netbox:
        calculator.apply_to_netbox()
    
    return calculator.get_results()


def calculate_stp_for_all_vlans(apply_to_netbox=False):
    """
    Calcula STP para TODAS as VLANs da rede.
    Útil para job em segundo plano.
    """
    vlans = VLAN.objects.all()
    results = {}
    
    for vlan in vlans:
        logger.info(f"Processando VLAN {vlan.vid}...")
        result = calculate_stp_for_vlan(vlan.id, apply_to_netbox=apply_to_netbox)
        if result:
            results[vlan.id] = result
    
    return results