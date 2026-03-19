from django.urls import path
from . import views

urlpatterns = [
    path('mapa/', views.MapaVlanView.as_view(), name='mapa'),
]