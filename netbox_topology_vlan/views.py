from django.shortcuts import render
from django.views.generic import View
from dcim.models import Site
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .stp_algorithm import calculate_stp_for_vlan


class MapaVlanView(View):
    def get(self, request):
        sites = Site.objects.all().order_by('name')
        return render(request, 'netbox_topology_vlan/mapa.html', {'sites': sites})



@require_http_methods(["POST"])
def calculate_stp_view(request):
    """View para calcular STP de uma VLAN específica"""
    try:
        vlan_id = request.POST.get('vlan_id')
        
        if not vlan_id:
            return JsonResponse({'error': 'VLAN ID é obrigatório'}, status=400)
        
        result = calculate_stp_for_vlan(int(vlan_id), apply_to_netbox=True)
        
        if result:
            return JsonResponse({
                'status': 'success',
                'root_bridge': result['root_bridge'],
                'port_roles': {str(k): v for k, v in result['port_roles'].items()},
                'port_states': {str(k): v for k, v in result['port_states'].items()},
            })
        else:
            return JsonResponse({'error': 'Falha ao calcular STP'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)