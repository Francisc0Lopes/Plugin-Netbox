from netbox.plugins.jobs import register_jobs
from rq_job import Job
from ipam.models import VLAN
from django.core.cache import cache
from .stp_algorithm import calculate_stp_for_all_vlans

class CalculateSTPTopology(Job):
    """Calcula automaticamente a topologia STP para todas as VLANs"""
    
    class Meta:
        name = "Calcular STP"
        description = "Calcula a topologia Spanning Tree Protocol para todas as VLANs e atualiza NetBox"
        task_queues = ['default']
        hidden = False
    
    def do_work(self):
        self.logger.info("🔄 Iniciando cálculo STP para todas as VLANs...")
        
        try:
            # Calcular e aplicar ao NetBox
            results = calculate_stp_for_all_vlans(apply_to_netbox=True)
            
            # Cache com TTL de 1 hora
            cache.set('stp_results_all', results, timeout=3600)
            
            self.logger.info(f"✅ Cálculo STP concluído para {len(results)} VLANs!")
            return f"Sucesso: {len(results)} VLANs processadas"
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular STP: {e}")
            raise e

register_jobs(CalculateSTPTopology)