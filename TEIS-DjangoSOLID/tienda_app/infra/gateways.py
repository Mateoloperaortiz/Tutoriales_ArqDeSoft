import datetime
from ..domain.interfaces import ProcesadorPago

class BancoNacionalProcesador(ProcesadorPago):

    def pagar(self, monto: float) -> bool:
        # Reemplazo de SU_NOMBRE por identidad del estudiante.
        archivo_log = "pagos_locales_MATEO.log"

        with open(archivo_log, "a") as f:
            f.write(
                f"[{datetime.datetime.now()}] "
                f"Transaccion exitosa por: ${monto}\n"
            )

        return True
