"""
Comprehensive dependency injection container for the chat application.

This module provides a centralized way to configure and manage all dependencies,
including repositories, services, and database connections. It automatically
configures the appropriate database backend (PostgreSQL for production, 
SQLite for testing) based on environment variables.
"""

import os
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncEngine

from ...application.services.uow_chat_service import UowChatService
from ...domain.repositories.chat_repository import BaseChatRepository
from ..config.database import Database, DatabaseConfig
from ..database.repository_factory import (
    DatabaseType,
    RepositoryContainer,
    create_chat_repository_factory,
    create_test_sqlite_engine,
)


class ApplicationContainer:
    """
    Main dependency injection container for the chat application.
    
    This container manages the lifecycle of all major components and ensures
    proper configuration based on the environment (production vs testing).
    
    Design Principles:
    - Single source of truth for all dependencies
    - Environment-aware configuration (SQLite for tests, PostgreSQL for prod)
    - Lazy initialization of expensive resources
    - Clear separation of concerns between layers
    
    Usage:
        # Production usage
        container = ApplicationContainer()
        chat_service = await container.get_chat_service()
        
        # Testing usage
        container = ApplicationContainer(force_sqlite=True)
        chat_service = await container.get_chat_service()
    """

    def __init__(self, force_sqlite: bool = False):
        """
        Initialize the application container.
        
        Args:
            force_sqlite: If True, forces SQLite usage regardless of environment.
                         Useful for testing scenarios.
        """
        self._force_sqlite = force_sqlite
        self._database: Database | None = None
        self._repository_container: RepositoryContainer | None = None
        self._chat_service: UowChatService | None = None

    async def get_database(self) -> Database:
        """Get or create the database instance."""
        if self._database is None:
            config = DatabaseConfig.from_env()
            
            # Override for testing if requested
            if self._force_sqlite:
                config.use_sqlite = True
                config.sqlite_path = ":memory:"
                
            self._database = Database(config)
        
        return self._database

    async def get_repository_container(self) -> RepositoryContainer:
        """Get or create the repository container."""
        if self._repository_container is None:
            database = await self.get_database()
            
            # Determine database type
            db_type = DatabaseType.SQLITE if self._force_sqlite else DatabaseType.from_environment()
            
            self._repository_container = RepositoryContainer(
                engine=database.engine,
                db_type=db_type
            )
        
        return self._repository_container

    async def get_chat_repository_factory(self) -> Callable[[], BaseChatRepository]:
        """Get the chat repository factory."""
        container = await self.get_repository_container()
        return container.chat_repository_factory

    async def get_chat_service(self) -> UowChatService:
        """Get or create the chat service."""
        if self._chat_service is None:
            repo_factory = await self.get_chat_repository_factory()
            self._chat_service = UowChatService(repo_factory)
        
        return self._chat_service

    async def health_check(self) -> dict:
        """
        Perform a comprehensive health check of all components.
        
        Returns:
            Dictionary with health status of each component
        """
        results = {}
        
        try:
            await self.get_database()
            results["database_config"] = "ok"
        except Exception as e:
            results["database_config"] = f"error: {e}"

        try:
            repo_container = await self.get_repository_container()
            repo_healthy = await repo_container.health_check()
            results["repository"] = "ok" if repo_healthy else "unhealthy"
        except Exception as e:
            results["repository"] = f"error: {e}"

        try:
            await self.get_chat_service()
            results["chat_service"] = "ok"
        except Exception as e:
            results["chat_service"] = f"error: {e}"

        return results

    async def cleanup(self):
        """Clean up all resources."""
        if self._database:
            await self._database.close()
            self._database = None
        
        self._repository_container = None
        self._chat_service = None


class TestingContainer(ApplicationContainer):
    """
    Specialized container for testing that always uses SQLite.
    
    This container is pre-configured for testing scenarios with:
    - In-memory SQLite database
    - Optimized for speed over durability
    - Isolated from production configuration
    """

    def __init__(self):
        """Initialize test container with SQLite configuration."""
        super().__init__(force_sqlite=True)

    async def get_database(self) -> Database:
        """Get database configured specifically for testing."""
        if self._database is None:
            # Create test-specific configuration
            config = DatabaseConfig(
                use_sqlite=True,
                sqlite_path=":memory:",
                echo=False,  # Reduce noise in tests
            )
            self._database = Database(config)
        
        return self._database


# Global container instance for the application
_app_container: ApplicationContainer | None = None


def get_application_container() -> ApplicationContainer:
    """
    Get the global application container instance.
    
    Returns:
        Singleton ApplicationContainer instance
    """
    global _app_container
    if _app_container is None:
        _app_container = ApplicationContainer()
    return _app_container


def reset_application_container():
    """
    Reset the global container. Useful for testing.
    """
    global _app_container
    _app_container = None