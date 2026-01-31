.PHONY: help install up down logs shell test lint format clean

help:
	@echo "RoundtableTrading Development Commands"
	@echo "======================================="
	@echo "install    - Install all dependencies"
	@echo "up         - Start Docker services"
	@echo "down       - Stop Docker services"
	@echo "logs       - View Docker logs"
	@echo "shell      - PostgreSQL shell"
	@echo "redis-cli  - Redis CLI"
	@echo "test       - Run tests"
	@echo "lint       - Run linter"
	@echo "format     - Format code"
	@echo "clean      - Clean cache and temp files"

install:
	uv sync --all-extras

up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Services started successfully!"

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker exec -it roundtable_postgres psql -U roundtable -d roundtable_trading

redis-cli:
	docker exec -it roundtable_redis redis-cli

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
