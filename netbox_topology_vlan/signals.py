from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from dcim.models import Interface, Device
from ipam.models import VLAN

def invalidate_vlan_topology_cache():
    """Apaga a chave de cache específica da topologia."""
    # Use delete() para uma chave ou clear() para TUDO (cuidado com clear)
    print("✅ A limpar cache da topologia...")
    cache.delete('vlan_topology_data') 

# Lista de modelos que afetam o desenho da topologia
# Se editares um Device (nome), uma Interface (ligação) ou VLAN, o mapa limpa.
@receiver(post_save, sender=Interface)
@receiver(post_save, sender=VLAN)
@receiver(post_save, sender=Device)
def on_save_changes(sender, instance, **kwargs):
    # O 'created' indica se é um novo objeto ou uma edição
    status = "criado" if kwargs.get('created') else "editado"
    print(f"✅ SIGNAL: {sender.__name__} {status} (ID: {instance.id}).")
    invalidate_vlan_topology_cache()

@receiver(post_delete, sender=Interface)
@receiver(post_delete, sender=VLAN)
@receiver(post_delete, sender=Device)
def on_delete_changes(sender, instance, **kwargs):
    print(f"❌ SIGNAL: {sender.__name__} eliminado (ID: {instance.id}).")
    invalidate_vlan_topology_cache()