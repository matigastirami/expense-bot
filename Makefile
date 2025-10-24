.PHONY: install install-libs install-api install-bot install-web
.PHONY: test test-libs test-api test-bot
.PHONY: lint format
.PHONY: dev-api dev-bot dev-web
.PHONY: docker-up docker-down

# Install all dependencies
install: install-libs install-api install-bot install-web

install-libs:
	pip install -e libs/database
	pip install -e libs/schemas
	pip install -e libs/utils
	pip install -e libs/integrations
	pip install -e libs/agent

install-api:
	pip install -r packages/api/requirements.txt

install-bot:
	pip install -r packages/telegram-bot/requirements.txt

install-web:
	cd packages/web && npm install

# Run tests
test: test-libs test-api test-bot

test-libs:
	pytest libs/database/tests
	pytest libs/utils/tests

test-api:
	pytest packages/api/tests

test-bot:
	pytest packages/telegram-bot/tests

# Development servers
dev-api:
	@echo "Starting Expense Tracker API..."
	PYTHONPATH=. python packages/api/run.py

dev-bot:
	cd packages/telegram-bot && python -m src.app

dev-web:
	cd packages/web && npm run dev

# Docker
docker-up:
	docker-compose -f infrastructure/docker/docker-compose.yml up

docker-down:
	docker-compose -f infrastructure/docker/docker-compose.yml down

# Migrations
migrate:
	cd libs/db && alembic upgrade head

migration-create:
	cd libs/db && alembic revision --autogenerate -m "$(msg)"

# Testing
test-api-endpoints:
	@echo "Running API endpoint tests..."
	cd packages/api && python test_api.py
