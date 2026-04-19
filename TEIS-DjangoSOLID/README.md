# Django + Flask con Primer Estrangulamiento

Este proyecto ejecuta la tienda sobre Docker con PostgreSQL 18, Django/Gunicorn, un microservicio Flask para compras `v2` y Nginx como proxy inverso. El runtime oficial pasa a ser el stack de `docker compose`.

## Arquitectura

```
Internet -> Nginx (:80) -> Django/Gunicorn (:8000)
                         -> Flask Pagos (:5000)
Django/Gunicorn (:8000) -> PostgreSQL (:5432)
```

Nginx sigue siendo el punto de entrada principal. Django y Flask conviven detras del proxy para demostrar el primer estrangulamiento por version de API. Para el laboratorio, Flask tambien expone `:5000` de forma directa para pruebas puntuales del nuevo servicio.

## Versiones fijadas

- Python `3.14-slim`
- PostgreSQL `18.3`
- Django `6.0.3`
- Django REST Framework `3.16.1`
- Psycopg `3.3.3`
- Gunicorn `25.1.0`
- Nginx `1.25-alpine`
- Flask `3.x` sobre `python:3.11-alpine`

## Requisitos

- Docker Desktop o Docker Engine con Docker Compose
- Un archivo `.env` basado en `.env.example`

## Configuracion

1. Cree el archivo de entorno:

   ```bash
   cp .env.example .env
   ```

2. Revise al menos estas variables:

   - `SECRET_KEY`
   - `DEBUG`
   - `ALLOWED_HOSTS`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_HOST`
   - `DB_PORT`
   - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
   - `PAYMENT_PROVIDER`

Para desarrollo local con Docker, el `.env.example` ya trae valores funcionales. Mantenga alineadas las variables `DB_*` y `POSTGRES_*`, porque Django consume las primeras y el contenedor de PostgreSQL las segundas.

`PAYMENT_PROVIDER` acepta estos valores:

- `BANCO`: usa el gateway local que registra pagos en `pagos_locales_MATEO.log`.
- `MOCK`: simula el cobro sin escribir pagos reales.

## Levantar el proyecto con Docker

Construya y levante los servicios:

```bash
docker compose up --build
```

La aplicacion quedara disponible en:

- Inicio: `http://localhost/`
- Inventario: `http://localhost/inventario/`
- API Django v1 productos: `http://localhost/api/v1/productos/`
- API Django v1 compra: `http://localhost/api/v1/comprar/`
- API Flask v2 compra por Nginx: `http://localhost/api/v2/comprar`
- API Flask directa: `http://localhost:5000/api/v2/comprar`

El contenedor `web` espera a PostgreSQL, aplica migraciones y luego arranca Gunicorn. Nginx atiende el puerto 80, envia `/api/v1/` al monolito Django, `/api/v2/comprar` al microservicio Flask y deja el resto del trafico web hacia Django.

## Ejecutar tests en el contenedor

```bash
docker compose run --rm web python manage.py test
```

## Sembrar datos de prueba

Ejecute el script existente dentro del contenedor:

```bash
docker compose exec web sh -c "python manage.py shell < seed_data.py"
```

El comando imprime el `libro_id` creado o actualizado. Use ese valor para probar la API.

## Probar la API

Listar productos servidos por Django:

```bash
curl http://localhost/api/v1/productos/
```

Compra Django v1:

```bash
curl -X POST http://localhost/api/v1/comprar/ \
  -H "Content-Type: application/json" \
  -d '{"libro_id": <LIBRO_ID>, "direccion_envio": "Calle 123"}'
```

Respuesta esperada:

```json
{
  "estado": "exito",
  "mensaje": "Orden X procesada exitosamente."
}
```

Si el libro no existe, la API responde `404`. Si no hay stock, responde `409`.

Compra Flask v2 por Nginx:

```bash
curl -X POST http://localhost/api/v2/comprar \
  -H "Content-Type: application/json" \
  -d '{"producto_id": <LIBRO_ID>, "cantidad": 1}'
```

Compra Flask v2 directa:

```bash
curl -X POST http://localhost:5000/api/v2/comprar \
  -H "Content-Type: application/json" \
  -d '{"producto_id": <LIBRO_ID>, "cantidad": 1}'
```

Respuesta esperada para v2:

```json
{
  "mensaje": "Compra procesada exitosamente por el Microservicio Flask",
  "producto_id": 1,
  "cantidad": 1,
  "status": "Aprobado"
}
```

## Despliegue manual en EC2

1. Cree una instancia Amazon Linux 2023 `t2.micro`.
2. Abra los puertos `22` (SSH) y `80` (HTTP) en el Security Group. El puerto `8000` ya no debe estar expuesto: Django solo responde por la red interna de Docker.
3. Conectese por SSH e instale Docker:

   ```bash
   sudo dnf update -y
   sudo dnf install -y git docker
   sudo systemctl enable --now docker
   sudo usermod -aG docker ec2-user
   exit
   ```

4. Vuelva a entrar por SSH para tomar el nuevo grupo.
5. Clone el repositorio:

   ```bash
   git clone <SU_REPOSITORIO>
   cd TEIS-DjangoSOLID
   ```

6. Cree `.env` a partir de `.env.example` y ajuste:

   - `SECRET_KEY` por un valor real
   - `DEBUG=False`
   - `ALLOWED_HOSTS=<IP_PUBLICA_EC2>,localhost,127.0.0.1`

7. Levante los contenedores:

   ```bash
   docker compose up -d --build
   ```

8. Cargue los datos de prueba:

   ```bash
   docker compose exec web sh -c "python manage.py shell < seed_data.py"
   ```

9. Pruebe la coexistencia desde su equipo:

   ```bash
   curl http://<IP_PUBLICA_EC2>/api/v1/productos/

   curl -X POST http://<IP_PUBLICA_EC2>/api/v1/comprar/ \
     -H "Content-Type: application/json" \
     -d '{"libro_id": <LIBRO_ID>, "direccion_envio": "AWS Academy"}'

   curl -X POST http://<IP_PUBLICA_EC2>/api/v2/comprar \
     -H "Content-Type: application/json" \
     -d '{"producto_id": <LIBRO_ID>, "cantidad": 1}'
   ```

10. Verifique que los tres contenedores esten corriendo:

    ```bash
    docker ps
    ```

    Debe ver `nginx`, `web`, `pagos_flask` y `db` en estado `Up`. Intentar acceder a `http://<IP_PUBLICA_EC2>:8000/` debe fallar con timeout; esa es la evidencia de que Django sigue aislado tras Nginx.

11. Revise los logs del estrangulamiento:

    ```bash
    docker compose logs nginx
    ```

    Debe verse el `upstream` de Django para `/api/v1/...` y el de Flask para `/api/v2/comprar`.

## Comandos utiles

- Ver logs:

  ```bash
  docker compose logs -f
  ```

- Bajar servicios:

  ```bash
  docker compose down
  ```

- Bajar servicios y borrar volumen de PostgreSQL:

  ```bash
  docker compose down -v
  ```
