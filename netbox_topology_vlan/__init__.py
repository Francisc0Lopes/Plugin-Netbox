from netbox.plugins import PluginConfig

class TopologyVlanConfig(PluginConfig):
    name = 'netbox_topology_vlan' # Tem de ser exatamente o nome da pasta do plugin
    verbose_name = 'Visualização de Topologias Lógicas (VLANs)'
    description = 'Projeto Final de Curso 25/26'
    version = '0.1.0'
    base_url = 'topology-vlan'
    author = 'Francisco Lopes e João Constantino'

config = TopologyVlanConfig

