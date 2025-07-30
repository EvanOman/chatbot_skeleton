import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
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
        use_sqlite: bool = False,
        sqlite_path: str = ":memory:",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.echo = echo
        self.use_sqlite = use_sqlite
        self.sqlite_path = sqlite_path

    @property
    def url(self) -> str:
        if self.use_sqlite:
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        # Use SQLite for testing, PostgreSQL for production
        use_sqlite = os.getenv("TESTING", "false").lower() == "true"

        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            username=os.getenv("DB_USERNAME", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            database=os.getenv("DB_DATABASE", "chatapp"),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            use_sqlite=use_sqlite,
            sqlite_path=os.getenv("SQLITE_PATH", ":memory:"),
        )


class Database:
    def __init__(self, config: DatabaseConfig):
        self.config = config

        # Configure engine based on database type
        if config.use_sqlite:
            # SQLite configuration - optimized for testing
            self.engine = create_async_engine(
                config.url,
                echo=config.echo,
                future=True,
                # SQLite doesn't support connection pooling the same way
            )
        else:
            # PostgreSQL configuration
            is_testing = os.getenv("TESTING", "false").lower() == "true"

            if is_testing:
                # Use NullPool for testing to prevent connection sharing issues
                self.engine = create_async_engine(
                    config.url,
                    echo=config.echo,
                    poolclass=NullPool,
                    connect_args={
                        "command_timeout": 60,  # Timeout for CI environments
                        "server_settings": {
                            "application_name": "sample_chat_app_tests",
                        },
                    },
                )
            else:
                # Production PostgreSQL with connection pooling
                self.engine = create_async_engine(
                    config.url,
                    echo=config.echo,
                    pool_size=5,
                    max_overflow=10,
                    pool_recycle=3600,
                    connect_args={
                        "command_timeout": 60,
                        "server_settings": {
                            "application_name": "sample_chat_app",
                        },
                    },
                )

        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncSession:
        async with self.async_session_factory() as session:
            yield session

    def get_engine(self):
        """Get the underlying SQLAlchemy engine."""
        return self.engine

    async def close(self) -> None:
        await self.engine.dispose()
