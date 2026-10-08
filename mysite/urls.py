"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from reportes import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('reportar/', views.reportar, name='reportar'),
    path('mis-reportes/', views.mis_reportes, name='mis_reportes'),
    # Trae gratis /accounts/login/ y /accounts/logout/ de Django.
    path('accounts/', include('django.contrib.auth.urls')),
]

# En desarrollo, servir las fotos subidas desde /media/
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
