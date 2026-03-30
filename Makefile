.PHONY: dev dev-build dev-down dev-logs help

help:
	@echo "Available commands:"
	@echo "  make dev        - Start all services with Docker Compose"
	@echo "  make dev-build  - Rebuild and start all services"
	@echo "  make dev-down   - Stop all services"
	@echo "  make dev-logs   - Tail logs from all services"

dev:
	@docker compose up

dev-build:
	@docker compose up --build

dev-down:
	@docker compose down

dev-logs:
	@docker compose logs -f
