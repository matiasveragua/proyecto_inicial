"""
URL configuration for mysite project.

Rutas del proyecto. El flujo para reportar es:

    /              inicio, el mapa con los dos botones
    /ubicacion/    paso 1: donde esta el desperfecto
    /reportar/     paso 2: que es y una foto
    /mis-reportes/ la lista de lo que ha reportado el usuario

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
    path('reportar/', views.reportar, name='reportar'),
    path('mis-reportes/', views.mis_reportes, name='mis_reportes'),
    path('mas-detalle/', views.mas_detalle, name='mas_detalle'),

    path('accounts/registro/', views.registro, name='registro'),
    # Trae gratis /accounts/login/ y /accounts/logout/ de Django.
    # LoginView usa reportes/login.html, que es la pantalla que hizo Bastian.
    path('accounts/login/', views.EntrarView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/registro/', views.registro, name='registro'),
    path('terminos/', views.terminos, name='terminos'),
    path('reporte-registrado/<int:pk>/', views.reporte_registrado, name='reporte_registrado'),
    path('nuevo-reporte/', views.nuevo_reporte, name='nuevo_reporte'),
    path('confirmacion/<int:pk>/', views.confirmacion_enviada, name='confirmacion_enviada'),
]

# En desarrollo, servir las fotos subidas desde /media/
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
