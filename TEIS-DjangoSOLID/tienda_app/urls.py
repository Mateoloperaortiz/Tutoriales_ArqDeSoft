from django.urls import path
from .views import compra_rapida_fbv, CompraRapidaView, CompraRapidaServiceView, CompraView

urlpatterns = [
    path("compra-rapida-fbv/<int:libro_id>/", compra_rapida_fbv, name="compra_rapida_fbv"),
    path("compra-rapida-cbv/<int:libro_id>/", CompraRapidaView.as_view(), name="compra_rapida_cbv"),
    path("compra-rapida-service/<int:libro_id>/", CompraRapidaServiceView.as_view(), name="compra_rapida_service"),
    path('compra/<int:libro_id>/', CompraView.as_view(), name='finalizar_compra'),
]
