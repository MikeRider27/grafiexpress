# GrafiExpress

Sistema de gestión para industria gráfica (ventas, producción, compras, materiales,
clientes, cobros, pagos, etc.) hecho en Django 1.8 / Python 3.5.

## Levantar el proyecto con Docker

Requisitos: Docker (con Compose v2) y `make`.

### Arquitectura

```
navegador → nginx (:APP_PORT, 8002 por defecto) → web (gunicorn :8000) → db (PostgreSQL 12)
                                                          └→ jasper (PDFs) → db
```

| Servicio | Qué hace | Persistencia |
|---|---|---|
| `db` | PostgreSQL **interno** del stack. No publica puertos: solo lo ve `web` por la red interna `backend`. | volumen `grafiexpress_pgdata` |
| `web` | Django + gunicorn. Al arrancar espera a la base, corre `migrate` y `collectstatic` solo. | volúmenes `static` y `media` |
| `nginx` | Proxy reverso; sirve `/static/` y `/media/` directamente. | — |
| `jasper` | Genera los PDF de facturas y remisiones (JasperReports, Java 8). Solo red interna. | — |

Los datos sobreviven a `make down` / reinicios; solo se borran con `make reset-db`
o `docker compose down -v`.

### Primera vez

```
make init        # crea .env con SECRET_KEY y DB_PASSWORD aleatorias
make up          # build + levanta db, web y nginx
make superuser   # crea el usuario administrador
```

La app queda en `http://localhost:8002/`. Con `DEBUG=False` (recomendado),
`ALLOWED_HOSTS` en `.env` tiene que incluir el dominio/IP con el que se accede.

### Cargar datos existentes

**Opción A — al crear la base (semilla):** copiar un dump a `docker/db/seed/`
y poner su nombre en `DB_SEED_FILE` del `.env`. Se restaura solo la primera vez
que se crea el volumen (para repetirlo: `make reset-db`). Acepta `.backup`
(`pg_dump -Fc`), `.sql` y `.sql.gz`.

**Opción B — sobre una base ya levantada:**
```
make restore f=ruta/al/dump.backup
```

Para migrar desde el servidor PostgreSQL anterior, generar el dump allá con
`pg_dump -Fc -h <host> -p <puerto> -U <usuario> <base> > grafiexpress.backup`
y usar cualquiera de las dos opciones. Las migraciones que falten se aplican
solas al arrancar `web`.

> Los dumps de 2017 en `backups/` **no** sirven como semilla: su esquema no
> coincide con el historial de migraciones (p. ej. `materiales.0002` falla
> porque la columna ya existe).

### Roles de usuario

Al arrancar se crean (si no existen) estos grupos, con permisos de
agregar/modificar en sus módulos; **borrar queda solo para Administrador**
(Django 1.8 no tiene permiso de "solo ver"):

| Rol | Módulos |
|---|---|
| Administrador | Todo, incluida la gestión de usuarios |
| Gerencia | Todos los módulos, sin borrar ni gestionar usuarios |
| Comercial | Clientes, comercial y carga de sus propias OT |
| Facturación | Facturas y remisiones (imprimir/anular) y clientes |
| Cobranzas | Recibos, cheques, bancos y estado de cuenta |
| Compras y pagos | Proveedores, compras, pagos, cheques emitidos y bancos |
| Producción | OT de todos los vendedores, costos, procesos y máquinas |
| Depósito | Stock, altas, bajas, retiros y devoluciones |

Se asignan en Sistema > Usuarios > (usuario) > Grupos. Un vendedor debe
tener además su ficha en Funcionarios vinculada al usuario: así ve solo sus
OT y actividades (salvo que tenga el permiso "Ver Todas las OTs").
Si se cambia la definición en `sistema/management/commands/crear_roles.py`,
aplicarla con `make roles`.

### Datos de prueba

Para probar sin datos reales, sobre una base vacía (sin clientes):
```
make demo
```
Carga datos ficticios en todos los módulos (clientes, OT, facturas, cobros,
compras, pagos, stock, producción, comercial) usando la misma lógica del
sistema, así que saldos, stock y cantidades entregadas/facturadas quedan
consistentes. También crea dos usuarios vendedores de prueba
(`vendedor_marta` / `vendedor_julio`, contraseña `demo1234`).

### Operación diaria

```
make help        # lista todos los comandos
make logs        # logs de todo (make logs s=web para uno solo)
make ps          # estado y healthchecks
make backup      # dump a docker/db/backups/grafiexpress_<fecha>.backup
make psql        # consola SQL
make manage c="showmigrations"
```

### Modo desarrollo

```
make dev
```

Monta el código del host en el contenedor (gunicorn con `--reload`, sin rebuild)
y publica PostgreSQL en `127.0.0.1:${DB_EXPOSE_PORT}` (5433 por defecto) para
conectarse con pgAdmin/DBeaver. Comandos que escriben archivos en el repo
(`makemigrations`) necesitan root: `docker compose exec -u root web python manage.py makemigrations`.

### Servicio de reportes (JasperReports)

Las facturas y remisiones (formato triplicado para formulario preimpreso) se
generan con JasperReports en el contenedor `jasper`:

- `docker/jasper/ReportServer.java`: servicio HTTP en Java 8 que carga los
  `.jasper` de `common/jasper/` (JasperReports 3.0.0, las mismas librerías que
  usaba el servidor original) y consulta directo la base `db`.
- `common/jasper/conector.py`: cliente HTTP que usa Django (`JASPER_URL`).

`common/jasper/server.py` (Jython + socket + pickle) quedó **obsoleto**: no
funcionaba con Python 3 y ya no se usa.

Si se modifica un reporte en iReport, recompilar el `.jasper` con
JasperReports 3.0.x, copiarlo a `common/jasper/` y reconstruir:
`docker compose up -d --build jasper`. Errores: `make logs s=jasper`.

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
