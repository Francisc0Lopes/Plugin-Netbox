from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ipam.models import VLAN
from ..utils import get_vlan
from ..gns3_importer import process_gns3_file


class VlanTopologyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        vlan_id = request.query_params.get('vlan_id')
        
        if not vlan_id:
            return Response({"Erro": "Falta o vlan_id no URL"}, status=400)
        
        try:
            vlan = VLAN.objects.get(pk=vlan_id)
        except VLAN.DoesNotExist:
            return Response({"error": "VLAN não encontrada"}, status=404)
            
        resultado = get_vlan(vlan_id) #utils.py
        
        if "Erro" in resultado:#Caso VLAN nao exista
            return Response(resultado, status=404)
            
        return Response(resultado)#devolve mapa

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