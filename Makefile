.PHONY: up down test lint migrate seed

up:
	docker compose -f infra/docker-compose.yml up --build

down:
	docker compose -f infra/docker-compose.yml down

test:
	cd apps/api && ../../.venv/Scripts/python -m pytest
	cd apps/web && npm test

lint:
	cd apps/api && ../../.venv/Scripts/ruff check .
	cd apps/api && ../../.venv/Scripts/mypy app
	cd apps/web && npm run lint

migrate:
	cd apps/api && ../../.venv/Scripts/alembic -c alembic.ini upgrade head

seed:
	cd apps/api && ../../.venv/Scripts/python -m app.simulator.cli seed
