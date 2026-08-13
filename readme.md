# GrafiExpress

Sistema de gestión para industria gráfica (ventas, producción, compras, materiales,
clientes, cobros, pagos, etc.) hecho en Django 1.8 / Python 3.5.

## Levantar el proyecto con Docker (desarrollo)

Requisitos: Docker y Docker Compose.

1. Copiar el archivo de variables de entorno de ejemplo:
   ```
   cp .env.example .env
   ```
   Ajustar en `.env` los valores de `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
   según a qué base de datos PostgreSQL te vas a conectar. Los valores por
   defecto apuntan a la base usada actualmente en desarrollo.

   ⚠️ Si `SECRET_KEY` tiene el caracter `$`, escribilo como `$$` en `.env`
   (docker-compose interpola `$` como variables; `$$` es el literal).

2. Construir la imagen y levantar el servicio:
   ```
   docker compose up -d --build web
   ```
   El build corre `collectstatic` dentro de la imagen, pero el volumen
   `./static_volume:/app/staticfiles` tapa esos archivos con lo que haya en
   el host. Por eso, después de cada `--build` (o si cambiaste algún CSS/JS),
   hay que correr `collectstatic` una vez más ya con el volumen montado:
   ```
   docker compose exec web python manage.py collectstatic --noinput
   ```
   Si no se ve ningún estilo en `/admin/`, este es el primer paso a probar.

3. La app queda disponible en `http://localhost:8002/` (puerto definido en
   `docker-compose.yml`, mapeado al 8000 interno del contenedor).

4. Migraciones (se corren manualmente, no están en el build):
   ```
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

5. Ver logs:
   ```
   docker compose logs -f web
   ```

6. Comandos que escriben archivos dentro del repo (`makemigrations`, por
   ejemplo) necesitan correr como root, porque el contenedor corre con un
   usuario sin privilegios y el código está montado desde el host:
   ```
   docker compose exec -u root web python manage.py makemigrations
   ```

### Servicio de reportes (JasperReports)

El servicio `jasper-report` está **deshabilitado** en `docker-compose.yml`
(comentado). El script que necesita (`common/jasper/server.py`) es Jython, no
Python normal, y requiere una imagen con JDK que todavía no está armada. Ver
los comentarios en `docker-compose.yml` para el detalle de qué falta.

## Correr sin Docker (bare-metal)

Requiere Python 3.5 y las dependencias de `requirements.txt`.

```
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Si no se define ninguna variable de entorno, `settings.py` usa los mismos
valores de `SECRET_KEY`/`DEBUG`/base de datos que ya tenía hardcodeados
(ver `.env.example` para la lista completa de variables soportadas).

## Vulnerabilidades de dependencias (Dependabot)

El stack está anclado a Python 3.5, así que las versiones de las
dependencias están limitadas a las últimas que todavía publican wheels (o
compilan) para esa versión. Se actualizó lo que se pudo sin tocar código:

| Paquete | Antes | Ahora | Nota |
|---|---|---|---|
| Django | 1.8.14 | 1.8.19 | último parche de seguridad *dentro* de la rama 1.8 |
| Pillow | 3.3.1 | 7.2.0 | última con wheel para Python 3.5 |
| psycopg2-binary | 2.7.7 | 2.8.6 | última con wheel para Python 3.5 |
| reportlab | 3.3.0 | 3.5.52 | 3.5.55+ requiere Python 3.6+ |
| num2words | 0.5.3 | 0.5.13 | 0.5.14 rompe en Python 3.5 (f-strings en `lang_BN.py`) |
| xlwt | 1.1.2 | 1.3.0 | sin más versiones nuevas (paquete sin mantenimiento) |

Esto **no** cierra el grueso de las alertas críticas/altas de Dependabot:
esas son mayormente por Django 1.8 estar fuera de soporte desde 2018. Para
resolverlas de verdad hay que migrar a una versión soportada (Django 2.2 LTS
como mínimo), lo que implica cambios de código en todas las apps
(`MIDDLEWARE_CLASSES` → `MIDDLEWARE`, `url()`, templates, etc.) y no es algo
para hacer de paso — requiere su propio plan de trabajo y testing.

## Actualizar sistema en producción

1. `git checkout produccion`
2. `git pull master`
3. `python manage.py makemigrations`
4. `python manage.py migrate`
5. `git add .`
6. `git commit -m '<mensaje>'`
7. `git push origin produccion`

## Acceso a servidores

**Servidor de producción**
- IP: 190.128.217.106
- Puerto: 8012

**Servidor Amazon**
- IP: 54.219.130.191
- Puerto: 8000
