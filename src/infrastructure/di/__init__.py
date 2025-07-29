"""
Dependency Injection module for the chat application.

This module provides centralized dependency management with support for:
- Environment-based configuration (production vs testing)
- Repository pattern with Unit of Work
- Database abstraction (PostgreSQL/SQLite)
- Service layer orchestration

Main exports:
- ApplicationContainer: Main DI container for production
- TestContainer: Specialized container for testing
- get_application_container: Global container access
"""

from .container import (
    ApplicationContainer,
    TestingContainer,
    get_application_container,
    reset_application_container,
)

__all__ = [
    "ApplicationContainer",
    "TestingContainer", 
    "get_application_container",
    "reset_application_container",
]