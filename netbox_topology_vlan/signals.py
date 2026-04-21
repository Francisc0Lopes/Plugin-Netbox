from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from dcim.models import Interface, Device
from ipam.models import VLAN

#NÃO FUNCIONA, NÃO SEI PORQUÊ, A IDEIA ERA LIMPAR O CACHE QUANDO HOUVER ALTERAÇÕES NAS INTERFACES,
# VLANs OU DISPOSITIVOS PARA GARANTIR QUE O MAPA SEJA ATUALIZADO 
def invalidate_vlan_topology_cache():
    """Função helper para limpar o cache da topologia VLAN."""
    cache.clear() 

# Quando uma interface ou VLAN muda
@receiver(post_save, sender=Interface)
@receiver(post_save, sender=VLAN)
def on_save_interface_or_vlan(sender, instance, **kwargs):
    invalidate_vlan_topology_cache()

# Quando uma interface é apagada
@receiver(post_delete, sender=Interface)
def on_delete_interface(sender, instance, **kwargs):
    invalidate_vlan_topology_cache()

# Quando um dispositivo é apagado
@receiver(post_delete, sender=Device)
def on_delete_device(sender, instance, **kwargs):
    invalidate_vlan_topology_cache()