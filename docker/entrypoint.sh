#!/bin/sh
# Entrypoint del contenedor "web".
#
# 1. Espera a que PostgreSQL acepte conexiones.
# 2. Aplica migraciones pendientes y crea los roles de usuario que falten
#    (desactivable con RUN_MIGRATIONS=0).
# 3. Recolecta estáticos en el volumen compartido con nginx
#    (desactivable con RUN_COLLECTSTATIC=0).
# 4. Ejecuta el comando recibido (por defecto gunicorn, ver Dockerfile).
set -e

python - <<'EOF'
import os, sys, time
import psycopg2

params = dict(
    dbname=os.environ.get('DB_NAME', 'grafiexpress'),
    user=os.environ.get('DB_USER', 'grafiexpress'),
    password=os.environ.get('DB_PASSWORD', ''),
    host=os.environ.get('DB_HOST', 'db'),
    port=os.environ.get('DB_PORT', '5432'),
)
timeout = int(os.environ.get('DB_WAIT_TIMEOUT', '60'))
deadline = time.time() + timeout
while True:
    try:
        psycopg2.connect(connect_timeout=3, **params).close()
        print('[entrypoint] Base de datos disponible en {host}:{port}'.format(**params))
        break
    except psycopg2.OperationalError as exc:
        if time.time() > deadline:
            print('[entrypoint] No se pudo conectar a la base de datos: %s' % exc, file=sys.stderr)
            sys.exit(1)
        print('[entrypoint] Esperando a la base de datos...')
        time.sleep(2)
EOF

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[entrypoint] Aplicando migraciones"
    python manage.py migrate --noinput
    # Crea los roles de usuario que falten (no modifica los existentes)
    python manage.py crear_roles
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
    echo "[entrypoint] Recolectando archivos estáticos"
    python manage.py collectstatic --noinput -v 0
fi

exec "$@"
