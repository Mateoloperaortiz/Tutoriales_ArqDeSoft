from django.urls import path
from .views import (
    compra_rapida_fbv,
    CompraRapidaView,
    CompraRapidaServiceView,
    CompraView,
    inventario_view,
)
from tienda_app.api.views import CompraAPIView

urlpatterns = [
    path("inventario/", inventario_view, name="inventario"),
    path("compra-rapida-fbv/<int:libro_id>/", compra_rapida_fbv, name="compra_rapida_fbv"),
    path("compra-rapida-cbv/<int:libro_id>/", CompraRapidaView.as_view(), name="compra_rapida_cbv"),
    path("compra-rapida-service/<int:libro_id>/", CompraRapidaServiceView.as_view(), name="compra_rapida_service"),
    path('compra/<int:libro_id>/', CompraView.as_view(), name='finalizar_compra'),
    path("api/v1/comprar/", CompraAPIView.as_view(), name="api_comprar"),
]
