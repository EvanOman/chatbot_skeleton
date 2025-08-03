"""
Pytest configuration and shared fixtures for integration tests.

This file provides common fixtures and configuration that can be used
across all test modules.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.models import Base
from src.infrastructure.di.container import (
    TestingContainer,
    reset_application_container,
)
from src.main import app

# Set testing environment
os.environ["TESTING"] = "true"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session.

    This session-scoped event loop prevents asyncpg 'another operation is in progress'
    errors by ensuring all async operations within a test session use the same loop.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_container():
    """Create test container with SQLite database."""
    # Reset any existing container
    reset_application_container()

    # Create testing container
    container = TestingContainer()

    # Initialize database
    db = await container.get_database()
    async with db.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield container

    # Cleanup
    await container.cleanup()
    reset_application_container()


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_container):
    """Get test database engine from container."""
    db = await test_container.get_database()
    return db.get_engine()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession]:
    """Provide a database session for testing with proper transaction isolation.

    Each test gets a fresh session. The session will automatically handle
    cleanup through the context manager.
    """
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            # Ensure any pending transaction is handled
            if session.in_transaction():
                await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def clean_db(test_engine):
    """Clean database before and after each test using separate session.

    Uses a separate session to avoid transaction conflicts with the main test session.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    # Create a separate session for cleanup
    cleanup_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with cleanup_session_factory() as session:
        # Clean up all data before test - SQLite compatible
        await session.execute(text("DELETE FROM chat_message"))
        await session.execute(text("DELETE FROM chat_thread"))
        await session.commit()

    yield

    # Clean up after test
    async with cleanup_session_factory() as session:
        await session.execute(text("DELETE FROM chat_message"))
        await session.execute(text("DELETE FROM chat_thread"))
        await session.commit()


@pytest_asyncio.fixture(scope="session")
async def test_session_factory(test_engine):
    """Provide a session factory for dependency injection in tests."""
    from sqlalchemy.orm import sessionmaker

    return sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def test_client() -> Generator[TestClient]:
    """Provide a test client for synchronous testing."""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Provide an async client for testing with database dependency override."""
    from httpx import ASGITransport

    from src.presentation.api.dependencies import get_database_session

    # Override the database session dependency for testing
    async def _get_test_session():
        yield db_session

    app.dependency_overrides[get_database_session] = _get_test_session

    transport = ASGITransport(app=app)
    client = None
    try:
        client = AsyncClient(transport=transport, base_url="http://test")
        yield client
    finally:
        if client:
            await client.aclose()
        # Clean up the dependency override
        if get_database_session in app.dependency_overrides:
            del app.dependency_overrides[get_database_session]


@pytest.fixture
def test_user_id() -> UUID:
    """Provide a consistent test user ID."""
    return UUID("123e4567-e89b-12d3-a456-426614174000")


@pytest.fixture
def alt_user_id() -> UUID:
    """Provide an alternative test user ID."""
    return UUID("987fcdeb-51d2-43a1-b123-426614174999")


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_text_file(temp_dir: Path) -> Path:
    """Create a sample text file for testing."""
    file_path = temp_dir / "sample.txt"
    file_path.write_text("This is a sample text file for testing purposes.")
    return file_path


@pytest.fixture
def sample_json_file(temp_dir: Path) -> Path:
    """Create a sample JSON file for testing."""
    import json

    file_path = temp_dir / "sample.json"
    data = {"name": "Test Data", "values": [1, 2, 3, 4, 5], "nested": {"key": "value"}}
    file_path.write_text(json.dumps(data, indent=2))
    return file_path


# Pytest markers for different test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (slower)"
    )
    config.addinivalue_line("markers", "unit: mark test as unit test (faster)")
    config.addinivalue_line("markers", "api: mark test as API test")
    config.addinivalue_line("markers", "websocket: mark test as WebSocket test")
    config.addinivalue_line("markers", "agent: mark test as agent/AI test")
    config.addinivalue_line("markers", "database: mark test as database test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Skip tests based on environment
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment."""
    # Skip integration tests in CI if database not available
    if os.getenv("SKIP_INTEGRATION_TESTS", "false").lower() == "true":
        skip_integration = pytest.mark.skip(reason="Integration tests disabled")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

    # Skip slow tests if requested
    if os.getenv("SKIP_SLOW_TESTS", "false").lower() == "true":
        skip_slow = pytest.mark.skip(reason="Slow tests disabled")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


# Custom assertion helpers
class DatabaseAssertions:
    """Helper class for database-related assertions."""

    @staticmethod
    async def assert_thread_exists(session: AsyncSession, thread_id: UUID):
        """Assert that a thread exists in the database."""
        from src.infrastructure.database.models import ChatThreadModel

        result = await session.get(ChatThreadModel, thread_id)
        assert result is not None, f"Thread {thread_id} not found in database"

    @staticmethod
    async def assert_message_count(
        session: AsyncSession, thread_id: UUID, expected_count: int
    ):
        """Assert the number of messages in a thread."""
        from src.infrastructure.database.models import ChatMessageModel

        result = await session.execute(
            text("SELECT COUNT(*) FROM chat_message WHERE thread_id = :thread_id"),
            {"thread_id": thread_id},
        )
        actual_count = result.scalar()
        assert actual_count == expected_count, (
            f"Expected {expected_count} messages, got {actual_count}"
        )


@pytest.fixture
def db_assertions():
    """Provide database assertion helpers."""
    return DatabaseAssertions()


# Database cleanup utilities
@pytest_asyncio.fixture
async def database_cleanup():
    """Ensure database connections are properly cleaned up after test session."""
    yield

    # Force cleanup of any remaining connections

    # Cleanup handled by test_container fixture
    pass


# Environment setup for different test scenarios
@pytest.fixture
def mock_environment(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        "OPENAI_API_KEY": "test-key-123",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "SERPAPI_API_KEY": "test-serpapi-key",
        "OPENWEATHER_API_KEY": "test-weather-key",
        "ENABLE_PROFILING": "true",
        "DB_ECHO": "false",
        "TESTING": "true",  # Ensure we're in testing mode with SQLite
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    return test_env


@pytest.fixture
def mock_no_api_keys(monkeypatch):
    """Mock environment with no API keys for fallback testing."""
    api_keys = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "SERPAPI_API_KEY",
        "OPENWEATHER_API_KEY",
    ]

    for key in api_keys:
        monkeypatch.delenv(key, raising=False)

    return {}


# Performance testing helpers
@pytest.fixture
def performance_timer():
    """Helper for measuring test performance."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

        def assert_under(self, max_seconds: float):
            assert self.elapsed is not None, "Timer not stopped"
            assert self.elapsed < max_seconds, (
                f"Operation took {self.elapsed:.2f}s, expected < {max_seconds}s"
            )

    return Timer()


# WebSocket testing helpers
@pytest.fixture
def websocket_url():
    """Provide WebSocket URL for testing."""
    from src.infrastructure.config.ports import PortConfig
    return f"{PortConfig.get_ws_url()}/ws"


# File upload testing helpers
@pytest.fixture
def sample_file_upload():
    """Provide sample file upload data."""
    import base64

    content = b"This is test file content"
    encoded = base64.b64encode(content).decode()

    return {"filename": "test.txt", "content": encoded, "content_type": "text/plain"}
