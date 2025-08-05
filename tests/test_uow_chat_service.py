from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from src.application.services.uow_chat_service import SYSTEM_USER_ID, UowChatService
from src.domain.repositories.chat_repository import ChatRepository


class MockChatRepository(ChatRepository):
    """In-memory mock repository for testing the UOW pattern."""

    def __init__(self):
        self.threads = {}
        self.messages = []
        self.in_transaction = False
        self.should_fail = False
        self.commit_called = False
        self.rollback_called = False

    async def __aenter__(self):
        self.in_transaction = True
        self.commit_called = False
        self.rollback_called = False
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.in_transaction = False
        if exc_type is None:
            self.commit_called = True
        else:
            self.rollback_called = True
            # In real implementation, this would rollback the transaction
            # For testing, we just track that rollback was called

    async def insert_thread(
        self, *, thread_id: UUID, user_id: UUID, title: str
    ) -> None:
        if not self.in_transaction:
            raise RuntimeError("Must be in transaction")
        if self.should_fail:
            raise Exception("Simulated database error")

        self.threads[thread_id] = {
            "thread_id": thread_id,
            "user_id": user_id,
            "title": title,
            "status": "active",
        }

    async def insert_message(
        self,
        *,
        thread_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
        meta=None,
        client_msg_id=None,
    ) -> None:
        if not self.in_transaction:
            raise RuntimeError("Must be in transaction")
        if self.should_fail:
            raise Exception("Simulated database error")

        # Simple deduplication check
        if client_msg_id:
            existing = [
                m for m in self.messages if m.get("client_msg_id") == client_msg_id
            ]
            if existing:
                return  # Skip duplicate

        self.messages.append(
            {
                "message_id": uuid4(),
                "thread_id": thread_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "meta": meta,
                "client_msg_id": client_msg_id,
            }
        )

    async def get_thread(self, thread_id: UUID) -> dict | None:
        if not self.in_transaction:
            raise RuntimeError("Must be in transaction")
        return self.threads.get(thread_id)

    async def list_messages(self, thread_id: UUID, limit: int = 50) -> list[dict]:
        if not self.in_transaction:
            raise RuntimeError("Must be in transaction")
        thread_messages = [m for m in self.messages if m["thread_id"] == thread_id]
        return thread_messages[-limit:]  # Most recent first (simplified)


@pytest.fixture
def mock_repo():
    return MockChatRepository()


@pytest.fixture
def repo_factory(mock_repo):
    return lambda: mock_repo


@pytest.fixture
def chat_service(repo_factory):
    return UowChatService(repo_factory)


@pytest.fixture
def mock_llm_generate():
    async def _generate(message: str, context=None):
        return f"AI response to: {message}"

    return _generate


