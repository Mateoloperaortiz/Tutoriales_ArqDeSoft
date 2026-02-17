from rest_framework import serializers

from tienda_app.models import Libro


class LibroSerializer(serializers.ModelSerializer):
    stock_actual = serializers.SerializerMethodField()

    class Meta:
        model = Libro
        fields = ["id", "titulo", "precio", "stock_actual"]

    def get_stock_actual(self, obj):
        if hasattr(obj, "inventario"):
            return obj.inventario.cantidad
        return 0


class OrdenInputSerializer(serializers.Serializer):
    """
    Serializer para validar la entrada de datos.
    Actua como DTO (Data Transfer Object).
    """

    libro_id = serializers.IntegerField(min_value=1)
    direccion_envio = serializers.CharField(max_length=200)
