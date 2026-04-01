# Saudi Sentinel — Makefile
# Convenience wrapper around docker compose commands.
# Usage: make <target>
# See README.md for full developer guide.

.PHONY: help level0-up level0-down level2-up level2-down level3-up level3-down \
        all-up all-down seed-aois notebooks test lint clean

PROJECT    := saudi-sentinel
ENV_FILE   := .env
DC         := docker compose -p $(PROJECT) --env-file $(ENV_FILE)
DC_LEVEL0  := $(DC) -f docker/docker-compose.level0.yml
DC_LEVEL2  := $(DC) -f docker/docker-compose.level0.yml -f docker/docker-compose.level2.yml
DC_LEVEL3  := $(DC) -f docker/docker-compose.level0.yml -f docker/docker-compose.level2.yml -f docker/docker-compose.level3.yml
DC_ALL     := $(DC) -f docker/docker-compose.yml

# Guard: abort early if .env doesn't exist
check-env:
	@test -f $(ENV_FILE) || (echo "\nERROR: $(ENV_FILE) not found.\nRun: cp .env.example .env  then fill in your credentials.\n" && exit 1)

help:
	@echo ""
	@echo "Saudi Sentinel — Make targets"
	@echo "================================="
	@echo "  level0-up      Start Level 0 (PostGIS, MinIO, Redis, Tile API)"
	@echo "  level0-down    Stop Level 0 services"
	@echo "  level2-up      Start Level 2 (Airflow, MLflow, Model Server, Grafana)"
	@echo "  level2-down    Stop Level 2 services"
	@echo "  level3-up      Start Level 3 (API Gateway, Frontend, Alert Worker)"
	@echo "  level3-down    Stop Level 3 services"
	@echo "  all-up         Start full stack (all levels)"
	@echo "  all-down       Stop all services"
	@echo "  seed-aois      Seed AOI definitions into PostGIS catalog"
	@echo "  notebooks      Start JupyterLab on port 8888"
	@echo "  test           Run test suite (in Docker)"
	@echo "  lint           Run ruff linter (in Docker)"
	@echo "  clean          Remove Python cache files"
	@echo ""

# --- Level 0 ---

level0-up: check-env
	@echo "Starting Level 0 (PostGIS, MinIO, Redis, Tile API)..."
	$(DC_LEVEL0) up -d
	@echo ""
	@echo "  Tile API:      http://localhost:8100"
	@echo "  MinIO Console: http://localhost:9001  (credentials in .env)"
	@echo ""

level0-down:
	$(DC_LEVEL0) down

seed-aois: check-env
	$(DC_LEVEL0) exec tile-api python /app/data_pipeline/seed_aois.py --config /app/data_pipeline/config/aois.yaml

# --- Level 2 ---

level2-up: check-env
	@echo "Starting Level 2 (Airflow, MLflow, Model Server, Prometheus, Grafana)..."
	$(DC_LEVEL2) up -d
	@echo ""
	@echo "  Airflow:      http://localhost:8080  (user: airflow / pass: airflow)"
	@echo "  MLflow:       http://localhost:5000"
	@echo "  Model Server: http://localhost:8200"
	@echo "  Grafana:      http://localhost:3000  (user: admin / pass from .env)"
	@echo ""

level2-down:
	$(DC_LEVEL2) down

# --- Level 3 ---

level3-up: check-env
	@echo "Starting Level 3 (API Gateway, Frontend, Alert Worker)..."
	$(DC_LEVEL3) up -d
	@echo ""
	@echo "  API Gateway: http://localhost:8300"
	@echo "  Frontend:    http://localhost:3001"
	@echo ""

level3-down:
	$(DC_LEVEL3) down

# --- Full stack ---

all-up: check-env
	$(DC_ALL) up -d

all-down:
	$(DC_ALL) down

# --- Notebooks ---

notebooks:
	@echo "Starting JupyterLab on http://localhost:8888 ..."
	docker build -f docker/notebooks.Dockerfile -t saudi-sentinel-notebooks .
	docker run --rm -p 8888:8888 \
		-v $(PWD)/notebooks:/app/notebooks \
		-v $(PWD)/shared:/app/shared \
		saudi-sentinel-notebooks

# --- Development (all run in Docker, no local Python needed) ---

test:
	docker build -f docker/data_pipeline.Dockerfile -t saudi-sentinel-test .
	docker run --rm \
		-v $(PWD)/tests:/app/tests \
		saudi-sentinel-test \
		sh -c "pip install -q pytest pytest-asyncio pytest-cov && pytest tests/ -v --tb=short"

lint:
	docker run --rm \
		-v $(PWD):/src \
		-w /src \
		python:3.11-slim \
		sh -c "pip install -q ruff && ruff check shared/ data_pipeline/ mlops/ system/ tests/"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