class TestUowChatService:
    """Test the Unit-of-Work pattern implementation."""

    @pytest.mark.asyncio
    async def test_create_thread_with_first_msg_happy_path(
        self, chat_service, mock_repo, mock_llm_generate
    ):
        """Test successful thread creation with first message and AI reply."""
        thread_id = uuid4()
        user_id = uuid4()
        title = "Test Thread"
        first_msg = "Hello, world!"

        result = await chat_service.create_thread_with_first_msg(
            thread_id=thread_id,
            user_id=user_id,
            title=title,
            first_msg=first_msg,
            llm_generate_fn=mock_llm_generate,
        )

        # Verify result
        assert result["thread_id"] == thread_id
        assert result["status"] == "completed"
        assert result["user_message"] == first_msg
        assert result["ai_reply"] == "AI response to: Hello, world!"

        # Verify database state
        assert thread_id in mock_repo.threads
        assert len(mock_repo.messages) == 2  # User message + AI reply

        # Verify user message
        user_msg = mock_repo.messages[0]
        assert user_msg["thread_id"] == thread_id
        assert user_msg["user_id"] == user_id
        assert user_msg["role"] == "user"
        assert user_msg["content"] == first_msg

        # Verify AI message
        ai_msg = mock_repo.messages[1]
        assert ai_msg["thread_id"] == thread_id
        assert ai_msg["user_id"] == SYSTEM_USER_ID
        assert ai_msg["role"] == "assistant"
        assert ai_msg["content"] == "AI response to: Hello, world!"

        # Verify transactions were committed (called multiple times)
        assert mock_repo.commit_called

    @pytest.mark.asyncio
    async def test_create_thread_llm_failure_leaves_consistent_state(
        self, chat_service, mock_repo
    ):
        """Test that LLM failure after thread creation leaves data in consistent state."""
        thread_id = uuid4()
        user_id = uuid4()
        title = "Test Thread"
        first_msg = "Hello, world!"

        # Mock LLM function that always fails
        async def failing_llm_generate(message: str):
            raise Exception("LLM service unavailable")

        # Should raise exception
        with pytest.raises(Exception, match="LLM service unavailable"):
            await chat_service.create_thread_with_first_msg(
                thread_id=thread_id,
                user_id=user_id,
                title=title,
                first_msg=first_msg,
                llm_generate_fn=failing_llm_generate,
            )

        # Thread and user message should still exist (first transaction committed)
        assert thread_id in mock_repo.threads
        assert len(mock_repo.messages) == 1  # Only user message, no AI reply

        user_msg = mock_repo.messages[0]
        assert user_msg["content"] == first_msg
        assert user_msg["role"] == "user"

    @pytest.mark.asyncio
    async def test_database_failure_triggers_rollback(self, chat_service, mock_repo):
        """Test that database failures trigger transaction rollback."""
        thread_id = uuid4()
        user_id = uuid4()
        title = "Test Thread"
        first_msg = "Hello, world!"

        # Configure mock to fail on database operations
        mock_repo.should_fail = True

        async def mock_llm_generate(message: str):
            return "AI response"

        # Should raise database exception
        with pytest.raises(Exception, match="Simulated database error"):
            await chat_service.create_thread_with_first_msg(
                thread_id=thread_id,
                user_id=user_id,
                title=title,
                first_msg=first_msg,
                llm_generate_fn=mock_llm_generate,
            )

        # Verify rollback was called
        assert mock_repo.rollback_called

        # Database should be empty (rollback prevented commits)
        assert len(mock_repo.threads) == 0
        assert len(mock_repo.messages) == 0

    @pytest.mark.asyncio
    async def test_add_message_and_reply(
        self, chat_service, mock_repo, mock_llm_generate
    ):
        """Test adding message to existing thread and getting AI reply."""
        thread_id = uuid4()
        user_id = uuid4()

        # Pre-populate thread
        mock_repo.threads[thread_id] = {
            "thread_id": thread_id,
            "user_id": user_id,
            "title": "Existing Thread",
        }

        message_content = "What's the weather like?"

        # Mock LLM function that uses context
        async def context_aware_llm(message: str, context: list):
            return f"AI response to '{message}' (context: {len(context)} messages)"

        result = await chat_service.add_message_and_reply(
            thread_id=thread_id,
            user_id=user_id,
            message_content=message_content,
            llm_generate_fn=context_aware_llm,
        )

        # Verify result
        assert result["thread_id"] == thread_id
        assert result["status"] == "completed"
        assert result["user_message"] == message_content
        assert "AI response to 'What's the weather like?'" in result["ai_reply"]

        # Verify two messages were added
        assert len(mock_repo.messages) == 2

        user_msg = mock_repo.messages[0]
        assert user_msg["role"] == "user"
        assert user_msg["content"] == message_content

        ai_msg = mock_repo.messages[1]
        assert ai_msg["role"] == "assistant"
        assert ai_msg["user_id"] == SYSTEM_USER_ID

    @pytest.mark.asyncio
    async def test_thread_not_found_error(self, chat_service, mock_repo):
        """Test error handling when thread doesn't exist."""
        non_existent_thread_id = uuid4()
        user_id = uuid4()

        async def mock_llm_generate(message: str, context: list):
            return "AI response"

        with pytest.raises(ValueError, match="Thread .* not found"):
            await chat_service.add_message_and_reply(
                thread_id=non_existent_thread_id,
                user_id=user_id,
                message_content="Hello",
                llm_generate_fn=mock_llm_generate,
            )

    @pytest.mark.asyncio
    async def test_deduplication_with_client_msg_id(self, chat_service, mock_repo):
        """Test message deduplication using client_msg_id."""
        thread_id = uuid4()
        user_id = uuid4()
        client_msg_id = "unique-client-123"

        # Create thread first
        await chat_service.create_empty_thread(
            thread_id=thread_id, user_id=user_id, title="Test Thread"
        )

        # Add same message twice with same client_msg_id
        await chat_service.add_user_message(
            thread_id=thread_id,
            user_id=user_id,
            content="Test message",
            client_msg_id=client_msg_id,
        )

        # Second call should be deduplicated
        await chat_service.add_user_message(
            thread_id=thread_id,
            user_id=user_id,
            content="Test message",
            client_msg_id=client_msg_id,
        )

        # Should only have one message (deduplication worked)
        assert len(mock_repo.messages) == 1
        assert mock_repo.messages[0]["client_msg_id"] == client_msg_id

    @pytest.mark.asyncio
    async def test_read_operations(self, chat_service, mock_repo):
        """Test read-only operations."""
        thread_id = uuid4()
        user_id = uuid4()

        # Setup test data
        mock_repo.threads[thread_id] = {
            "thread_id": thread_id,
            "user_id": user_id,
            "title": "Test Thread",
        }
        mock_repo.messages.append(
            {
                "message_id": uuid4(),
                "thread_id": thread_id,
                "user_id": user_id,
                "role": "user",
                "content": "Hello",
            }
        )

        # Test get_thread_info
        thread_info = await chat_service.get_thread_info(thread_id)
        assert thread_info["thread_id"] == thread_id
        assert thread_info["title"] == "Test Thread"

        # Test get_thread_messages
        messages = await chat_service.get_thread_messages(thread_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello"

        # Test non-existent thread
        non_existent_info = await chat_service.get_thread_info(uuid4())
        assert non_existent_info is None
