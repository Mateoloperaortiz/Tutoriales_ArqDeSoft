from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tienda_app.infra.factories import PaymentFactory
from tienda_app.models import Libro
from tienda_app.services import CompraService

from .serializers import OrdenInputSerializer


class CompraAPIView(APIView):
    """
    Endpoint para procesar compras via JSON.
    POST /api/v1/comprar/
    Payload: { "libro_id": 1, "direccion_envio": "Calle 123" }
    """

    def post(self, request):
        serializer = OrdenInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data

        try:
            libro = Libro.objects.get(id=datos["libro_id"])
        except Libro.DoesNotExist:
            return Response({"error": "Libro no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            gateway = PaymentFactory.get_processor()
            servicio = CompraService(procesador_pago=gateway)
            usuario = (
                request.user.get_username()
                if getattr(request.user, "is_authenticated", False)
                else "Invitado API"
            )

            resultado = servicio.ejecutar_proceso_compra(
                usuario=usuario,
                lista_productos=[libro],
                direccion=datos["direccion_envio"],
            )

            return Response(
                {
                    "estado": "exito",
                    "mensaje": resultado,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        except Exception:
            return Response({"error": "Error interno"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
