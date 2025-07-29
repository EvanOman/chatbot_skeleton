"""Tests for SQLite repository implementation."""

import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from src.application.services.uow_chat_service import UowChatService
from src.infrastructure.database.repository_factory import (
    DatabaseType,
    create_chat_repository_factory,
)


@pytest_asyncio.fixture
async def sqlite_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest.fixture
def sqlite_repo_factory(sqlite_engine):
    """Create a SQLite repository factory."""
    return create_chat_repository_factory(sqlite_engine, DatabaseType.SQLITE)


@pytest.mark.asyncio
async def test_sqlite_repository_basic_operations(sqlite_repo_factory):
    """Test basic CRUD operations with SQLite repository."""
    thread_id = uuid4()
    user_id = uuid4()

    # Test thread creation
    async with sqlite_repo_factory() as repo:
        await repo.insert_thread(
            thread_id=thread_id, user_id=user_id, title="Test Thread"
        )

    # Test thread retrieval
    async with sqlite_repo_factory() as repo:
        retrieved = await repo.get_thread(thread_id)
        assert retrieved is not None
        assert retrieved["thread_id"] == str(thread_id)
        assert retrieved["title"] == "Test Thread"
        assert retrieved["user_id"] == str(user_id)

    # Test message insertion
    async with sqlite_repo_factory() as repo:
        await repo.insert_message(
            thread_id=thread_id,
            user_id=user_id,
            role="user",
            content="Hello, SQLite!",
            meta={"test": "data"},
        )

    # Test message listing
    async with sqlite_repo_factory() as repo:
        messages = await repo.list_messages(thread_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello, SQLite!"
        assert messages[0]["metadata"] == {"test": "data"}
        assert messages[0]["role"] == "user"


@pytest.mark.asyncio
async def test_sqlite_repository_deduplication(sqlite_repo_factory):
    """Test message deduplication with client_msg_id."""
    thread_id = uuid4()
    user_id = uuid4()
    client_msg_id = "unique-client-123"

    # Create thread
    async with sqlite_repo_factory() as repo:
        await repo.insert_thread(
            thread_id=thread_id, user_id=user_id, title="Dedup Test"
        )

    # Insert message with client_msg_id
    async with sqlite_repo_factory() as repo:
        await repo.insert_message(
            thread_id=thread_id,
            user_id=user_id,
            role="user",
            content="First message",
            client_msg_id=client_msg_id,
        )

    # Try to insert duplicate - should be handled gracefully (no exception)
    async with sqlite_repo_factory() as repo:
        await repo.insert_message(
            thread_id=thread_id,
            user_id=user_id,
            role="user",
            content="Duplicate message",
            client_msg_id=client_msg_id,
        )

    # Verify only one message exists
    async with sqlite_repo_factory() as repo:
        messages = await repo.list_messages(thread_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "First message"


@pytest.mark.asyncio
async def test_sqlite_transaction_rollback(sqlite_repo_factory):
    """Test that transactions properly rollback on error."""
    thread_id = uuid4()
    user_id = uuid4()

    # Create thread successfully
    async with sqlite_repo_factory() as repo:
        await repo.insert_thread(
            thread_id=thread_id, user_id=user_id, title="Rollback Test"
        )

    # Try to insert message but simulate error
    try:
        async with sqlite_repo_factory() as repo:
            await repo.insert_message(
                thread_id=thread_id,
                user_id=user_id,
                role="user",
                content="This should rollback",
            )
            # Simulate an error after insert
            raise Exception("Simulated error")
    except Exception:
        pass  # Expected

    # Verify message was not persisted due to rollback
    async with sqlite_repo_factory() as repo:
        messages = await repo.list_messages(thread_id)
        assert len(messages) == 0  # No messages due to rollback
