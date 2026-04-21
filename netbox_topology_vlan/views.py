from django.shortcuts import render
from django.views.generic import View
from dcim.models import Site

class MapaVlanView(View):
    def get(self, request):
        sites = Site.objects.all().order_by('name')
        return render(request, 'netbox_topology_vlan/mapa.html', {'sites': sites})