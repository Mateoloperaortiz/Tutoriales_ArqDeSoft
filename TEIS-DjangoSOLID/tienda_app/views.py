import datetime

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .domain.logic import CalculadorImpuestos
from .infra.factories import PaymentFactory
from .infra.gateways import BancoNacionalProcesador
from .models import Inventario, Libro, Orden, OrdenItem
from .services import CompraRapidaService, CompraService


def _build_purchase_context(libro, **extra_context):
    context = {
        "libro": libro,
        "total": CalculadorImpuestos.obtener_total_con_iva(libro.precio),
    }
    context.update(extra_context)
    return context


def _crear_orden_legacy(libro, total):
    # Compatibilidad temporal: las rutas legacy siguen rellenando Orden.libro.
    orden = Orden.objects.create(libro=libro, total=total)
    OrdenItem.objects.create(
        orden=orden,
        libro=libro,
        cantidad=1,
        precio_unitario=libro.precio,
    )
    return orden


def inventario_view(request):
    libros = Libro.objects.select_related("inventario").order_by("id")
    items = []
    for libro in libros:
        stock_actual = libro.inventario.cantidad if hasattr(libro, "inventario") else 0
        items.append(
            {
                "libro": libro,
                "stock_actual": stock_actual,
            }
        )

    return render(request, "tienda_app/inventario.html", {"items": items})


def compra_rapida_fbv(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)

    if request.method == "POST":
        # VIOLACION SRP: Logica de inventario en la vista
        inventario = Inventario.objects.get(libro=libro)
        if inventario.cantidad > 0:
            total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)

            # VIOLACION DIP: Proceso de pago acoplado al file system
            with open("pagos_manuales.log", "a") as f:
                f.write(f"[{datetime.datetime.now()}] Pago FBV: ${total}\n")

            with transaction.atomic():
                inventario.cantidad -= 1
                inventario.save(update_fields=["cantidad"])
                _crear_orden_legacy(libro, total)

            return HttpResponse(f"Compra exitosa: {libro.titulo}")
        return HttpResponse("Sin stock", status=400)

    return render(request, "tienda_app/compra_rapida.html", _build_purchase_context(libro))


class CompraRapidaView(View):
    template_name = 'tienda_app/compra_rapida.html'

    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        return render(request, self.template_name, _build_purchase_context(libro))

    def post(self, request, libro_id):
        # La logica de negocio aun reside aqui, pero separada del GET
        libro = get_object_or_404(Libro, id=libro_id)
        inv = Inventario.objects.get(libro=libro)
        if inv.cantidad > 0:
            total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
            with transaction.atomic():
                inv.cantidad -= 1
                inv.save(update_fields=["cantidad"])
                _crear_orden_legacy(libro, total)
            return HttpResponse("Comprado via CBV")
        return HttpResponse("Error", status=400)


class CompraRapidaServiceView(View):
    template_name = "tienda_app/compra_rapida.html"

    def setup_service(self):
        gateway = BancoNacionalProcesador()
        return CompraRapidaService(procesador_pago=gateway)

    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        return render(request, self.template_name, _build_purchase_context(libro))

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
    template_name = "tienda_app/compra.html"

    def setup_service(self):
        # ANTES: gateway = BancoNacionalProcesador()
        # AHORA: Delegacion total a la Fabrica
        gateway = PaymentFactory.get_processor()
        return CompraService(procesador_pago=gateway)

    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        return render(request, self.template_name, _build_purchase_context(libro))

    def post(self, request, libro_id):
        servicio = self.setup_service()
        libro = get_object_or_404(Libro, id=libro_id)

        try:
            mensaje = servicio.ejecutar_proceso_compra(
                usuario="Estudiante EAFIT",
                lista_productos=[libro],
                direccion="Universidad EAFIT",
            )
            return render(
                request,
                self.template_name,
                _build_purchase_context(libro, mensaje_exito=mensaje),
            )
        except Exception as exc:
            return render(
                request,
                self.template_name,
                _build_purchase_context(libro, error=str(exc)),
                status=400,
            )
