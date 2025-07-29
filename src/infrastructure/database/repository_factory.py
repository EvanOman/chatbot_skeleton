import os
from enum import Enum
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ...domain.repositories.chat_repository import BaseChatRepository
from .pg_chat_repository import PgChatRepository
from .sqlite_chat_repository import SqliteChatRepository


class DatabaseType(Enum):
    """Supported database types for repositories."""
    
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"

    @classmethod
    def from_environment(cls) -> "DatabaseType":
        """
        Determine database type from environment variables.
        
        Returns SQLITE for testing environments, POSTGRESQL for production.
        """
        if os.getenv("TESTING", "false").lower() == "true":
            return cls.SQLITE
        return cls.POSTGRESQL


def create_chat_repository_factory(
    engine: AsyncEngine, db_type: DatabaseType = DatabaseType.POSTGRESQL
) -> Callable[[], BaseChatRepository]:
    """
    Create a repository factory function for dependency injection.

    This factory creates new repository instances for each UOW transaction,
    following the pattern specified in the issue.

    Args:
        engine: The SQLAlchemy async engine
        db_type: The database type to use (PostgreSQL or SQLite)

    Usage:
        # For production (PostgreSQL)
        repo_factory = create_chat_repository_factory(engine)
        
        # For testing (SQLite)
        repo_factory = create_chat_repository_factory(
            engine, DatabaseType.SQLITE
        )
        
        chat_service = UowChatService(repo_factory)

        # Service uses it like:
        async with repo_factory() as repo:
            await repo.insert_thread(...)
    """

    def factory() -> BaseChatRepository:
        if db_type == DatabaseType.SQLITE:
            return SqliteChatRepository(engine)
        else:
            return PgChatRepository(engine)

    return factory


def create_test_sqlite_engine() -> AsyncEngine:
    """
    Create an in-memory SQLite engine optimized for testing.
    
    Returns:
        AsyncEngine configured for in-memory SQLite with fast settings
    """
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )


class RepositoryContainer:
    """
    Dependency injection container for repository factories.

    Provides a centralized way to configure and access repository factories
    throughout the application. Automatically selects the appropriate database
    type based on environment configuration.
    
    Usage:
        # For production (automatically uses PostgreSQL)
        container = RepositoryContainer(pg_engine)
        
        # For testing (automatically uses SQLite if TESTING=true)
        container = RepositoryContainer(test_engine, DatabaseType.SQLITE)
        
        # Access repository factory
        repo_factory = container.chat_repository_factory
        async with repo_factory() as repo:
            await repo.insert_thread(...)
    """

    def __init__(
        self, 
        engine: AsyncEngine, 
        db_type: DatabaseType | None = None
    ) -> None:
        """
        Initialize repository container.
        
        Args:
            engine: Database engine to use
            db_type: Database type override. If None, determined from environment.
        """
        self.engine = engine
        self.db_type = db_type or DatabaseType.from_environment()
        self._chat_repository_factory = create_chat_repository_factory(engine, self.db_type)

    @property
    def chat_repository_factory(self) -> Callable[[], BaseChatRepository]:
        """Get the chat repository factory."""
        return self._chat_repository_factory

    async def health_check(self) -> bool:
        """
        Perform a health check by testing database connectivity.

        Returns True if database is accessible, False otherwise.
        """
        try:
            async with self._chat_repository_factory():
                # Simple connectivity test - this would create a connection
                # and begin a transaction, then immediately close it
                pass
            return True
        except Exception:
            return False
