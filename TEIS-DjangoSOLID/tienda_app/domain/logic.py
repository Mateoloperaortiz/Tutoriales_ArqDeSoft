from decimal import Decimal


class CalculadorImpuestos:
    """
    S: Responsabilidad única - Solo calcula impuestos.
    O: Abierto a extensión - Podríamos heredar para diferentes países.
    """

    IVA = Decimal("1.19")

    @staticmethod
    def obtener_total_con_iva(precio_base):
        base = Decimal(str(precio_base))
        return (base * CalculadorImpuestos.IVA).quantize(Decimal("0.01"))
