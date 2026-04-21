from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ipam.models import VLAN
from dcim.models import Interface
from ..utils import get_vlan
from ..gns3_importer import process_gns3_file

class VlanTopologyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        vlan_ids_str = request.query_params.get('vlan_id')
        site_id = request.query_params.get('site_id')
        
        if not vlan_ids_str:
            return Response({"Erro": "Falta o vlan_id no URL"}, status=400)
        
        try:
            vlan_ids = [int(vid.strip()) for vid in vlan_ids_str.split(',')]
        except ValueError:
            return Response({"Erro": "Formato de ID inválido"}, status=400)
            
        resultado = get_vlan(vlan_ids, site_id)
        if "Erro" in resultado:
            return Response(resultado, status=404)
            
        return Response(resultado)

@method_decorator(csrf_exempt, name='dispatch')
class ImportGNS3View(LoginRequiredMixin, View):
    
    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return JsonResponse({"Erro": "Nenhum ficheiro recebido."}, status=400)
        
        try:
            content = file_obj.read().decode('utf-8')
            resultado = process_gns3_file(content)
            
            if "Erro" in resultado:
                return JsonResponse(resultado, status=400)
                
            return JsonResponse(resultado)
            
        except Exception as e:
            return JsonResponse({"Erro": f"Erro interno no servidor: {str(e)}"}, status=500)

class SiteVlansView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        site_id = request.query_params.get('site_id')
        if not site_id:
            return Response({"Erro": "Falta o site_id no URL"}, status=400)
            
        # 1. Apanha VLANs ligadas diretamente ao Site no Netbox
        vlans_diretas = VLAN.objects.filter(site_id=site_id)
        vlan_ids = set([v.id for v in vlans_diretas])
        
        # 2. Apanha VLANs configuradas nas portas de TODOS os equipamentos do Site
        interfaces = Interface.objects.filter(device__site_id=site_id).prefetch_related('tagged_vlans', 'untagged_vlan')
        
        for iface in interfaces:
            if iface.untagged_vlan:
                vlan_ids.add(iface.untagged_vlan.id)
            for vlan in iface.tagged_vlans.all():
                vlan_ids.add(vlan.id)
                
        # Filtra e ordena as que encontrou
        vlans_finais = VLAN.objects.filter(id__in=vlan_ids).order_by('vid')
        
        # Constrói e devolve os dados
        dados = [{"id": v.id, "vid": v.vid, "name": v.name} for v in vlans_finais]
        return Response(dados)