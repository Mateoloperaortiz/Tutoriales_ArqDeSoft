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
    # Campo legacy: se conserva como espejo de compatibilidad para flujos single-item.
    # El detalle canonico de productos comprados vive en Orden.items.
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


class OrdenItem(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name="items")
    libro = models.ForeignKey(Libro, on_delete=models.PROTECT, related_name="orden_items")
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["orden", "libro"], name="unique_libro_por_orden"),
        ]
