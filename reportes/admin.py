from django.contrib import admin
from .models import Categoria, Ubicacion, Reporte, Confirmacion, CambioEstado

admin.site.register(Categoria)
admin.site.register(Ubicacion)
admin.site.register(Reporte)
admin.site.register(Confirmacion)
admin.site.register(CambioEstado)