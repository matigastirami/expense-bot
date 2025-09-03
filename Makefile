.PHONY: help install dev test lint format typecheck clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  install     Install production dependencies"
	@echo "  dev         Install development dependencies"
	@echo "  test        Run tests"
	@echo "  lint        Run linting"
	@echo "  format      Format code"
	@echo "  typecheck   Run type checking"
	@echo "  clean       Clean cache files"
	@echo "  docker-up   Start services with docker-compose"
	@echo "  docker-down Stop services with docker-compose"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/

clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down