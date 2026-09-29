#!/bin/sh
# Ejecuta un comando todos los días a la hora indicada (zona horaria de TZ).
#   diario.sh HH:MM comando [args...]
# Sin crond: un bucle que duerme hasta la próxima ejecución, así el contenedor
# no necesita cron ni privilegios y los logs salen por "docker compose logs".
set -u
HORA="$1"; shift

segundos_hasta() {
    ahora=$(date +%s)
    objetivo=$(date -d "$(date +%Y-%m-%d) $1" +%s 2>/dev/null || date -D '%Y-%m-%d %H:%M' -d "$(date +%Y-%m-%d) $1" +%s)
    [ "$objetivo" -le "$ahora" ] && objetivo=$((objetivo + 86400))
    echo $((objetivo - ahora))
}

echo "[diario] '$*' programado todos los días a las $HORA ($(date +%Z))"
while true; do
    espera=$(segundos_hasta "$HORA")
    echo "[diario] próxima ejecución en $((espera / 3600))h $((espera % 3600 / 60))m"
    sleep "$espera"
    echo "[diario] $(date '+%Y-%m-%d %H:%M:%S') ejecutando: $*"
    "$@" || echo "[diario] ERROR: el comando terminó con código $?"
done
