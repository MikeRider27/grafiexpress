FROM python:3.5.10-slim-buster

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Reemplaza todo el sources.list con el repositorio archive válido (sin security)
RUN echo "deb http://archive.debian.org/debian buster main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://archive.debian.org/debian buster-updates main contrib non-free" >> /etc/apt/sources.list

# Actualiza e instala dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libjpeg62-turbo-dev \
        zlib1g-dev \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copia e instala dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir gunicorn && \
    pip install --no-cache-dir -r requirements.txt

# Copia el código fuente
COPY . .

# Recopila estáticos (no detiene el build si falla)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "grafiexpress.wsgi:application", "--bind", "0.0.0.0:8000"]