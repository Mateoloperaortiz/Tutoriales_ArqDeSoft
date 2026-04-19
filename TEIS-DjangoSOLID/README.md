# Django Clean Monolith Dockerizado

Este proyecto ejecuta la aplicacion Django de la tienda sobre Docker, PostgreSQL 18 y Gunicorn. El runtime oficial pasa a ser el stack de `docker compose`.

## Versiones fijadas

- Python `3.14-slim`
- PostgreSQL `18.3`
- Django `6.0.3`
- Django REST Framework `3.16.1`
- Psycopg `3.3.3`
- Gunicorn `25.1.0`

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

- Inicio: `http://localhost:8000/`
- Inventario: `http://localhost:8000/inventario/`
- API: `http://localhost:8000/api/v1/comprar/`

El contenedor `web` espera a PostgreSQL, aplica migraciones y luego arranca Gunicorn.

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

Ejemplo de compra exitosa:

```bash
curl -X POST http://localhost:8000/api/v1/comprar/ \
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

## Despliegue manual en EC2

1. Cree una instancia Amazon Linux 2023 `t2.micro`.
2. Abra los puertos `22` y `8000` en el Security Group.
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

9. Pruebe la API desde su equipo:

   ```bash
   curl -X POST http://<IP_PUBLICA_EC2>:8000/api/v1/comprar/ \
     -H "Content-Type: application/json" \
     -d '{"libro_id": <LIBRO_ID>, "direccion_envio": "AWS Academy"}'
   ```

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
