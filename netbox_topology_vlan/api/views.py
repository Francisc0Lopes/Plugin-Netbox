from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ipam.models import VLAN
from ..utils import get_vlan  

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