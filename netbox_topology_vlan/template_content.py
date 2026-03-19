from netbox.plugins import PluginTemplateExtension

class VlanTopologyButton(PluginTemplateExtension):
    """
    Adiciona um botão de acesso rápido ao mapa na página de detalhes de uma VLAN.
    """
    model = 'ipam.vlan'

    def buttons(self):
        # Renderiza um botão que envia o ID da VLAN para a tua vista do mapa
        return self.render('netbox_topology_vlan/inc/topology_button.html')

template_extensions = [VlanTopologyButton]