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
