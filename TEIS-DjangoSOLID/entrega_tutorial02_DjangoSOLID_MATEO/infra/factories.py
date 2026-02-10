import os
from .gateways import BancoNacionalProcesador

# Implementacion ligera para pruebas (Mocking)
class MockPaymentProcessor:
    def pagar(self, monto: float) -> bool:
        print(f"[DEBUG] Mock Payment: Procesando pago de ${monto} sin cargo real.")
        return True

class PaymentFactory:
    @staticmethod
    def get_processor():
        # LECCION ARQUITECTURA: La configuracion viene del ambiente, no del codigo
        provider = os.getenv('PAYMENT_PROVIDER', 'BANCO')

        if provider == 'MOCK':
            return MockPaymentProcessor()

        # Por defecto usamos la infraestructura real
        return BancoNacionalProcesador()
