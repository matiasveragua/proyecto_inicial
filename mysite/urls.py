"""
URL configuration for mysite project.

Rutas del proyecto. El flujo para reportar es:

    /              inicio, el mapa con los dos botones
    /ubicacion/    paso 1: donde esta el desperfecto
    /cercanos/     paso 2: lo que ya hay reportado ahi, para confirmar
    /reportar/     paso 3: que es y una foto
    /mis-reportes/ lo que el usuario reporto y lo que confirmo
    /reporte/5/    el seguimiento de un reporte: estado e historial

Las de cuenta (/accounts/login/ y /accounts/logout/) las trae Django hechas.
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from reportes import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.inicio, name='inicio'),
    path('ubicacion/', views.ubicacion, name='ubicacion'),
    path('cercanos/', views.cercanos, name='cercanos'),
    path('reportar/', views.reportar, name='reportar'),
    path('mis-reportes/', views.mis_reportes, name='mis_reportes'),
    # <int:...> deja pasar solo numeros, asi /reporte/abc/ es un 404 y la
    # vista recibe un entero y no un texto.
    path('reporte/<int:reporte_id>/', views.detalle, name='detalle'),
    path('mas-detalle/', views.mas_detalle, name='mas_detalle'),
    path('panel-municipal/', views.panel_municipal, name='panel_municipal'),

    path('accounts/registro/', views.registro, name='registro'),
    # Trae gratis /accounts/login/ y /accounts/logout/ de Django.
    # LoginView usa reportes/login.html, que es la pantalla que hizo Bastian.
    path('accounts/login/', views.EntrarView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('terminos/', views.terminos, name='terminos'),
    path('actualizar-estado/', views.actualizar_estado, name='actualizar_estado'),
]

# En desarrollo, servir las fotos subidas desde /media/
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
