from typing import Callable
from sqlalchemy.ext.asyncio import AsyncEngine

from ...domain.repositories.chat_repository import ChatRepository
from .pg_chat_repository import PgChatRepository


def create_chat_repository_factory(engine: AsyncEngine) -> Callable[[], ChatRepository]:
    """
    Create a repository factory function for dependency injection.
    
    This factory creates new repository instances for each UOW transaction,
    following the pattern specified in the issue.
    
    Usage:
        repo_factory = create_chat_repository_factory(engine)
        chat_service = UowChatService(repo_factory)
        
        # Service uses it like:
        async with repo_factory() as repo:
            await repo.insert_thread(...)
    """
    def factory() -> ChatRepository:
        return PgChatRepository(engine)
    
    return factory


class RepositoryContainer:
    """
    Dependency injection container for repository factories.
    
    Provides a centralized way to configure and access repository factories
    throughout the application.
    """
    
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        self._chat_repository_factory = create_chat_repository_factory(engine)
    
    @property
    def chat_repository_factory(self) -> Callable[[], ChatRepository]:
        """Get the chat repository factory."""
        return self._chat_repository_factory
    
    async def health_check(self) -> bool:
        """
        Perform a health check by testing database connectivity.
        
        Returns True if database is accessible, False otherwise.
        """
        try:
            async with self._chat_repository_factory() as repo:
                # Simple connectivity test - this would create a connection
                # and begin a transaction, then immediately close it
                pass
            return True
        except Exception:
            return False