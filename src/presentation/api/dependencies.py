from collections.abc import AsyncGenerator
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ...application.services.uow_chat_service import UowChatService
from ...domain.repositories.chat_repository import BaseChatRepository
from ...infrastructure.container.container import Container
from ...infrastructure.di import get_application_container


async def get_database_session() -> AsyncGenerator[AsyncSession]:
    """Get database session for legacy SQLAlchemy ORM-based services."""
    database = Container.database()
    async for session in database.get_session():
        yield session


async def get_chat_repository_factory() -> Callable[[], BaseChatRepository]:
    """
    Get chat repository factory for Unit-of-Work pattern.
    
    Returns a factory function that creates repository instances configured
    for the current environment (PostgreSQL for production, SQLite for testing).
    """
    container = get_application_container()
    return await container.get_chat_repository_factory()


async def get_chat_service() -> UowChatService:
    """
    Get the chat service configured with the appropriate repository.
    
    The service automatically uses the correct database backend based on
    the environment (PostgreSQL for production, SQLite for testing).
    """
    container = get_application_container()
    return await container.get_chat_service()
