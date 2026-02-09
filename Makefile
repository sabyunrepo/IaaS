.PHONY: up down logs test shell rebuild tunnel-up tunnel-down tunnel-logs

# ============================================
# Cloudflare Tunnel (별도 프로젝트로 관리)
# ============================================
tunnel-up:
	docker compose -f docker-compose.tunnel.yml -p cloudflare up -d
	@echo "Cloudflare Tunnel started"

tunnel-down:
	docker compose -f docker-compose.tunnel.yml -p cloudflare down
	@echo "Cloudflare Tunnel stopped"

tunnel-logs:
	docker compose -f docker-compose.tunnel.yml -p cloudflare logs -f

# ============================================
# Main Services
# ============================================
up:
	docker compose --profile worker up -d
	@echo "Services starting..."
	@echo "Backend:     http://localhost:8000"
	@echo "Temporal UI: http://localhost:8080"
	@echo "Langfuse:    http://localhost:3100"
	@echo "API Docs:    http://localhost:8000/docs"

down:
	docker compose --profile worker down

logs:
	docker compose logs -f $(service)

test:
	docker compose exec backend pytest -v

shell:
	docker compose exec backend bash

rebuild:
	docker compose --profile worker down
	docker compose build --no-cache
	docker compose --profile worker up -d
