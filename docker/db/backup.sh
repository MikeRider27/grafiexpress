#!/bin/sh
# Backup de la base interna: pg_dump en formato custom a /backups, verificación
# de que el archivo se puede leer y borrado de los de más de BACKUP_DIAS días.
set -eu
DESTINO=/backups
ARCHIVO="$DESTINO/grafiexpress_$(date +%Y%m%d_%H%M%S).backup"
export PGPASSWORD="$DB_PASSWORD"

pg_dump -Fc -h "${DB_HOST:-db}" -U "$DB_USER" -d "$DB_NAME" -f "$ARCHIVO.tmp"
pg_restore -l "$ARCHIVO.tmp" > /dev/null          # falla si el dump está corrupto
mv "$ARCHIVO.tmp" "$ARCHIVO"
echo "[backup] OK $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))"

find "$DESTINO" -name 'grafiexpress_*.backup' -mtime +"${BACKUP_DIAS:-14}" -print -delete | sed 's/^/[backup] rotado: /'
