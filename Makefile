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
	@echo "Starting Telegram Bot..."
	./run_bot.sh

dev-agent-cli:
	@echo "Finance Agent CLI - Pass your query as an argument"
	@echo "Example: make dev-agent-cli QUERY='How much did I spend this week?'"
	PYTHONPATH=. python packages/agent/cli.py $(QUERY)

dev-agent-repl:
	@echo "Starting Finance Agent REPL..."
	PYTHONPATH=. python packages/agent/repl.py

dev-web:
	cd packages/web && npm run dev

# Docker - Development
docker-dev-build:
	@echo "Building Docker images for development..."
	docker-compose build

docker-dev-up:
	@echo "Starting development environment with Docker..."
	docker-compose up -d

docker-dev-down:
	@echo "Stopping development environment..."
	docker-compose down

docker-dev-logs:
	docker-compose logs -f

docker-dev-restart:
	docker-compose restart

# Docker - Production
docker-prod-build:
	@echo "Building Docker images for production..."
	docker-compose -f docker-compose.prod.yml build

docker-prod-up:
	@echo "Starting production environment with Docker..."
	docker-compose -f docker-compose.prod.yml up -d

docker-prod-down:
	@echo "Stopping production environment..."
	docker-compose -f docker-compose.prod.yml down

docker-prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

docker-prod-ps:
	docker-compose -f docker-compose.prod.yml ps

# Docker - Service-specific
docker-build-api:
	docker-compose build api

docker-build-bot:
	docker-compose build bot

docker-build-agent:
	docker-compose build agent

# Docker - Cleanup
docker-clean:
	@echo "Removing all containers, images, and volumes..."
	docker-compose down -v
	docker system prune -af

# Docker - Database
docker-db-backup:
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U finance finance > backup_$$(date +%Y%m%d_%H%M%S).sql

docker-db-restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T postgres psql -U finance finance < $$backup_file

# Migrations
migrate:
	cd libs/db && alembic upgrade head

migration-create:
	cd libs/db && alembic revision --autogenerate -m "$(msg)"

# Testing
test-api-endpoints:
	@echo "Running API endpoint tests..."
	cd packages/api && python test_api.py
