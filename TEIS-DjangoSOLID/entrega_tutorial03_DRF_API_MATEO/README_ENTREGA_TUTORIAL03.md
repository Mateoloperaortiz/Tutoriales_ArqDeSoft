# Evidencia Tutorial 03: DRF y API

## Archivos listos para subir

1. `pagos_locales_MATEO.log`
- Copia del log de pagos generados por la pasarela seleccionada por `PaymentFactory`.
- Incluye transacciones creadas desde `POST /api/v1/comprar/`.

2. `captura_post_drf_tutorial03.png`
- Captura de la interfaz web de DRF mostrando `HTTP 201 Created` para `POST /api/v1/comprar/`.

3. `inventario_antes_api.png`
- Captura HTML de `/inventario/` antes de la compra (Libro ID 9 con stock 2).

4. `inventario_despues_api.png`
- Captura HTML de `/inventario/` después de la compra por API (Libro ID 9 con stock 1).
- Demuestra reutilización de la misma lógica de negocio: la API y la vista HTML reflejan el mismo inventario.

5. `evidencia_tutorial03_api_html_log.txt`
- Registro textual reproducible con status del endpoint, stock antes/después y conteo de líneas en log antes/después.

## Endpoint validado

- `POST /api/v1/comprar/`
- Ejemplo de payload:

```json
{
  "libro_id": 9,
  "direccion_envio": "Calle Evidencia HTML"
}
```
