from netbox.plugins import PluginMenuItem

menu_items = (
    PluginMenuItem(
        link='plugins:netbox_topology_vlan:mapa',
        link_text='Mapa de VLANs',
        permissions=['dcim.view_interface'], #So para quem pode ver interfaces
    ),
)