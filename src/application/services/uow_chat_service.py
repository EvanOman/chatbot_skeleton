import logging
from typing import Awaitable, Callable
from uuid import UUID, uuid4

from ...domain.repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)

# System user ID for AI responses
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


class UowChatService:
    """
    Chat service implementing Unit-of-Work pattern.

    Key principles:
    - Fast database operations (<100ms) happen inside 'async with repo' blocks
    - Slow operations (LLM calls, external I/O) happen outside transactions
    - Multiple short transactions instead of one long transaction
    - Each service method can be retried independently
    """

    def __init__(self, repo_factory: Callable[[], ChatRepository]) -> None:
        self.repo_factory = repo_factory

    async def create_thread_with_first_msg(
        self,
        *,
        thread_id: UUID,
        user_id: UUID,
        title: str,
        first_msg: str,
        llm_generate_fn: Callable[[str], Awaitable[str]],
    ) -> dict:
        """
        Create a new thread with first message, then generate AI response.

        Uses two separate transactions:
        1. Fast: Create thread + user message
        2. Fast: Store AI response (after slow LLM call)
        """

        # Transaction 1: Create thread and first message (fast, <100ms)
        async with self.repo_factory() as repo:
            await repo.insert_thread(thread_id=thread_id, user_id=user_id, title=title)
            await repo.insert_message(
                thread_id=thread_id, user_id=user_id, role="user", content=first_msg
            )

        logger.info(f"Thread {thread_id} created with first message")

        # Slow operation outside transaction: Generate AI response
        try:
            ai_reply = await llm_generate_fn(first_msg)
        except Exception as e:
            logger.error(f"LLM generation failed for thread {thread_id}: {e}")
            # Thread and user message are already committed
            # Could add a "pending_reply" status if needed
            raise

        # Transaction 2: Store AI response (fast, <100ms)
        await self._store_ai_reply(thread_id, ai_reply)

        return {
            "thread_id": thread_id,
            "status": "completed",
            "user_message": first_msg,
            "ai_reply": ai_reply,
        }

    async def add_message_and_reply(
        self,
        *,
        thread_id: UUID,
        user_id: UUID,
        message_content: str,
        llm_generate_fn: Callable[[str, list[dict]], Awaitable[str]],
    ) -> dict:
        """
        Add user message to existing thread and generate AI reply.

        Uses separate transactions for user message and AI response.
        """

        # Transaction 1: Store user message (fast, <100ms)
        async with self.repo_factory() as repo:
            # Verify thread exists
            thread = await repo.get_thread(thread_id)
            if not thread:
                raise ValueError(f"Thread {thread_id} not found")

            await repo.insert_message(
                thread_id=thread_id,
                user_id=user_id,
                role="user",
                content=message_content,
            )

        logger.info(f"User message added to thread {thread_id}")

        # Get conversation history for context (separate read transaction)
        async with self.repo_factory() as repo:
            messages = await repo.list_messages(thread_id, limit=10)

        # Slow operation outside transaction: Generate AI response
        try:
            ai_reply = await llm_generate_fn(message_content, messages)
        except Exception as e:
            logger.error(f"LLM generation failed for thread {thread_id}: {e}")
            raise

        # Transaction 2: Store AI response (fast, <100ms)
        await self._store_ai_reply(thread_id, ai_reply)

        return {
            "thread_id": thread_id,
            "status": "completed",
            "user_message": message_content,
            "ai_reply": ai_reply,
        }

    async def get_thread_info(self, thread_id: UUID) -> dict | None:
        """Get thread information (read-only, single transaction)."""
        async with self.repo_factory() as repo:
            return await repo.get_thread(thread_id)

    async def get_thread_messages(self, thread_id: UUID, limit: int = 50) -> list[dict]:
        """Get thread messages (read-only, single transaction)."""
        async with self.repo_factory() as repo:
            return await repo.list_messages(thread_id, limit)

    async def _store_ai_reply(self, thread_id: UUID, ai_reply: str) -> None:
        """
        Internal method to store AI reply in a separate transaction.

        This is kept private and reused by public methods to maintain
        the pattern of short, focused transactions.
        """
        async with self.repo_factory() as repo:
            await repo.insert_message(
                thread_id=thread_id,
                user_id=SYSTEM_USER_ID,
                role="assistant",
                content=ai_reply,
            )

        logger.info(f"AI reply stored for thread {thread_id}")

    # Helper methods for common patterns

    async def create_empty_thread(
        self, *, thread_id: UUID, user_id: UUID, title: str
    ) -> dict:
        """Create an empty thread (single fast transaction)."""
        async with self.repo_factory() as repo:
            await repo.insert_thread(thread_id=thread_id, user_id=user_id, title=title)

        return {
            "thread_id": thread_id,
            "user_id": user_id,
            "title": title,
            "status": "created",
        }

    async def add_user_message(
        self,
        *,
        thread_id: UUID,
        user_id: UUID,
        content: str,
        client_msg_id: str | None = None,
    ) -> None:
        """Add a user message (single fast transaction with deduplication)."""
        async with self.repo_factory() as repo:
            await repo.insert_message(
                thread_id=thread_id,
                user_id=user_id,
                role="user",
                content=content,
                client_msg_id=client_msg_id,
            )
