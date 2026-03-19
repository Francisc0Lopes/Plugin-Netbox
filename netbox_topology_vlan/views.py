from django.shortcuts import render
from django.views.generic import View
from ipam.models import VLAN

class MapaVlanView(View):
    def get(self, request):
        vlans = VLAN.objects.all().order_by('vid')#Todas as vlans ativas
        
        
        context = {#variaveis para o html
            'vlans': vlans,
        }
        
        return render(request, 'netbox_topology_vlan/mapa.html', context)#renderizar html