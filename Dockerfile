FROM python:3.5.10-slim-buster

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    WEB_CONCURRENCY=3

WORKDIR /app

# Reemplaza todo el sources.list con el repositorio archive válido (Debian Buster
# ya no recibe actualizaciones de seguridad, así que solo el archive funciona)
RUN echo "deb http://archive.debian.org/debian buster main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://archive.debian.org/debian buster-updates main contrib non-free" >> /etc/apt/sources.list

# Dependencias del sistema necesarias para compilar Pillow y psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libjpeg62-turbo-dev \
        zlib1g-dev \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copia e instala dependencias Python (capa cacheada mientras no cambie requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Usuario sin privilegios para correr la app
RUN groupadd -r app && useradd -r -g app -d /app app

# Copia el código fuente
COPY . .

RUN mkdir -p /app/staticfiles /app/media && \
    chown -R app:app /app

# Recopila estáticos en build time. Si tu SECRET_KEY/DB solo están disponibles
# en runtime (vía variables de entorno), corré collectstatic como parte del
# arranque del contenedor en vez de acá.
RUN python manage.py collectstatic --noinput || true

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3).status < 500 else 1)" || exit 1

CMD ["sh", "-c", "gunicorn grafiexpress.wsgi:application --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY} --timeout 60 --access-logfile - --error-logfile -"]
