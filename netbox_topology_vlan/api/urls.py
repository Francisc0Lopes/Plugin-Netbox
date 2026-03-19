from django.urls import path
from . import views

urlpatterns = [
    path('get-topology/', views.VlanTopologyView.as_view(), name='get_topology'),
]