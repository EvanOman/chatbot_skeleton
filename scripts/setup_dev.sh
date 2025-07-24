#!/bin/bash

# Development environment setup script
# Run this after cloning the repository

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up development environment${NC}"
echo "========================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed${NC}"
    echo "Please install uv: https://github.com/astral-sh/uv"
    exit 1
fi

echo -e "${YELLOW}📦 Installing dependencies...${NC}"
uv sync --extra dev

echo -e "${YELLOW}🪝 Installing pre-commit hooks...${NC}"
uv run pre-commit install
uv run pre-commit install --hook-type pre-push

echo -e "${YELLOW}🔧 Running pre-commit on all files (initial setup)...${NC}"
uv run pre-commit run --all-files || {
    echo -e "${YELLOW}⚠️  Pre-commit found issues and fixed them${NC}"
    echo -e "${YELLOW}📝 Please review the changes and commit them${NC}"
}

echo -e "${YELLOW}📊 Checking if PostgreSQL is running...${NC}"
if docker-compose ps postgres &> /dev/null && [ "$(docker-compose ps postgres | grep Up)" ]; then
    echo -e "${GREEN}✅ PostgreSQL is already running${NC}"
else
    echo -e "${YELLOW}🐳 Starting PostgreSQL with Docker Compose...${NC}"
    docker-compose up -d postgres

    # Wait for PostgreSQL to be ready
    echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
            echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
            break
        fi
        sleep 1
    done
fi

echo -e "${YELLOW}🗃️  Running database migrations...${NC}"
uv run alembic upgrade head

echo -e "${YELLOW}🧪 Running basic tests to verify setup...${NC}"
uv run pytest tests/test_basic_functionality.py -v

echo ""
echo -e "${GREEN}✅ Development environment setup complete!${NC}"
echo ""
echo -e "${BLUE}🎯 What's configured:${NC}"
echo "  • All Python dependencies installed"
echo "  • Pre-commit hooks installed (runs on every commit)"
echo "  • Pre-push hooks installed (runs tests before push)"
echo "  • PostgreSQL database running and migrated"
echo "  • Basic tests passing"
echo ""
echo -e "${BLUE}📝 Development workflow:${NC}"
echo "  • Pre-commit automatically runs linting/formatting on commit"
echo "  • Pre-push automatically runs basic tests before push"
echo "  • Run './scripts/test_local.sh' for comprehensive testing"
echo "  • Use 'uv run dev' for development with live reloading"
echo ""
echo -e "${BLUE}🔧 Useful commands:${NC}"
echo "  uv run pre-commit run --all-files  # Run linting on all files"
echo "  ./scripts/test_local.sh integration # Run integration tests"
echo "  uv run chatapp status              # Check application status"
echo "  docker-compose up -d               # Start all services"
echo ""
echo -e "${GREEN}Happy coding! 🎉${NC}"
