# Resumen de Código - Tutorial 01

## services.py (tienda_app/services.py)

```python
from collections import Counter

from django.db import transaction

from .domain.builders import OrdenBuilder
from .domain.logic import CalculadorImpuestos
from .models import Inventario, Libro


class CompraRapidaService:
    def __init__(self, procesador_pago):
        self.procesador_pago = procesador_pago

    def procesar(self, libro_id):
        libro = Libro.objects.get(id=libro_id)
        inv = Inventario.objects.get(libro=libro)

        if inv.cantidad <= 0:
            raise ValueError("No hay existencias.")

        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)

        if self.procesador_pago.pagar(total):
            inv.cantidad -= 1
            inv.save(update_fields=["cantidad"])
            return total
        return None


class CompraService:
    def __init__(self, procesador_pago):
        self.procesador = procesador_pago
        self.builder = OrdenBuilder()

    @staticmethod
    def _contar_productos(lista_productos):
        return Counter(libro.id for libro in lista_productos)

    @staticmethod
    def _obtener_inventarios_bloqueados(conteo_por_libro):
        inventarios = (
            Inventario.objects
            .select_for_update()
            .select_related("libro")
            .filter(libro_id__in=conteo_por_libro.keys())
        )
        inventarios_por_libro = {inventario.libro_id: inventario for inventario in inventarios}

        faltantes = [libro_id for libro_id in conteo_por_libro if libro_id not in inventarios_por_libro]
        if faltantes:
            raise ValueError("No hay inventario configurado para uno o más libros.")

        for libro_id, cantidad_requerida in conteo_por_libro.items():
            inventario = inventarios_por_libro[libro_id]
            if inventario.cantidad < cantidad_requerida:
                raise ValueError(f"No hay existencias para '{inventario.libro.titulo}'.")

        return inventarios_por_libro

    def ejecutar_proceso_compra(self, usuario, lista_productos, direccion):
        if not lista_productos:
            raise ValueError("Debe incluir al menos un producto para comprar.")

        with transaction.atomic():
            conteo_por_libro = self._contar_productos(lista_productos)
            inventarios_por_libro = self._obtener_inventarios_bloqueados(conteo_por_libro)

            # Uso del Builder: Semantica clara y validacion interna
            orden = (
                self.builder
                .con_usuario(usuario)
                .con_productos(lista_productos)
                .para_envio(direccion)
                .build()
            )

            # Uso del Factory (inyectado): Cambio de comportamiento sin cambio de codigo
            if not self.procesador.pagar(orden.total):
                orden.delete()
                raise Exception("Error en la pasarela de pagos.")

            for libro_id, cantidad_requerida in conteo_por_libro.items():
                inventario = inventarios_por_libro[libro_id]
                inventario.cantidad -= cantidad_requerida
                inventario.save(update_fields=["cantidad"])

            return f"Orden {orden.id} procesada exitosamente."
```

## views.py (tienda_app/views.py)

```python
import datetime

from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Libro, Inventario, Orden
from .domain.logic import CalculadorImpuestos
from .services import CompraRapidaService, CompraService
from .infra.factories import PaymentFactory
from .infra.gateways import BancoNacionalProcesador


def compra_rapida_fbv(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)

    if request.method == "POST":
        # VIOLACION SRP: Logica de inventario en la vista
        inventario = Inventario.objects.get(libro=libro)
        if inventario.cantidad > 0:
            # VIOLACION OCP: Calculo de negocio hardcoded
            total = float(libro.precio) * 1.19

            # VIOLACION DIP: Proceso de pago acoplado al file system
            with open("pagos_manuales.log", "a") as f:
                f.write(f"[{datetime.datetime.now()}] Pago FBV: ${total}\n")

            inventario.cantidad -= 1
            inventario.save(update_fields=["cantidad"])
            Orden.objects.create(libro=libro, total=total)

            return HttpResponse(f"Compra exitosa: {libro.titulo}")
        return HttpResponse("Sin stock", status=400)

    total_estimado = float(libro.precio) * 1.19
    return render(
        request,
        "tienda_app/compra_rapida.html",
        {"libro": libro, "total": total_estimado},
    )


class CompraRapidaView(View):
    template_name = 'tienda_app/compra_rapida.html'

    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = float(libro.precio) * 1.19
        return render(request, self.template_name, {"libro": libro, "total": total})

    def post(self, request, libro_id):
        # La logica de negocio aun reside aqui, pero separada del GET
        libro = get_object_or_404(Libro, id=libro_id)
        inv = Inventario.objects.get(libro=libro)
        if inv.cantidad > 0:
            total = float(libro.precio) * 1.19
            inv.cantidad -= 1
            inv.save(update_fields=["cantidad"])
            Orden.objects.create(libro=libro, total=total)
            return HttpResponse("Comprado via CBV")
        return HttpResponse("Error", status=400)


class CompraRapidaServiceView(View):
    template_name = "tienda_app/compra_rapida.html"

    def setup_service(self):
        gateway = BancoNacionalProcesador()
        return CompraRapidaService(procesador_pago=gateway)

    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return render(request, self.template_name, {"libro": libro, "total": total})

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            total = servicio.procesar(libro_id)
            if total is None:
                return HttpResponse("Error en pago", status=400)
            return HttpResponse(f"Compra exitosa via Service: ${total}")
        except ValueError as exc:
            return HttpResponse(str(exc), status=400)


class CompraView(View):
    template_name = "tienda_app/compra_rapida.html"

    def setup_service(self):
        # ANTES: gateway = BancoNacionalProcesador()
        # AHORA: Delegacion total a la Fabrica
        gateway = PaymentFactory.get_processor()
        return CompraService(procesador_pago=gateway)

    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return render(request, self.template_name, {"libro": libro, "total": total})

    def post(self, request, libro_id):
        servicio = self.setup_service()
        libro = get_object_or_404(Libro, id=libro_id)

        try:
            mensaje = servicio.ejecutar_proceso_compra(
                usuario="Estudiante EAFIT",
                lista_productos=[libro],
                direccion="Universidad EAFIT",
            )
            return HttpResponse(mensaje)
        except Exception as exc:
            return HttpResponse(str(exc), status=400)
```
