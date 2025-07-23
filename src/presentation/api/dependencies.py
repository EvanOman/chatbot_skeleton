from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...infrastructure.container.container import Container


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    database = Container.database()
    async for session in database.get_session():
        yield session