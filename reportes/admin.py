from django.contrib import admin

from .models import (CambioEstado, Categoria, Confirmacion, Perfil, Reporte,
                     Ubicacion)

admin.site.register(Categoria)
admin.site.register(Ubicacion)
admin.site.register(Reporte)
admin.site.register(Confirmacion)
admin.site.register(CambioEstado)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "es_gestor", "comuna")
    list_filter = ("es_gestor", "comuna")
    search_fields = ("usuario__username", "comuna")
