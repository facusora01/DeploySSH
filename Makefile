.PHONY: help up down build rebuild logs ps restart clean shell-back shell-front test test-coverage test-watch

help: ## Lista de comandos disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Levanta los servicios en background
	docker compose up -d

down: ## Apaga los servicios
	docker compose down

build: ## Builda las imágenes
	docker compose build
	docker compose exec back alembic upgrade head

rebuild: ## Builda sin cache y levanta
	docker compose build --no-cache
	docker compose up -d
	docker compose exec back alembic upgrade head

rebuild-back: ## Builda sin cache el back y levanta
	docker compose build back
	docker compose up -d back
	docker compose exec back alembic upgrade head

logs: ## Sigue los logs de todos los servicios
	docker compose logs -f

ps: ## Estado de los servicios
	docker compose ps

seed: ## Crea los usuarios en la db
	docker compose exec back python -m scripts.seed
	
restart: ## Reinicia los servicios
	docker compose restart

clean: ## Apaga, borra volúmenes e imágenes locales
	docker compose down -v --rmi local

shell-back: ## Abre bash en el contenedor del back
	docker compose exec back bash

shell-front: ## Abre sh en el contenedor del front
	docker compose exec front sh

test: ## Ejecuta los tests del backend
	cd backend 
	poetry run pytest 

test-coverage: ## Ejecuta los tests con coverage
	cd backend 
	poetry run pytest --cov=app --cov-report=term-missing

test-watch: ## Ejecuta los tests en modo watch
	cd backend
	poetry run pytest -v --watch

lock: ## Regenera el poetry.lock del backend (no requiere Poetry local)
	docker run --rm -v "$(CURDIR)/backend:/app" -w /app python:3.11-slim \
		sh -c "pip install poetry --quiet && poetry lock"
