# AutoBiz Development Makefile
# Usage: make <target>

.PHONY: dev down build logs backend-logs frontend-logs db-shell migrate makemigrations backend-shell clean restart status

# Start all services in development mode (with build)
dev:
	docker compose up --build

# Stop all services
down:
	docker compose down

# Build all service images without starting
build:
	docker compose build

# Follow logs for all services
logs:
	docker compose logs -f

# Follow backend logs only
backend-logs:
	docker compose logs -f backend

# Follow frontend logs only
frontend-logs:
	docker compose logs -f frontend

# Open a psql shell to the database
db-shell:
	docker compose exec db psql -U autobiz autobiz

# Run database migrations
migrate:
	docker compose exec backend alembic upgrade head

# Create a new migration (usage: make makemigrations msg="description")
makemigrations:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

# Open a bash shell in the backend container
backend-shell:
	docker compose exec backend bash

# Stop all services and remove volumes (destroys data)
clean:
	docker compose down -v

# Restart all services
restart:
	docker compose restart

# Show status of all services
status:
	docker compose ps
