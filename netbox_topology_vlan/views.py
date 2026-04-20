from django.shortcuts import render
from django.views.generic import View
from ipam.models import VLAN
from dcim.models import Site

class MapaVlanView(View):
    def get(self, request):
        vlans = VLAN.objects.all().order_by('vid')
        sites = Site.objects.all().order_by('name') # <--- Vai buscar todos os sites
        selected_vlan_id = request.GET.get('vlan_id', '')
        
        context = {
            'vlans': vlans,
            'sites': sites, # <--- Envia a caixa de sites para o HTML
            'selected_vlan_id': selected_vlan_id, 
        }
        return render(request, 'netbox_topology_vlan/mapa.html', context)
