from django.shortcuts import render
from django.views.generic import View
from ipam.models import VLAN

class MapaVlanView(View):
    def get(self, request):
        vlans = VLAN.objects.all().order_by('vid')
        # Tenta apanhar o ID da VLAN que vem do botão que acabámos de criar
        selected_vlan_id = request.GET.get('vlan_id', '')
        
        context = {
            'vlans': vlans,
            'selected_vlan_id': selected_vlan_id, # Enviamos para o HTML
        }
        return render(request, 'netbox_topology_vlan/mapa.html', context)