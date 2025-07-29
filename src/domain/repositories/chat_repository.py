from abc import ABC, abstractmethod
from uuid import UUID
from typing import Any


class ChatRepository(ABC):
    """
    Thin Repository implementing the Unit-of-Work pattern.
    Provides primitive CRUD operations and transaction management.
    
    Usage:
        async with repo_factory() as repo:
            await repo.insert_thread(...)
            await repo.insert_message(...)
        # __aexit__ commits; any exception triggers rollback automatically
    """
    
    # ---------- primitive CRUD ----------
    @abstractmethod
    async def insert_thread(self, *, thread_id: UUID, user_id: UUID, title: str) -> None:
        """Insert a new thread. Does not commit - handled by context manager."""
        pass

    @abstractmethod
    async def insert_message(
        self,
        *,
        thread_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
        meta: dict[str, Any] | None = None,
        client_msg_id: str | None = None,
    ) -> None:
        """Insert a new message. Does not commit - handled by context manager."""
        pass

    @abstractmethod
    async def get_thread(self, thread_id: UUID) -> dict[str, Any] | None:
        """Get thread by ID. Returns dict with thread data or None if not found."""
        pass

    @abstractmethod
    async def list_messages(self, thread_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
        """List messages for a thread, most recent first, up to limit."""
        pass

    # ---------- tx boundaries ----------
    @abstractmethod
    async def __aenter__(self) -> "ChatRepository":
        """Opens DB session & begins transaction"""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type: type | None, exc: Exception | None, tb: Any) -> None:
        """Commit on success, rollback on exception"""
        pass