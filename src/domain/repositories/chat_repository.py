from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class BaseChatRepository(ABC):
    """
    Base Repository interface implementing the Unit-of-Work pattern.
    
    This serves as the foundation for all chat repository implementations,
    providing primitive CRUD operations and transaction management through
    async context managers.

    Design Principles:
    - All operations within an async context manager are atomic
    - Transactions are lightweight (<100ms) and minimize lock time
    - Implementations must handle both PostgreSQL and SQLite backends
    - Supports message deduplication via client_msg_id
    
    Usage:
        async with repo_factory() as repo:
            await repo.insert_thread(...)
            await repo.insert_message(...)
        # __aexit__ commits; any exception triggers rollback automatically
    """

    # ---------- Thread Operations ----------
    @abstractmethod
    async def insert_thread(
        self, *, thread_id: UUID, user_id: UUID, title: str
    ) -> None:
        """
        Insert a new thread. Does not commit - handled by context manager.
        
        Args:
            thread_id: Unique identifier for the thread
            user_id: ID of the user who owns the thread
            title: Display title for the thread
        
        Raises:
            Exception: If thread_id already exists or database error occurs
        """
        pass

    @abstractmethod
    async def get_thread(self, thread_id: UUID) -> dict[str, Any] | None:
        """
        Get thread by ID. Returns dict with thread data or None if not found.
        
        Args:
            thread_id: UUID of the thread to retrieve
            
        Returns:
            Dictionary containing thread data fields or None if not found.
            Expected fields: thread_id, user_id, title, status, created_at, updated_at
        """
        pass

    # ---------- Message Operations ----------
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
        """
        Insert a new message with deduplication support.
        
        Args:
            thread_id: UUID of the thread this message belongs to
            user_id: ID of the user who sent the message
            role: Message role (user, assistant, system)
            content: The message content
            meta: Optional metadata dictionary
            client_msg_id: Optional client-side message ID for deduplication
            
        Note:
            If client_msg_id is provided and a message with that ID already exists,
            implementations should handle this gracefully (PostgreSQL logs and continues,
            SQLite may raise constraint error depending on implementation).
        """
        pass

    @abstractmethod
    async def list_messages(
        self, thread_id: UUID, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        List messages for a thread, most recent first, up to limit.
        
        Args:
            thread_id: UUID of the thread to get messages for
            limit: Maximum number of messages to return (default 50)
            
        Returns:
            List of message dictionaries ordered by created_at DESC.
            Expected fields: message_id, thread_id, user_id, role, content, 
                           created_at, metadata, type
        """
        pass

    # ---------- Transaction Management ----------
    @abstractmethod
    async def __aenter__(self) -> "BaseChatRepository":
        """
        Async context manager entry - opens connection and begins transaction.
        
        Returns:
            Self for use in the async with statement
            
        Note:
            Implementations must establish database connection and begin transaction
        """
        pass

    @abstractmethod
    async def __aexit__(
        self, exc_type: type | None, exc: Exception | None, tb: Any
    ) -> None:
        """
        Async context manager exit - commit on success, rollback on exception.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc: Exception instance if an exception occurred  
            tb: Traceback if an exception occurred
            
        Note:
            Must commit transaction if exc_type is None, rollback otherwise.
            Must always clean up connection resources.
        """
        pass


# Maintain backward compatibility
ChatRepository = BaseChatRepository
