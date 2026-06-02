from netbox.filtersets import NetBoxModelFilterSet
from ipam.models import VLAN
import django_filters

class MapaVlanFilterSet(NetBoxModelFilterSet):
    # Exemplo de filtro padrão se quiseres estender buscas por ID de Site ou VID (VLANID)
    site_id = django_filters.NumberFilter(field_name='site__id')
    vid = django_filters.NumberFilter(field_name='vid')

    class Meta:
        model = VLAN
        fields = ['id', 'vid', 'name', 'status', 'role']