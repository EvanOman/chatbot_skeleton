"""
Centralized port configuration for the entire application.

This module provides a single source of truth for all port configurations,
making it easy to manage and avoid conflicts between different services.
"""

import os
from typing import Optional


class PortConfig:
    """Centralized configuration for all application ports."""
    
    # Application ports
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    
    # Database ports
    DB_PORT: int = int(os.getenv("DB_PORT", "5433"))
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    
    # Admin interface ports
    ADMINER_PORT: int = int(os.getenv("ADMINER_PORT", "8080"))
    
    # Development server port (when using `uv run dev`)
    DEV_PORT: int = int(os.getenv("DEV_PORT", "8002"))
    
    # WebSocket configuration
    WS_PORT: Optional[int] = int(os.getenv("WS_PORT", str(APP_PORT)))  # Default to same as app
    
    @classmethod
    def get_app_url(cls, host: Optional[str] = None) -> str:
        """Get the full application URL."""
        host = host or "localhost"
        return f"http://{host}:{cls.APP_PORT}"
    
    @classmethod
    def get_ws_url(cls, host: Optional[str] = None) -> str:
        """Get the WebSocket URL."""
        host = host or "localhost"
        return f"ws://{host}:{cls.WS_PORT}"
    
    @classmethod
    def get_db_url(cls, 
                   username: Optional[str] = None,
                   password: Optional[str] = None,
                   database: Optional[str] = None,
                   driver: str = "postgresql+asyncpg") -> str:
        """Get the database connection URL."""
        username = username or os.getenv("DB_USERNAME", "postgres")
        password = password or os.getenv("DB_PASSWORD", "postgres")
        database = database or os.getenv("DB_DATABASE", "chatapp")
        
        return f"{driver}://{username}:{password}@{cls.DB_HOST}:{cls.DB_PORT}/{database}"
    
    @classmethod
    def get_adminer_url(cls, host: Optional[str] = None) -> str:
        """Get the Adminer database GUI URL."""
        host = host or "localhost"
        return f"http://{host}:{cls.ADMINER_PORT}"
    
    @classmethod
    def validate_ports(cls) -> None:
        """Validate that all configured ports are unique."""
        ports = {
            "APP_PORT": cls.APP_PORT,
            "DB_PORT": cls.DB_PORT,
            "ADMINER_PORT": cls.ADMINER_PORT,
            "DEV_PORT": cls.DEV_PORT,
        }
        
        # Only add WS_PORT if it's different from APP_PORT
        if cls.WS_PORT != cls.APP_PORT:
            ports["WS_PORT"] = cls.WS_PORT
        
        # Check for duplicate ports
        seen_ports = {}
        for name, port in ports.items():
            if port in seen_ports:
                raise ValueError(
                    f"Port conflict: {name}={port} conflicts with "
                    f"{seen_ports[port]}={port}"
                )
            seen_ports[port] = name
    
    @classmethod
    def print_config(cls) -> None:
        """Print the current port configuration."""
        print("=== Port Configuration ===")
        print(f"Application: {cls.get_app_url()}")
        print(f"WebSocket: {cls.get_ws_url()}")
        print(f"Database: {cls.DB_HOST}:{cls.DB_PORT}")
        print(f"Adminer: {cls.get_adminer_url()}")
        print(f"Dev Server: http://localhost:{cls.DEV_PORT}")
        print("========================")


# Validate ports on module load
try:
    PortConfig.validate_ports()
except ValueError as e:
    print(f"WARNING: {e}")