.PHONY: up down build logs migrate test seed clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f api

logs-worker:
	docker compose logs -f celery-worker

migrate:
	docker compose exec api alembic upgrade head

migration:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

test:
	docker compose exec api pytest tests/ -v

test-cov:
	docker compose exec api pytest tests/ -v --cov=app --cov-report=html

seed:
	docker compose exec api python scripts/seed.py

health:
	curl -s http://localhost:8000/api/v1/health | python -m json.tool

clean:
	docker compose down -v
	rm -rf backend/build backend/.pytest_cache

shell:
	docker compose exec api bash

db-shell:
	docker compose exec db psql -U pa_user -d prior_auth

redis-cli:
	docker compose exec redis redis-cli
