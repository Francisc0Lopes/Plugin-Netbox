from django.urls import path
from . import views

urlpatterns = [ #Ao clicar o botao do menu faz isto ACHO EU DO QUE VI
    path('mapa/', views.MapaVlanView.as_view(), name='mapa'),
]