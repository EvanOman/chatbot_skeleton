"""SQLite implementation of the ChatRepository interface for testing."""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from ...domain.repositories.chat_repository import ChatRepository


class SqliteChatRepository(ChatRepository):
    """SQLite implementation of ChatRepository for fast testing."""

    def __init__(self, engine: AsyncEngine) -> None:
        """Initialize repository with SQLite engine."""
        self.engine = engine
        self._conn = None
        self._trans = None

    async def __aenter__(self) -> "SqliteChatRepository":
        """Start a new database transaction."""
        self._conn = await self.engine.connect()
        self._trans = await self._conn.begin()
        
        # Create tables if they don't exist (for in-memory databases)
        await self._ensure_tables_exist()
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Commit or rollback the transaction."""
        if exc_type is None:
            await self._trans.commit()
        else:
            await self._trans.rollback()
        await self._conn.close()

    async def _ensure_tables_exist(self) -> None:
        """Create tables if they don't exist (for in-memory SQLite)."""
        # Create chat_thread table
        await self._conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_thread (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """))
        
        # Create chat_message table with client_msg_id for deduplication
        await self._conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_message (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                client_msg_id TEXT,
                metadata TEXT,
                FOREIGN KEY (thread_id) REFERENCES chat_thread(id),
                UNIQUE(client_msg_id)
            )
        """))
        
        # Create index for performance
        await self._conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_message_thread_id 
            ON chat_message(thread_id)
        """))

    async def insert_thread(
        self, *, thread_id: UUID, user_id: UUID, title: str
    ) -> None:
        """Insert a new chat thread."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            await self._conn.execute(
                text("""
                    INSERT INTO chat_thread (id, user_id, title, created_at, updated_at)
                    VALUES (:id, :user_id, :title, :created_at, :updated_at)
                """),
                {
                    "id": str(thread_id),
                    "user_id": str(user_id),
                    "title": title,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        except Exception as e:
            raise Exception(f"Failed to insert thread: {e}") from e

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
        """Insert a new chat message."""
        try:
            from uuid import uuid4
            
            metadata_json = json.dumps(meta) if meta else None
            message_id = uuid4()
            now = datetime.now(timezone.utc).isoformat()
            
            await self._conn.execute(
                text("""
                    INSERT INTO chat_message 
                    (id, thread_id, role, content, created_at, client_msg_id, metadata)
                    VALUES (:id, :thread_id, :role, :content, :created_at, :client_msg_id, :metadata)
                """),
                {
                    "id": str(message_id),
                    "thread_id": str(thread_id),
                    "role": role,
                    "content": content,
                    "created_at": now,
                    "client_msg_id": client_msg_id,
                    "metadata": metadata_json,
                }
            )
        except Exception as e:
            raise Exception(f"Failed to insert message: {e}") from e

    async def get_thread(self, thread_id: UUID) -> dict[str, Any] | None:
        """Get a chat thread by ID."""
        try:
            result = await self._conn.execute(
                text("""
                    SELECT id, user_id, title, created_at, updated_at
                    FROM chat_thread
                    WHERE id = :thread_id
                """),
                {"thread_id": str(thread_id)}
            )
            row = result.fetchone()
            
            if row is None:
                return None
            
            return {
                "thread_id": row[0],
                "user_id": row[1],
                "title": row[2],
                "created_at": row[3],
                "updated_at": row[4],
            }
        except Exception as e:
            raise Exception(f"Failed to get thread: {e}") from e

    async def list_messages(
        self, thread_id: UUID, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List messages in a thread, most recent first."""
        try:
            result = await self._conn.execute(
                text("""
                    SELECT id, thread_id, role, content, created_at, metadata
                    FROM chat_message
                    WHERE thread_id = :thread_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {
                    "thread_id": str(thread_id),
                    "limit": limit,
                }
            )
            
            messages = []
            for row in result:
                metadata = json.loads(row[5]) if row[5] else None
                messages.append({
                    "message_id": row[0],
                    "thread_id": row[1],
                    "role": row[2],
                    "content": row[3],
                    "created_at": row[4],
                    "metadata": metadata,
                })
            
            return messages
        except Exception as e:
            raise Exception(f"Failed to list messages: {e}") from e

