from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from dcim.models import Interface
from ipam.models import VLAN
from dcim.models import Device

"""Serve para reagir a ações que acontecem noutras partes do NetBox ou do plugin."""

@receiver(post_save, sender=Interface)
@receiver(post_save, sender=VLAN)
def invalidate_topology_cache(sender, instance, **kwargs):
    """Limpa cache quando interface/VLAN muda"""
    cache.delete_many([k for k in cache.keys('vlan_topology_*')])

@receiver(post_delete, sender=Interface)
def invalidate_topology_on_delete(sender, instance, **kwargs):
    """Limpa cache quando interface é removida"""
    cache.delete_many([k for k in cache.keys('vlan_topology_*')])

@receiver(post_delete, sender=Device)
def invalidate_topology_on_device_delete(sender, instance, **kwargs):
    """Limpa cache quando dispositivo é removido"""
    cache.delete_many([k for k in cache.keys('vlan_topology_*')])