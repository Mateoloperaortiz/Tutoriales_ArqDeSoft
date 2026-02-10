from tienda_app.models import Libro, Inventario

# Clear existing to avoid dupes if run multiple times
Libro.objects.filter(titulo="Clean Code en Python").delete()

l = Libro.objects.create(
    titulo="Clean Code en Python",
    precio=150.0
)

Inventario.objects.create(
    libro=l,
    cantidad=10
)

print("Datos creados exitosamente")
