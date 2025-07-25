# Default command - show available commands
default:
    @just --list

# Show current environment configuration
env-info:
    @echo "=== Current Environment Configuration ==="
    @echo "DB_PORT: ${DB_PORT:-5433} (PostgreSQL)"
    @echo "APP_PORT: ${APP_PORT:-8000} (FastAPI)"
    @echo "ADMINER_PORT: ${ADMINER_PORT:-8080} (Database GUI)"
    @echo ""
    @echo "To avoid port conflicts with other projects, this project uses:"
    @echo "- Port 5433 for PostgreSQL (instead of default 5432)"
    @echo "- Port 8000 for the application (standard default, parameterized)"
    @echo "- Port 8080 for Adminer (default, parameterized for conflicts)"

# Install project dependencies
install:
    uv sync --extra dev

# Start database containers
db-start:
    docker-compose up -d

# Stop database containers
db-stop:
    docker-compose down

# Run database migrations
migrate:
    uv run alembic upgrade head

# Run all tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=src --cov-report=html

# Run specific test file
test-file FILE:
    uv run pytest {{ FILE }} -v

# Run all checks
check:
    @just format-check
    @just lint
    # @just typecheck
    @just test

# Fix and check
fc:
    @echo "Running all fixes..."
    uv run ruff check src/ tests/ --fix
    uv run ruff format src/ tests/
    @echo "Running all checks..."
    @just check

# Format code
format:
    uv run ruff format src/ tests/

# Format code (check only)
format-check:
    uv run ruff format --check src/ tests/

# Lint code
lint:
    uv run ruff check src/ tests/

# Type check
typecheck:
    uv run mypy src/

# Run development server with live reloading
dev:
    uv run dev

# Run production server
run:
    uv run python main.py

# Seed database with example data
seed:
    uv run python seed_database.py

# Create new migration
migrate-create MSG:
    uv run alembic revision --autogenerate -m "{{ MSG }}"

# Rollback last migration
migrate-rollback:
    uv run alembic downgrade -1

# Full setup - install deps, start db, migrate, and run tests
setup: install db-start migrate test

# Quick start - start db and run dev server
quick-start: db-start migrate dev

# Clean everything - stop db, remove volumes
clean:
    docker-compose down -v

# Check project status
status:
    @echo "=== Docker Status ==="
    @docker-compose ps
    @echo "\n=== Database Connection ==="
    @docker-compose exec -T postgres pg_isready -U postgres || echo "Database not ready"
    @echo "\n=== Python Dependencies ==="
    @uv pip list | head -5
    @echo "... (truncated)"

# Run CLI commands
cli *ARGS:
    uv run chatapp {{ ARGS }}

# Build Docker image
docker-build:
    docker build -t chat-app .

# Run with Docker Compose (build and start)
docker-up:
    docker-compose up --build

# View logs
logs:
    docker-compose logs -f

# Database shell
db-shell:
    docker-compose exec postgres psql -U postgres -d chatapp

# Python shell with app context
shell:
    uv run python -i -c "from src.infrastructure.container.container import AppContainer; container = AppContainer(); print('Container loaded. Access services via: container.<service_name>()')"

# Profile the application
profile TYPE="flamegraph" DURATION="30":
    uv run chatapp profile --type {{ TYPE }} --duration {{ DURATION }}

# Fix common issues
fix-port-conflict:
    @echo "Stopping conflicting PostgreSQL containers..."
    @docker ps -q --filter "publish=5432" | xargs -r docker stop
    @echo "Port 5432 should now be free"

# Health check
health:
    @curl -s http://localhost:${APP_PORT:-8000}/ || echo "API not running"
    @echo "\n"
    @curl -s http://localhost:${ADMINER_PORT:-8080}/ > /dev/null && echo "Adminer is running at http://localhost:${ADMINER_PORT:-8080}" || echo "Adminer not running"