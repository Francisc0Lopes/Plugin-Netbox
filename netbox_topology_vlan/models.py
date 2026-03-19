from django.db import models
from dcim.models import Device

class DeviceCoordinates(models.Model):
    """
    Guarda a posição X e Y de um equipamento no mapa para uma determinada VLAN.
    """
    device = models.ForeignKey(to=Device, on_delete=models.CASCADE, related_name='+')
    vlan_id = models.IntegerField()
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)

    class Meta:
        unique_together = ('device', 'vlan_id')

    def __str__(self):
        return f"{self.device.name} (VLAN {self.vlan_id}): {self.x}, {self.y}"