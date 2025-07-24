# Testing Guide for Sample Chat App

This document provides comprehensive information about testing the Sample Chat App, including setup, test execution, and CI/CD integration.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Architecture](#test-architecture)
- [Local Testing](#local-testing)
- [Test Categories](#test-categories)
- [CI/CD Integration](#cicd-integration)
- [Performance Testing](#performance-testing)
- [Troubleshooting](#troubleshooting)

## 🔍 Overview

The Sample Chat App includes a comprehensive testing suite with multiple layers:

- **Unit Tests**: Fast, isolated component testing
- **Integration Tests**: End-to-end functionality testing
- **Performance Tests**: Load testing and benchmarks
- **API Tests**: HTTP endpoint validation
- **Agent Tests**: AI agent and tool functionality
- **Database Tests**: Data persistence and query performance

## 🏗️ Test Architecture

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_basic_functionality.py   # Unit tests
├── test_integration.py      # Integration tests
└── test_performance.py      # Performance and load tests
```

### Key Testing Components

1. **Pytest Configuration** (`pytest.ini`): Test discovery, markers, and global settings
2. **Test Fixtures** (`conftest.py`): Shared test utilities and database setup
3. **Local Test Script** (`scripts/test_local.sh`): Interactive testing with database setup
4. **CI Workflows** (`.github/workflows/`): Automated testing pipelines

## 🚀 Local Testing

### Quick Start

The easiest way to run tests locally is using the interactive test script:

```bash
# Make script executable (first time only)
chmod +x scripts/test_local.sh

# Run interactive test menu
./scripts/test_local.sh

# Or specify test type directly
./scripts/test_local.sh integration
```

### Prerequisites

1. **PostgreSQL Database**:
   ```bash
   # Using Docker (recommended)
   docker-compose up -d

   # Or use existing PostgreSQL instance
   # Ensure database credentials match configuration
   ```

2. **Python Dependencies**:
   ```bash
   uv sync --extra dev
   ```

### Test Script Options

```bash
./scripts/test_local.sh [test-type] [pytest-args...]

# Test Types:
unit         # Fast unit tests (no database required)
integration  # Full integration tests (requires database)
performance  # Performance benchmarks (excludes stress tests)
stress       # Intensive stress tests (slow)
api          # API endpoint tests
agent        # AI agent functionality tests
all          # Complete test suite with coverage
quick        # Fast subset for development
clean        # Clean up test artifacts
```

### Manual Test Execution

```bash
# Unit tests only
uv run pytest tests/test_basic_functionality.py -v

# Integration tests
export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/chatapp_test"
uv run pytest tests/test_integration.py -v

# Performance tests
uv run pytest tests/test_performance.py -v -m "not stress"

# All tests with coverage
uv run pytest tests/ --cov=src --cov-report=html --cov-report=term
```

## 📊 Test Categories

### Unit Tests (`test_basic_functionality.py`)

Fast, isolated tests that don't require external dependencies:

- Domain entity validation
- Value object behavior
- Service layer logic
- Basic API endpoint imports

**Run with**: `./scripts/test_local.sh unit`

### Integration Tests (`test_integration.py`)

End-to-end tests with real database and API interactions:

- **API Endpoints**: Complete request/response cycles
- **Database Operations**: CRUD operations with real data
- **WebSocket Connections**: Real-time communication testing
- **Agent Functionality**: AI agent with tool integrations
- **Export Features**: Multi-format conversation exports
- **Webhook System**: External integration testing

**Run with**: `./scripts/test_local.sh integration`

### Performance Tests (`test_performance.py`)

Performance benchmarks and load testing:

- **Response Time Tests**: API endpoint performance benchmarks
- **Concurrent Request Handling**: Multi-user simulation
- **Database Performance**: Query optimization validation
- **Memory Usage Tests**: Memory leak detection
- **Agent Performance**: AI response time benchmarks
- **Stress Tests**: System limit testing

**Run with**: `./scripts/test_local.sh performance`

## 🔧 Test Configuration

### Environment Variables

```bash
# Database Configuration
export DB_HOST=localhost
export DB_PORT=5432
export DB_USERNAME=postgres
export DB_PASSWORD=postgres
export DB_DATABASE=chatapp_test

# Test-specific Settings
export TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chatapp_test
export SKIP_SLOW_TESTS=false
export SKIP_INTEGRATION_TESTS=false
export ENABLE_PROFILING=true

# API Keys for Agent Testing (use test values)
export OPENAI_API_KEY=test-key-123
export ANTHROPIC_API_KEY=test-anthropic-key
export SERPAPI_API_KEY=test-serpapi-key
export OPENWEATHER_API_KEY=test-weather-key
```

### Pytest Markers

Use markers to run specific test categories:

```bash
# Run only unit tests
uv run pytest -m "unit"

# Run only integration tests
uv run pytest -m "integration"

# Run API tests
uv run pytest -m "api"

# Run agent tests
uv run pytest -m "agent"

# Skip slow tests
uv run pytest -m "not slow"

# Run performance tests
uv run pytest -m "performance"
```

### Test Database Setup

The test suite automatically manages test databases:

1. **Automatic Creation**: Test script creates `chatapp_test` database
2. **Schema Migrations**: Alembic migrations run automatically
3. **Data Cleanup**: Each test gets a clean database state
4. **Parallel Testing**: Separate databases for concurrent test execution

## 🤖 CI/CD Integration

### GitHub Actions Workflows

#### 1. Main CI Pipeline (`.github/workflows/ci.yml`)

Runs on every push and pull request:

- **Unit Tests**: Fast validation without external dependencies
- **Integration Tests**: Core functionality validation
- **Code Quality**: Linting and formatting checks
- **Coverage Reporting**: Codecov integration

#### 2. Integration Test Pipeline (`.github/workflows/integration.yml`)

Comprehensive testing with matrix strategy:

- **Matrix Testing**: Parallel execution across test categories
- **API Tests**: Full HTTP endpoint validation
- **Agent Tests**: AI functionality with mocked APIs
- **Database Tests**: Data persistence validation
- **Performance Tests**: Response time benchmarks
- **Stress Tests**: System limit validation

#### 3. Scheduled Testing

- **Nightly Builds**: Complete test suite execution
- **Performance Monitoring**: Automated performance regression detection
- **Coverage Tracking**: Historical coverage trend analysis

### CI Environment Configuration

```yaml
# Matrix strategy for parallel testing
strategy:
  matrix:
    test-suite: [api, agent, database, performance]

# Environment variables
env:
  DB_HOST: localhost
  DB_PORT: 5432
  DB_USERNAME: postgres
  DB_PASSWORD: postgres
  TEST_DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/chatapp_test
```

## ⚡ Performance Testing

### Response Time Benchmarks

Performance tests validate that the application meets response time requirements:

- **API Endpoints**: < 2 seconds for thread creation, < 5 seconds for message processing
- **Database Queries**: < 1 second for message retrieval
- **Agent Responses**: < 10 seconds for AI-generated responses
- **Export Operations**: < 3 seconds for conversation exports

### Load Testing

Concurrent request testing validates system behavior under load:

- **Thread Creation**: 10 concurrent thread creations
- **Message Sending**: 5 concurrent messages to same thread
- **Static Content**: 20 concurrent requests to static endpoints

### Memory Usage Validation

Memory tests ensure the application doesn't have memory leaks:

- **Large Conversations**: Memory usage with 50+ messages
- **Agent Memory Management**: Memory cleanup after agent operations
- **Concurrent Operations**: Memory behavior under concurrent load

### Stress Testing

Intensive tests that validate system limits:

- **Rapid API Requests**: 20 rapid successive requests
- **Large Messages**: Handling of 10KB+ message content
- **Database Bulk Operations**: 100+ concurrent database operations

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check PostgreSQL is running
docker-compose ps

# Verify connection manually
PGPASSWORD=postgres psql -h localhost -U postgres -c "SELECT 1;"

# Reset test database
./scripts/test_local.sh clean
dropdb chatapp_test -h localhost -U postgres
createdb chatapp_test -h localhost -U postgres
```

#### 2. Test Timeout Issues

```bash
# Increase timeout for slow tests
uv run pytest tests/ --timeout=600

# Skip slow tests during development
uv run pytest tests/ -m "not slow"

# Run specific test with debug output
uv run pytest tests/test_integration.py::TestAPIEndpoints::test_create_thread -v -s
```

#### 3. Import or Dependency Errors

```bash
# Reinstall dependencies
uv sync --extra dev --force

# Check Python path
uv run python -c "import sys; print(sys.path)"

# Verify installation
uv run python -c "import pytest, httpx, sqlalchemy; print('Dependencies OK')"
```

#### 4. Agent Test Failures

```bash
# Set mock API keys for testing
export OPENAI_API_KEY=test-key-123
export ANTHROPIC_API_KEY=test-anthropic-key

# Run agent tests with fallback enabled
uv run pytest tests/test_integration.py::TestDSPyAgent -v -s

# Skip agent tests if APIs unavailable
uv run pytest tests/ -m "not agent"
```

### Debug Mode

Enable verbose debugging for test failures:

```bash
# Maximum verbosity
uv run pytest tests/ -vvv --tb=long --capture=no

# Debug specific test
uv run pytest tests/test_integration.py::TestAPIEndpoints::test_create_thread -vvv -s

# Print debug output
uv run pytest tests/ --capture=no --log-cli-level=DEBUG
```

### Performance Debugging

Identify slow tests and performance bottlenecks:

```bash
# Show 10 slowest tests
uv run pytest tests/ --durations=10

# Profile test execution
uv run pytest tests/ --profile

# Memory usage tracking
uv run pytest tests/ --memray
```

## 📈 Coverage and Reporting

### Coverage Reports

```bash
# Generate HTML coverage report
uv run pytest tests/ --cov=src --cov-report=html

# View coverage in terminal
uv run pytest tests/ --cov=src --cov-report=term

# Generate XML for CI integration
uv run pytest tests/ --cov=src --cov-report=xml
```

### Test Reports

```bash
# JUnit XML report
uv run pytest tests/ --junit-xml=report.xml

# JSON test results
uv run pytest tests/ --json=report.json

# HTML test report
uv run pytest tests/ --html=report.html --self-contained-html
```

## 🎯 Best Practices

### Writing Tests

1. **Use Descriptive Names**: Test method names should clearly describe what is being tested
2. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
3. **Test One Thing**: Each test should validate a single behavior or outcome
4. **Use Fixtures**: Leverage pytest fixtures for common test setup and teardown
5. **Mock External Dependencies**: Use mocks for external APIs and services

### Running Tests

1. **Start with Unit Tests**: Run fast unit tests during development
2. **Use Integration Tests for Validation**: Run integration tests before commits
3. **Performance Tests for Optimization**: Use performance tests to identify bottlenecks
4. **CI Tests for Quality Gates**: Let CI handle comprehensive testing

### Debugging Tests

1. **Use Verbose Output**: Add `-v` flag for detailed test output
2. **Isolate Failures**: Run specific failed tests to debug issues
3. **Check Logs**: Review application logs for error details
4. **Use Debugger**: Add `import pdb; pdb.set_trace()` for interactive debugging

---

For additional help or questions about testing, please refer to the main [README.md](README.md) or open an issue in the project repository.
