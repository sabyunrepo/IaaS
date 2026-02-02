.PHONY: up down logs test shell rebuild

up:
	docker compose up -d
	@echo "Services starting..."
	@echo "Backend:     http://localhost:8000"
	@echo "Temporal UI: http://localhost:8080"
	@echo "Langfuse:    http://localhost:3100"
	@echo "API Docs:    http://localhost:8000/docs"

down:
	docker compose down

logs:
	docker compose logs -f $(service)

test:
	docker compose exec backend pytest -v

shell:
	docker compose exec backend bash

rebuild:
	docker compose down -v
	docker compose build --no-cache
	docker compose up -d
