#!/bin/bash

# Local testing script for Sample Chat App
# This script sets up the environment and runs tests locally

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_NAME="chatapp_test"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"

echo -e "${BLUE}🧪 Sample Chat App - Local Test Runner${NC}"
echo "========================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check database connection
check_database() {
    echo -e "${YELLOW}📊 Checking database connection...${NC}"

    if ! command_exists psql; then
        echo -e "${RED}❌ PostgreSQL client (psql) not found${NC}"
        echo "Please install PostgreSQL client tools"
        return 1
    fi

    if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "${RED}❌ Cannot connect to PostgreSQL database${NC}"
        echo "Please ensure PostgreSQL is running with the following settings:"
        echo "  Host: $DB_HOST"
        echo "  Port: $DB_PORT"
        echo "  User: $DB_USER"
        echo "  Password: $DB_PASSWORD"
        echo ""
        echo "You can start PostgreSQL with Docker:"
        echo "  docker-compose up -d"
        return 1
    fi

    echo -e "${GREEN}✅ Database connection successful${NC}"
}

# Function to setup test database
setup_test_database() {
    echo -e "${YELLOW}🗃️  Setting up test database...${NC}"

    # Create test database if it doesn't exist
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || {
        echo -e "${YELLOW}ℹ️  Test database already exists${NC}"
    }

    # Run migrations on test database
    export DB_HOST=$DB_HOST
    export DB_PORT=$DB_PORT
    export DB_USERNAME=$DB_USER
    export DB_PASSWORD=$DB_PASSWORD
    export DB_DATABASE=$DB_NAME

    echo -e "${YELLOW}🔄 Running database migrations...${NC}"
    uv run alembic upgrade head

    echo -e "${GREEN}✅ Test database setup complete${NC}"
}

# Function to run different test suites
run_tests() {
    local test_type="$1"
    local test_args="${@:2}"

    # Set environment variables
    export DB_HOST=$DB_HOST
    export DB_PORT=$DB_PORT
    export DB_USERNAME=$DB_USER
    export DB_PASSWORD=$DB_PASSWORD
    export DB_DATABASE=$DB_NAME
    export TEST_DATABASE_URL="postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/${DB_NAME}"

    case $test_type in
        "unit")
            echo -e "${BLUE}🔬 Running unit tests...${NC}"
            uv run pytest tests/test_basic_functionality.py -v --tb=short $test_args
            ;;
        "integration")
            echo -e "${BLUE}🔗 Running integration tests...${NC}"
            uv run pytest tests/test_integration.py -v --tb=short --maxfail=10 $test_args
            ;;
        "performance")
            echo -e "${BLUE}⚡ Running performance tests...${NC}"
            uv run pytest tests/test_performance.py -v --tb=short --maxfail=5 -m "not stress" $test_args
            ;;
        "stress")
            echo -e "${BLUE}💪 Running stress tests...${NC}"
            echo -e "${YELLOW}⚠️  Warning: Stress tests may take several minutes${NC}"
            uv run pytest tests/test_performance.py -v --tb=short -m "stress" $test_args
            ;;
        "api")
            echo -e "${BLUE}🌐 Running API tests...${NC}"
            uv run pytest tests/test_integration.py::TestAPIEndpoints tests/test_integration.py::TestExportFunctionality -v --tb=short $test_args
            ;;
        "agent")
            echo -e "${BLUE}🤖 Running agent tests...${NC}"
            uv run pytest tests/test_integration.py::TestDSPyAgent tests/test_integration.py::TestToolIntegrations -v --tb=short $test_args
            ;;
        "all")
            echo -e "${BLUE}🚀 Running all tests...${NC}"
            uv run pytest tests/ -v --tb=short --maxfail=15 --cov=src --cov-report=html --cov-report=term $test_args
            ;;
        "quick")
            echo -e "${BLUE}⚡ Running quick test suite...${NC}"
            uv run pytest tests/test_basic_functionality.py tests/test_integration.py::TestAPIEndpoints -v --tb=short $test_args
            ;;
        *)
            echo -e "${RED}❌ Unknown test type: $test_type${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0 [test-type] [pytest-args...]"
    echo ""
    echo -e "${BLUE}Test Types:${NC}"
    echo "  unit         - Run unit tests only (fast)"
    echo "  integration  - Run integration tests (requires database)"
    echo "  performance  - Run performance tests (excludes stress tests)"
    echo "  stress       - Run stress tests (slow, intensive)"
    echo "  api          - Run API endpoint tests"
    echo "  agent        - Run AI agent tests"
    echo "  all          - Run all tests with coverage"
    echo "  quick        - Run a quick subset of tests"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 unit                          # Run unit tests"
    echo "  $0 integration                   # Run integration tests"
    echo "  $0 all --maxfail=5              # Run all tests, stop after 5 failures"
    echo "  $0 performance --durations=5     # Run performance tests, show 5 slowest"
    echo "  $0 api -k test_create_thread     # Run specific API test"
}

# Function to check dependencies
check_dependencies() {
    echo -e "${YELLOW}📦 Checking dependencies...${NC}"

    if ! command_exists uv; then
        echo -e "${RED}❌ uv package manager not found${NC}"
        echo "Please install uv: https://github.com/astral-sh/uv"
        exit 1
    fi

    # Check if dependencies are installed
    if ! uv run python -c "import pytest" 2>/dev/null; then
        echo -e "${YELLOW}📥 Installing dependencies...${NC}"
        uv sync --extra dev
    fi

    echo -e "${GREEN}✅ Dependencies ready${NC}"
}

# Function to clean up test artifacts
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up test artifacts...${NC}"

    # Remove test cache
    rm -rf .pytest_cache/
    rm -rf tests/__pycache__/
    rm -rf src/__pycache__/

    # Remove coverage files
    rm -f .coverage
    rm -rf htmlcov/

    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Main execution
main() {
    # Parse arguments
    local test_type="quick"  # Default to quick tests
    local test_args=()

    if [ $# -gt 0 ]; then
        test_type="$1"
        shift
        test_args=("$@")
    fi

    # Handle special commands
    case $test_type in
        "help"|"-h"|"--help")
            show_usage
            exit 0
            ;;
        "clean"|"cleanup")
            cleanup
            exit 0
            ;;
    esac

    echo -e "${BLUE}Test Type:${NC} $test_type"
    echo -e "${BLUE}Test Args:${NC} ${test_args[*]}"
    echo ""

    # Run checks and setup
    check_dependencies
    check_database
    setup_test_database

    echo ""

    # Run tests
    start_time=$(date +%s)

    if run_tests "$test_type" "${test_args[@]}"; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))

        echo ""
        echo -e "${GREEN}✅ Tests completed successfully!${NC}"
        echo -e "${BLUE}Total time:${NC} ${duration}s"

        # Show coverage report if generated
        if [ -f htmlcov/index.html ]; then
            echo -e "${BLUE}Coverage report:${NC} htmlcov/index.html"
        fi
    else
        echo ""
        echo -e "${RED}❌ Tests failed${NC}"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
