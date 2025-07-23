import os
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool


class DatabaseConfig:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        username: str = "postgres",
        password: str = "postgres",
        database: str = "chatapp",
        echo: bool = False,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.echo = echo
    
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            username=os.getenv("DB_USERNAME", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            database=os.getenv("DB_DATABASE", "chatapp"),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )


class Database:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = create_async_engine(
            config.url,
            echo=config.echo,
            poolclass=NullPool,
        )
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session_factory() as session:
            yield session
    
    async def close(self) -> None:
        await self.engine.dispose()