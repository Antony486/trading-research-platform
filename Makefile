.PHONY: help up down build test clean logs shell init-db

help:
	@echo "Available commands:"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make build      - Build Docker images"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean cache"
	@echo "  make logs       - View logs"
	@echo "  make shell-api  - Enter API container"
	@echo "  make init-db    - Initialize database"

up:
	docker-compose up -d
	@echo "Services started:"
	@echo "  API: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo "  Dashboard: http://localhost:8501"

down:
	docker-compose down -v

build:
	docker-compose build --no-cache

test:
	pytest tests/ -v --cov=services

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov

logs:
	docker-compose logs -f

shell-api:
	docker-compose exec api bash

init-db:
	docker-compose exec timescaledb psql -U admin -d trading_research -f /migrations/init.sql

status:
	docker-compose ps
	@echo "\n=== Service Health ==="
	@curl -s http://localhost:8000/health | jq . || echo "API not ready"
