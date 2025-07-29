import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine
from sqlalchemy.sql import func

from ...domain.repositories.chat_repository import ChatRepository
from .models import ChatMessageModel, ChatThreadModel

logger = logging.getLogger(__name__)


class PgChatRepository(ChatRepository):
    """
    PostgreSQL implementation of ChatRepository using async SQLAlchemy Core.
    
    Implements Unit-of-Work pattern with context manager for transaction boundaries.
    All operations inside 'async with' block are atomic and fast (<100ms).
    """
    
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        self._connection: AsyncConnection | None = None
        self._transaction = None

    async def __aenter__(self) -> "PgChatRepository":
        """Async context manager entry - opens connection and begins transaction"""
        self._connection = await self.engine.connect()
        self._transaction = await self._connection.begin()
        logger.debug("Transaction started")
        return self
    
    async def __aexit__(self, exc_type: type | None, exc: Exception | None, tb: Any) -> None:
        """Async context manager exit - commit on success, rollback on exception"""
        try:
            if exc_type is None:
                # No exception, commit the transaction
                if self._transaction:
                    await self._transaction.commit()
                logger.debug("Transaction committed successfully")
            else:
                # Exception occurred, rollback the transaction
                if self._transaction:
                    await self._transaction.rollback()
                logger.warning(f"Transaction rolled back due to {exc_type.__name__}: {exc}")
        finally:
            # Always close the connection
            if self._connection:
                await self._connection.close()
            self._connection = None
            self._transaction = None

    async def insert_thread(self, *, thread_id: UUID, user_id: UUID, title: str) -> None:
        """Insert a new thread. Must be called within async context manager."""
        if not self._connection:
            raise RuntimeError("Repository must be used within async context manager")
        
        # Use SQLAlchemy Core for raw SQL performance
        stmt = insert(ChatThreadModel).values(
            thread_id=thread_id,
            user_id=user_id,
            title=title,
            status="active",
            created_at=func.now(),
            updated_at=func.now()
        )
        
        await self._connection.execute(stmt)

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
        """Insert a new message with deduplication support. Must be called within async context manager."""
        if not self._connection:
            raise RuntimeError("Repository must be used within async context manager")
        
        # Generate message ID
        message_id = uuid4()
        
        # Use SQLAlchemy Core for raw SQL performance
        stmt = insert(ChatMessageModel).values(
            message_id=message_id,
            thread_id=thread_id,
            user_id=user_id,
            role=role,
            content=content,
            type="text",
            metadata_json=meta,
            client_msg_id=client_msg_id,
            created_at=func.now()
        )
        
        try:
            await self._connection.execute(stmt)
        except Exception as e:
            # Handle unique constraint violation for client_msg_id deduplication
            error_msg = str(e).lower()
            if client_msg_id and ("unique" in error_msg or "duplicate" in error_msg):
                logger.info(f"Message with client_msg_id {client_msg_id} already exists, skipping insert")
                # This is expected behavior for deduplication - not an error
                return
            else:
                # Re-raise other database errors
                logger.error(f"Database error inserting message: {e}")
                raise

    async def get_thread(self, thread_id: UUID) -> dict[str, Any] | None:
        """Get thread by ID. Returns dict with thread data or None if not found."""
        if not self._connection:
            raise RuntimeError("Repository must be used within async context manager")
        
        stmt = select(ChatThreadModel).where(ChatThreadModel.thread_id == thread_id)
        result = await self._connection.execute(stmt)
        row = result.fetchone()
        
        if row is None:
            return None
        
        # Convert SQLAlchemy row to dict
        return {
            "thread_id": row.thread_id,
            "user_id": row.user_id,
            "title": row.title,
            "status": row.status,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "summary": row.summary,
            "metadata": row.metadata_json,
        }

    async def list_messages(self, thread_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
        """List messages for a thread, most recent first, up to limit."""
        if not self._connection:
            raise RuntimeError("Repository must be used within async context manager")
        
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.thread_id == thread_id)
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
        )
        
        result = await self._connection.execute(stmt)
        rows = result.fetchall()
        
        # Convert SQLAlchemy rows to dicts
        return [
            {
                "message_id": row.message_id,
                "thread_id": row.thread_id,
                "user_id": row.user_id,
                "role": row.role,
                "content": row.content,
                "type": row.type,
                "metadata": row.metadata_json,
                "created_at": row.created_at,
            }
            for row in rows
        ]