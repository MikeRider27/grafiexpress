# Atajos para operar el stack Docker de GrafiExpress. "make help" lista todo.
COMPOSE     ?= docker compose
DEV_COMPOSE  = $(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml
BACKUP_DIR   = docker/db/backups
STAMP       := $(shell date +%Y%m%d_%H%M%S)

.DEFAULT_GOAL := help
.PHONY: help init up dev down restart build logs ps shell manage migrate \
        superuser psql backup restore reset-db demo

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

init: ## Crea .env a partir de .env.example con claves aleatorias
	@test -f .env && echo ".env ya existe, no se toca" || { \
		cp .env.example .env; \
		sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$$(python3 -c 'import secrets;print(secrets.token_urlsafe(50))')|" .env; \
		sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=$$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')|" .env; \
		echo ".env creado"; }

up: ## Levanta el stack (modo producción)
	$(COMPOSE) up -d --build

dev: ## Levanta el stack en modo desarrollo (código montado + recarga)
	$(DEV_COMPOSE) up -d --build

down: ## Detiene el stack (los datos quedan en los volúmenes)
	$(COMPOSE) down

restart: ## Reinicia la app
	$(COMPOSE) restart web

build: ## Reconstruye la imagen de la app
	$(COMPOSE) build web

logs: ## Sigue los logs (make logs s=web para uno solo)
	$(COMPOSE) logs -f --tail=100 $(s)

ps: ## Estado de los servicios
	$(COMPOSE) ps

shell: ## Shell dentro del contenedor web
	$(COMPOSE) exec web sh

manage: ## Ejecuta un comando de Django: make manage c="showmigrations"
	$(COMPOSE) exec web python manage.py $(c)

migrate: ## Aplica migraciones
	$(COMPOSE) exec web python manage.py migrate

superuser: ## Crea un superusuario de Django
	$(COMPOSE) exec web python manage.py createsuperuser

demo: ## Carga datos FALSOS de prueba (solo en una base sin clientes)
	$(COMPOSE) exec web python manage.py cargar_datos_demo

psql: ## Consola psql sobre la base interna
	$(COMPOSE) exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

backup: ## Genera un dump (formato custom) en docker/db/backups/
	$(COMPOSE) exec -T db sh -c 'pg_dump -Fc -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"' \
		> $(BACKUP_DIR)/grafiexpress_$(STAMP).backup
	@echo "Backup: $(BACKUP_DIR)/grafiexpress_$(STAMP).backup"

restore: ## Restaura un dump sobre la base actual: make restore f=ruta/al.backup
	@test -n "$(f)" || { echo "Uso: make restore f=ruta/al/dump.backup"; exit 1; }
	@echo "Se van a REEMPLAZAR los datos actuales con $(f). Ctrl+C para cancelar."; sleep 5
	$(COMPOSE) stop web
	$(COMPOSE) exec -T db sh -c 'pg_restore --clean --if-exists --no-owner --no-acl -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"' < $(f)
	$(COMPOSE) start web

reset-db: ## BORRA la base y la recrea desde cero (vuelve a aplicar DB_SEED_FILE)
	@echo "Se va a BORRAR el volumen de la base de datos. Ctrl+C para cancelar."; sleep 5
	$(COMPOSE) down
	docker volume rm grafiexpress_pgdata
	$(COMPOSE) up -d
