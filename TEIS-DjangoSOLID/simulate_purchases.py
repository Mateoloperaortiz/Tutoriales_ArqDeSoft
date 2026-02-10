from django.test import Client
from tienda_app.models import Libro, Inventario

# Ensure we have stock
try:
    libro = Libro.objects.get(titulo="Clean Code en Python")
except Libro.DoesNotExist:
    # Fallback if seed data failed or different title
    libro = Libro.objects.first()

if libro:
    Inventario.objects.update_or_create(libro=libro, defaults={'cantidad': 10})
    
    c = Client()
    url = f'/compra/{libro.id}/'
    
    print(f"Purchasing book {libro.id}...")
    
    response = c.post(url)
    print(f"Status {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.content.decode()}")
    else:
        print(f"Error Response: {response.content.decode()}")
else:
    print("No books found.")
