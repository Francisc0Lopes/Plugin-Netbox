from django.urls import path
from . import views

urlpatterns = [
    path('get-topology/', views.VlanTopologyView.as_view(), name='get_topology'),
    path('import-gns3/', views.ImportGNS3View.as_view(), name='import_gns3'),
]