from netbox.plugins.jobs import register_jobs
from rq_job import Job
from ipam.models import VLAN
from django.core.cache import cache
from ..utils import get_vlan

# AINDA NÃO TESTADO, A IDEIA É USAR ESTE JOB PARA REGERAR AS TOPOLOGIAS DE TODAS AS VLANs EM SEGUNDO PLANO
"""Para usar em topologias gigantes usa tarefas em segundo plano"""
class RegenerateTopology(Job):
    """Recalcula topologias com algoritmo STP"""
    class Meta:
        name = "Regenerar Topologias"
        description = "Recalcula topologias de todas as VLANs com lógica STP"
    
    def do_work(self):
        for vlan in VLAN.objects.all():
            topology = get_vlan(vlan.id)
            # Cache com TTL para evitar recalcular constantemente
            cache.set(f'vlan_topology_{vlan.id}', topology, timeout=3600)

register_jobs(RegenerateTopology)