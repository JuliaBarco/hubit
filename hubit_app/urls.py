from django.urls import path
from . import views
from django.shortcuts import render

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('actividades/', views.actividades_view, name='actividades'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('reservas/', views.reservas_view, name='reservas'),
    path('cuenta/', views.cuenta_view, name='cuenta'),
    path('datos/', views.datos_view, name='datos'),
    path('compras/', views.compras_view, name='compras'),
    path('saldo/', views.saldo_view, name='saldo'),
    path('lista-actividades/', views.lista_actividades_view, name='lista_actividades'),
     path('actividad-libre/', lambda request: render(request, 'actividad-libre.html'), name='actividad_libre'),
    path('actividad-bono/', lambda request: render(request, 'actividad-bono.html'), name='actividad_bono'),
    path('actividad/', views.actividad_view, name='actividad'),
    path("api/reservar-espacio/", views.reservar_espacio),
]