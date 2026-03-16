from decimal import Decimal

from tienda_app.models import Inventario, Libro


libro, created = Libro.objects.update_or_create(
    titulo="Clean Code en Python",
    defaults={"precio": Decimal("150.00")},
)

inventario, _ = Inventario.objects.update_or_create(
    libro=libro,
    defaults={"cantidad": 10},
)

accion = "creado" if created else "actualizado"
print(
    f"Seed completado: libro {accion} con id={libro.id}, "
    f"precio={libro.precio}, stock={inventario.cantidad}"
)
