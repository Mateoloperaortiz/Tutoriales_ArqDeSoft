import json
import os
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .domain.logic import CalculadorImpuestos
from .infra.factories import MockPaymentProcessor, PaymentFactory
from .infra.gateways import BancoNacionalProcesador
from .models import Inventario, Libro, Orden
from .services import CompraService


class ProcesadorPagoExitoso:
    def __init__(self):
        self.montos = []

    def pagar(self, monto):
        self.montos.append(monto)
        return True


class ProcesadorPagoFallido:
    def pagar(self, monto):
        return False


class CompraServiceTestCase(TestCase):
    def setUp(self):
        self.libro_a = Libro.objects.create(titulo="Libro A", precio=Decimal("100.00"))
        self.libro_b = Libro.objects.create(titulo="Libro B", precio=Decimal("50.00"))
        Inventario.objects.create(libro=self.libro_a, cantidad=2)
        Inventario.objects.create(libro=self.libro_b, cantidad=1)

    def test_compra_exitosa_crea_orden_y_descuenta_inventario(self):
        procesador = ProcesadorPagoExitoso()
        servicio = CompraService(procesador_pago=procesador)

        mensaje = servicio.ejecutar_proceso_compra(
            usuario="Estudiante",
            lista_productos=[self.libro_a, self.libro_b, self.libro_a],
            direccion="EAFIT",
        )

        self.assertIn("Orden", mensaje)
        self.assertEqual(Orden.objects.count(), 1)

        orden = Orden.objects.get()
        self.assertEqual(orden.total, Decimal("297.50"))
        self.assertEqual(procesador.montos, [Decimal("297.50")])

        inventario_a = Inventario.objects.get(libro=self.libro_a)
        inventario_b = Inventario.objects.get(libro=self.libro_b)
        self.assertEqual(inventario_a.cantidad, 0)
        self.assertEqual(inventario_b.cantidad, 0)

    def test_compra_falla_si_alguno_de_los_productos_no_tiene_stock(self):
        inventario_b = Inventario.objects.get(libro=self.libro_b)
        inventario_b.cantidad = 0
        inventario_b.save(update_fields=["cantidad"])

        servicio = CompraService(procesador_pago=ProcesadorPagoExitoso())

        with self.assertRaisesMessage(ValueError, "No hay existencias"):
            servicio.ejecutar_proceso_compra(
                usuario="Estudiante",
                lista_productos=[self.libro_a, self.libro_b],
                direccion="EAFIT",
            )

        self.assertEqual(Orden.objects.count(), 0)
        self.assertEqual(Inventario.objects.get(libro=self.libro_a).cantidad, 2)
        self.assertEqual(Inventario.objects.get(libro=self.libro_b).cantidad, 0)

    def test_pago_fallido_elimina_orden_y_no_descuenta_inventario(self):
        servicio = CompraService(procesador_pago=ProcesadorPagoFallido())

        with self.assertRaisesMessage(Exception, "Error en la pasarela de pagos."):
            servicio.ejecutar_proceso_compra(
                usuario="Estudiante",
                lista_productos=[self.libro_a],
                direccion="EAFIT",
            )

        self.assertEqual(Orden.objects.count(), 0)
        self.assertEqual(Inventario.objects.get(libro=self.libro_a).cantidad, 2)

    def test_rechaza_compra_sin_productos(self):
        servicio = CompraService(procesador_pago=ProcesadorPagoExitoso())

        with self.assertRaisesMessage(ValueError, "al menos un producto"):
            servicio.ejecutar_proceso_compra(
                usuario="Estudiante",
                lista_productos=[],
                direccion="EAFIT",
            )

    def test_total_se_calcula_con_calculador_de_impuestos(self):
        servicio = CompraService(procesador_pago=ProcesadorPagoExitoso())

        servicio.ejecutar_proceso_compra(
            usuario="Estudiante",
            lista_productos=[self.libro_a],
            direccion="EAFIT",
        )

        orden = Orden.objects.get()
        esperado = CalculadorImpuestos.obtener_total_con_iva(Decimal("100.00"))
        self.assertEqual(orden.total, esperado)


class PaymentFactoryTestCase(TestCase):
    def test_factory_retorna_mock_si_variable_de_entorno_es_mock(self):
        with patch.dict(os.environ, {"PAYMENT_PROVIDER": "MOCK"}, clear=False):
            procesador = PaymentFactory.get_processor()
            self.assertIsInstance(procesador, MockPaymentProcessor)

    def test_factory_retorna_banco_por_defecto(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PAYMENT_PROVIDER", None)
            procesador = PaymentFactory.get_processor()
            self.assertIsInstance(procesador, BancoNacionalProcesador)


class CompraAPITestCase(TestCase):
    def setUp(self):
        self.libro = Libro.objects.create(titulo="API Libro", precio=Decimal("80.00"))
        Inventario.objects.create(libro=self.libro, cantidad=1)
        self.url = reverse("api_comprar")

    @patch("tienda_app.api.views.PaymentFactory.get_processor")
    def test_api_compra_exitosa_descuenta_stock(self, mock_get_processor):
        mock_get_processor.return_value = ProcesadorPagoExitoso()

        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    "libro_id": self.libro.id,
                    "direccion_envio": "Calle 123",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["estado"], "exito")
        self.assertEqual(Orden.objects.count(), 1)
        self.assertEqual(Inventario.objects.get(libro=self.libro).cantidad, 0)
        mock_get_processor.assert_called_once()

    def test_api_valida_payload(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"direccion_envio": "Sin libro"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("libro_id", response.json())

    def test_api_retorna_404_si_libro_no_existe(self):
        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    "libro_id": 99999,
                    "direccion_envio": "Calle 404",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Libro no encontrado.")

    @patch("tienda_app.api.views.PaymentFactory.get_processor")
    def test_api_retorna_409_si_no_hay_stock(self, mock_get_processor):
        mock_get_processor.return_value = ProcesadorPagoExitoso()
        inventario = Inventario.objects.get(libro=self.libro)
        inventario.cantidad = 0
        inventario.save(update_fields=["cantidad"])

        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    "libro_id": self.libro.id,
                    "direccion_envio": "Calle sin stock",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("No hay existencias", response.json()["error"])

    @patch("tienda_app.api.views.PaymentFactory.get_processor")
    def test_api_compra_refleja_cambio_en_vista_html_inventario(self, mock_get_processor):
        mock_get_processor.return_value = ProcesadorPagoExitoso()
        inventario_url = reverse("inventario")

        before_response = self.client.get(inventario_url)
        before_stock = next(
            item["stock_actual"]
            for item in before_response.context["items"]
            if item["libro"].id == self.libro.id
        )

        self.client.post(
            self.url,
            data=json.dumps(
                {
                    "libro_id": self.libro.id,
                    "direccion_envio": "Calle HTML",
                }
            ),
            content_type="application/json",
        )

        after_response = self.client.get(inventario_url)
        after_stock = next(
            item["stock_actual"]
            for item in after_response.context["items"]
            if item["libro"].id == self.libro.id
        )

        self.assertEqual(before_stock, 1)
        self.assertEqual(after_stock, 0)
