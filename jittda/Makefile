.PHONY: up down logs shell test lint clean tunnel-up tunnel-down sonar-scan prod-up prod-down prod-build

# --- Cloudflare Tunnel (독립 생명주기) ---
tunnel-up:
	cd ../infra-tunnel && docker compose up -d

tunnel-down:
	cd ../infra-tunnel && docker compose down

# --- 개발 환경 관리 ---
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f backend

logs-all:
	docker compose logs -f

shell:
	docker compose exec backend bash

# --- 테스트 ---
test:
	docker compose exec backend pytest tests/ -v

test-domain:
	docker compose exec backend pytest tests/domain/ -v

test-infra:
	docker compose exec backend pytest tests/infrastructure/ -v

test-e2e:
	docker compose exec backend pytest tests/e2e/ -v

test-cov:
	docker compose exec backend pytest tests/ --cov=src --cov-report=html -v

# --- 코드 품질 ---
lint:
	docker compose exec backend ruff check src/

format:
	docker compose exec backend ruff format src/

# --- SonarQube 분석 (On-Demand) ---
sonar-scan:
	docker compose --profile analysis up -d sonarqube
	@echo "Waiting for SonarQube to start..."
	@sleep 30
	docker compose --profile analysis up sonar-scanner

# --- 프로덕션 ---
prod-build:
	docker compose -f docker-compose.yml build

prod-up:
	docker compose -f docker-compose.yml up -d

prod-down:
	docker compose -f docker-compose.yml down

prod-logs:
	docker compose -f docker-compose.yml logs -f

# --- 정리 ---
clean:
	docker compose down -v

infra-clean:
	docker compose down -v --remove-orphans
	docker volume prune -f
