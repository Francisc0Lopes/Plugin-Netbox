from django.urls import path
from . import views

urlpatterns = [
    path('mapa/', views.MapaVlanView.as_view(), name='mapa'),
    path('api/calculate-stp/', views.calculate_stp_view, name='calculate_stp'),
]