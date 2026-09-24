from django.db import models

# Create your models here.

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    gravedad_referencial = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre