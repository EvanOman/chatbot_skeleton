from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import DatabaseConfig, Database
from ..database.repositories import SQLAlchemyChatThreadRepository, SQLAlchemyChatMessageRepository
from ...application.services.chat_service import ChatService
from ...application.services.echo_bot_service import EchoBotService


class Container(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()
    
    # Database
    database_config = providers.Singleton(
        DatabaseConfig.from_env
    )
    
    database = providers.Singleton(
        Database,
        config=database_config,
    )
    
    # Repositories
    thread_repository = providers.Factory(
        SQLAlchemyChatThreadRepository,
        session=providers.Dependency(instance_of=AsyncSession),
    )
    
    message_repository = providers.Factory(
        SQLAlchemyChatMessageRepository,
        session=providers.Dependency(instance_of=AsyncSession),
    )
    
    # Services
    bot_service = providers.Singleton(
        EchoBotService,
    )
    
    chat_service = providers.Factory(
        ChatService,
        thread_repository=thread_repository,
        message_repository=message_repository,
        bot_service=bot_service,
    )