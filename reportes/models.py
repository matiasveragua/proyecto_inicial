from django.db import models

# Create your models here.

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    gravedad_referencial = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre


from django.conf import settings


class Ubicacion(models.Model):
    latitud = models.FloatField()
    longitud = models.FloatField()
    direccion_texto = models.CharField(max_length=200)
    comuna = models.CharField(max_length=60)

    def __str__(self):
        return f"{self.direccion_texto}, {self.comuna}"


class Reporte(models.Model):
    ESTADOS = [
        ("recibido", "Recibido"),
        ("en_revision", "En revisión"),
        ("atendido", "Atendido"),
        ("descartado", "Descartado"),
    ]
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    descripcion = models.TextField()
    foto = models.ImageField(upload_to="reportes/", blank=True)
    estado_actual = models.CharField(max_length=20, choices=ESTADOS, default="recibido")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.id} {self.categoria} - {self.ubicacion.comuna}"


class Confirmacion(models.Model):
    """Alguien dice que el reporte de otro es real: a mi tambien me pasa.

    No se le pone related_name a proposito: el panel municipal ya cuenta las
    confirmaciones con reporte.confirmacion_set, que es el nombre que Django da
    por defecto.
    """

    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_confirmacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Cada persona confirma un reporte una sola vez. Sin esto, apretar dos
        # veces el boton deja dos filas y el panel municipal ve un desperfecto
        # mas grave de lo que es: el contador de confirmaciones es justamente
        # lo que usa para priorizar.
        constraints = [
            models.UniqueConstraint(
                fields=["reporte", "usuario"],
                name="una_confirmacion_por_persona",
            ),
        ]

    def __str__(self):
        return f"{self.usuario} confirma #{self.reporte_id}"


class CambioEstado(models.Model):
    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE)
    gestor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)