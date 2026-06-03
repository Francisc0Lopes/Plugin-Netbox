from netbox.filtersets import NetBoxModelFilterSet
from ipam.models import VLAN
import django_filters

class MapaVlanFilterSet(NetBoxModelFilterSet):
        # Filtros de VLAN
    site_id = django_filters.NumberFilter(
        field_name='site__id', 
        label='Site ID'
    )
    
    site_name = django_filters.CharFilter(
        field_name='site__name', 
        lookup_expr='icontains',
        label='Site Name'
    )
    
    vid = django_filters.NumberFilter(
        field_name='vid',
        label='VLAN ID (VID)'
    )
    
    vid_range = django_filters.BaseInFilter(
        field_name='vid',
        label='VLAN ID Range (comma-separated)',
    )
    
    status = django_filters.CharFilter(
        field_name='status',
        lookup_expr='iexact',
        label='Status (Forwarding, Learning , Blocking , Listening, Disabled)'
    )
    
    role = django_filters.CharFilter(
        field_name='role',
        lookup_expr='icontains',
        label='Role/Type'
    )
    
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='VLAN Name'
    )

    class Meta:
        model = VLAN
        fields = ['id', 'vid', 'name', 'status', 'role', 'site']
