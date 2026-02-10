from django.db import models


class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.titulo

class Inventario(models.Model):
    libro = models.OneToOneField(Libro, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()


class Orden(models.Model):
    # Campo opcional para mantener compatibilidad con Tutorial 01 (FBV Spaghetti).
    libro = models.ForeignKey(
        Libro,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ordenes",
    )
    usuario = models.CharField(max_length=100, default="Invitado")
    direccion_envio = models.CharField(max_length=255, default="Dirección Local")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
