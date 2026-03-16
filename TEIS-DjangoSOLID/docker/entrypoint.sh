#!/bin/sh
set -eu

python - <<'PY'
import os
import time

import psycopg

dbname = os.environ["DB_NAME"]
user = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]
host = os.environ["DB_HOST"]
port = os.environ.get("DB_PORT", "5432")

for attempt in range(30):
    try:
        with psycopg.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            connect_timeout=3,
        ):
            print("Database is ready.")
            break
    except psycopg.OperationalError:
        if attempt == 29:
            raise
        print("Waiting for database...")
        time.sleep(2)
PY

exec "$@"
