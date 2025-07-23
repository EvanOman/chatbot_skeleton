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

from src.infrastructure.container.container import Container
from src.infrastructure.database.models import Base
from src.main import app

# Test configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/chatapp_test",
)

# Override database URL for testing if not already set
if "TEST_DATABASE_URL" not in os.environ:
    os.environ["DB_DATABASE"] = "chatapp_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession]:
    """Provide a database session for testing."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def clean_db(db_session: AsyncSession):
    """Clean database before each test."""
    # Clean up all data before test
    await db_session.execute(text("TRUNCATE TABLE chat_message CASCADE"))
    await db_session.execute(text("TRUNCATE TABLE chat_thread CASCADE"))
    await db_session.commit()

    yield

    # Clean up after test
    await db_session.execute(text("TRUNCATE TABLE chat_message CASCADE"))
    await db_session.execute(text("TRUNCATE TABLE chat_thread CASCADE"))
    await db_session.commit()


@pytest.fixture
def test_client() -> Generator[TestClient]:
    """Provide a test client for synchronous testing."""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    """Provide an async client for testing."""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


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
        assert (
            actual_count == expected_count
        ), f"Expected {expected_count} messages, got {actual_count}"


@pytest.fixture
def db_assertions():
    """Provide database assertion helpers."""
    return DatabaseAssertions()


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
            assert (
                self.elapsed < max_seconds
            ), f"Operation took {self.elapsed:.2f}s, expected < {max_seconds}s"

    return Timer()


# WebSocket testing helpers
@pytest.fixture
def websocket_url():
    """Provide WebSocket URL for testing."""
    return "ws://localhost:8000/ws"


# File upload testing helpers
@pytest.fixture
def sample_file_upload():
    """Provide sample file upload data."""
    import base64

    content = b"This is test file content"
    encoded = base64.b64encode(content).decode()

    return {"filename": "test.txt", "content": encoded, "content_type": "text/plain"}
