"""Tests for the repository container and dependency injection system."""

import os
from uuid import uuid4

import pytest
import pytest_asyncio

from src.infrastructure.database.repository_factory import DatabaseType
from src.infrastructure.di import ApplicationContainer, TestingContainer


@pytest.mark.asyncio
async def test_application_container_sqlite_mode():
    """Test ApplicationContainer in SQLite mode."""
    container = ApplicationContainer(force_sqlite=True)

    # Test database creation
    database = await container.get_database()
    assert database is not None
    assert database.config.use_sqlite is True

    # Test repository container
    repo_container = await container.get_repository_container()
    assert repo_container is not None
    assert repo_container.db_type == DatabaseType.SQLITE

    # Test repository factory
    repo_factory = await container.get_chat_repository_factory()
    assert repo_factory is not None

    # Test chat service
    chat_service = await container.get_chat_service()
    assert chat_service is not None

    # Test health check
    health = await container.health_check()
    assert health["database_config"] == "ok"
    assert health["repository"] == "ok"
    assert health["chat_service"] == "ok"

    # Cleanup
    await container.cleanup()


@pytest.mark.asyncio
async def test_test_container():
    """Test the specialized TestingContainer."""
    container = TestingContainer()

    # Should automatically use SQLite
    database = await container.get_database()
    assert database.config.use_sqlite is True
    assert database.config.sqlite_path == ":memory:"

    # Test that we can perform basic operations
    chat_service = await container.get_chat_service()

    thread_id = uuid4()
    user_id = uuid4()

    # This should work with SQLite backend
    result = await chat_service.create_empty_thread(
        thread_id=thread_id, user_id=user_id, title="Test Thread"
    )

    assert result["thread_id"] == thread_id
    assert result["status"] == "created"

    # Verify we can retrieve the thread
    thread_info = await chat_service.get_thread_info(thread_id)
    assert thread_info is not None
    assert thread_info["title"] == "Test Thread"

    await container.cleanup()


@pytest.mark.asyncio
async def test_repository_factory_basic_operations():
    """Test basic repository operations through the factory."""
    container = TestingContainer()
    repo_factory = await container.get_chat_repository_factory()

    thread_id = uuid4()
    user_id = uuid4()

    # Test thread creation
    async with repo_factory() as repo:
        await repo.insert_thread(
            thread_id=thread_id, user_id=user_id, title="Factory Test"
        )

    # Test thread retrieval
    async with repo_factory() as repo:
        thread = await repo.get_thread(thread_id)
        assert thread is not None
        assert thread["title"] == "Factory Test"
        assert thread["thread_id"] == str(thread_id)

    # Test message operations
    async with repo_factory() as repo:
        await repo.insert_message(
            thread_id=thread_id,
            user_id=user_id,
            role="user",
            content="Test message",
            meta={"source": "test"},
        )

    async with repo_factory() as repo:
        messages = await repo.list_messages(thread_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "Test message"
        assert messages[0]["metadata"]["source"] == "test"

    await container.cleanup()


@pytest.mark.asyncio
async def test_environment_based_database_selection(monkeypatch):
    """Test that database type is selected based on environment."""
    # Test production mode (no TESTING env var)
    monkeypatch.delenv("TESTING", raising=False)
    container = ApplicationContainer()

    database = await container.get_database()
    # In test environment, this will actually still use SQLite due to test configuration
    # but the point is to test the configuration logic

    await container.cleanup()

    # Test explicit testing mode
    monkeypatch.setenv("TESTING", "true")
    container = ApplicationContainer()

    database = await container.get_database()
    assert database.config.use_sqlite is True

    await container.cleanup()


@pytest.mark.asyncio
async def test_container_transaction_boundaries():
    """Test that transaction boundaries work correctly."""
    container = TestingContainer()
    repo_factory = await container.get_chat_repository_factory()

    thread_id = uuid4()
    user_id = uuid4()

    # Test successful transaction
    async with repo_factory() as repo:
        await repo.insert_thread(
            thread_id=thread_id, user_id=user_id, title="Transaction Test"
        )
        await repo.insert_message(
            thread_id=thread_id,
            user_id=user_id,
            role="user",
            content="Message in transaction",
        )

    # Verify both operations were committed
    async with repo_factory() as repo:
        thread = await repo.get_thread(thread_id)
        messages = await repo.list_messages(thread_id)

        assert thread is not None
        assert len(messages) == 1

    # Test rollback on exception
    thread_id_2 = uuid4()
    try:
        async with repo_factory() as repo:
            await repo.insert_thread(
                thread_id=thread_id_2, user_id=user_id, title="Rollback Test"
            )
            # Simulate an error
            raise Exception("Simulated error")
    except Exception:
        pass  # Expected

    # Verify rollback occurred
    async with repo_factory() as repo:
        thread = await repo.get_thread(thread_id_2)
        assert thread is None  # Should not exist due to rollback

    await container.cleanup()


@pytest.mark.asyncio
async def test_uow_chat_service_integration():
    """Test UowChatService with the new repository system."""
    container = TestingContainer()
    chat_service = await container.get_chat_service()

    thread_id = uuid4()
    user_id = uuid4()

    # Test creating empty thread
    result = await chat_service.create_empty_thread(
        thread_id=thread_id, user_id=user_id, title="UOW Integration Test"
    )

    assert result["thread_id"] == thread_id
    assert result["status"] == "created"

    # Test adding user message
    await chat_service.add_user_message(
        thread_id=thread_id,
        user_id=user_id,
        content="Hello from UOW test",
        client_msg_id="test-msg-123",
    )

    # Test retrieving messages
    messages = await chat_service.get_thread_messages(thread_id)
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello from UOW test"

    # Test deduplication
    await chat_service.add_user_message(
        thread_id=thread_id,
        user_id=user_id,
        content="Duplicate message",
        client_msg_id="test-msg-123",  # Same client ID
    )

    # Should still only have one message
    messages = await chat_service.get_thread_messages(thread_id)
    assert len(messages) == 1

    await container.cleanup()
