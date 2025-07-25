from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ...infrastructure.container.container import Container


async def get_database_session() -> AsyncGenerator[AsyncSession]:
    database = Container.database()
    async for session in database.get_session():
        yield session
