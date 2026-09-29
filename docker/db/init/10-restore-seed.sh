#!/bin/sh
# Se ejecuta UNA sola vez, cuando el volumen de datos de PostgreSQL está vacío
# (la imagen oficial corre todo lo que haya en /docker-entrypoint-initdb.d/).
#
# Si DB_SEED_FILE apunta a un dump existente dentro de /seed (carpeta
# docker/db/seed del repo), lo restaura en la base recién creada. Si no, la
# base queda vacía y Django crea las tablas con "migrate" al arrancar "web".
set -e

if [ -z "$DB_SEED_FILE" ]; then
    echo "[seed] DB_SEED_FILE no definido: se inicia con base vacía"
    exit 0
fi

SEED="/seed/$DB_SEED_FILE"
if [ ! -f "$SEED" ]; then
    echo "[seed] No existe $SEED: se inicia con base vacía"
    exit 0
fi

echo "[seed] Restaurando $SEED en la base $POSTGRES_DB"
case "$SEED" in
    *.sql)    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$SEED" ;;
    *.sql.gz) gunzip -c "$SEED" | psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" ;;
    # Formato custom de pg_dump (-Fc). Se excluyen el schema "public" y la
    # extensión plpgsql (ya existen en una base nueva y romperían el restore).
    # --no-owner/--no-acl: todo queda a nombre del usuario de la app.
    *)
        LIST=$(mktemp)
        pg_restore -l "$SEED" | grep -vE 'SCHEMA - public |EXTENSION - plpgsql|COMMENT - (SCHEMA public|EXTENSION plpgsql)' > "$LIST"
        pg_restore --no-owner --no-acl --exit-on-error -L "$LIST" \
            -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$SEED"
        rm -f "$LIST"
        ;;
esac
echo "[seed] Restauración terminada"
