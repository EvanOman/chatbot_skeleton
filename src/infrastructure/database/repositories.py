from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.chat_message import ChatMessage
from ...domain.entities.chat_thread import ChatThread
from ...domain.repositories.chat_message_repository import ChatMessageRepository
from ...domain.repositories.chat_thread_repository import ChatThreadRepository
from .mappers import ChatMessageMapper, ChatThreadMapper
from .models import ChatMessageModel, ChatThreadModel


class SQLAlchemyChatThreadRepository(ChatThreadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, thread: ChatThread) -> ChatThread:
        model = ChatThreadMapper.to_model(thread)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return ChatThreadMapper.to_domain(model)

    async def get_by_id(self, thread_id: UUID) -> ChatThread | None:
        stmt = select(ChatThreadModel).where(ChatThreadModel.thread_id == thread_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ChatThreadMapper.to_domain(model) if model else None

    async def get_by_user_id(self, user_id: UUID) -> list[ChatThread]:
        stmt = (
            select(ChatThreadModel)
            .where(ChatThreadModel.user_id == user_id)
            .order_by(ChatThreadModel.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [ChatThreadMapper.to_domain(model) for model in models]

    async def update(self, thread: ChatThread) -> ChatThread:
        stmt = select(ChatThreadModel).where(
            ChatThreadModel.thread_id == thread.thread_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        ChatThreadMapper.update_model(model, thread)
        await self.session.commit()
        await self.session.refresh(model)
        return ChatThreadMapper.to_domain(model)

    async def delete(self, thread_id: UUID) -> bool:
        stmt = delete(ChatThreadModel).where(ChatThreadModel.thread_id == thread_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def exists(self, thread_id: UUID) -> bool:
        stmt = select(ChatThreadModel.thread_id).where(
            ChatThreadModel.thread_id == thread_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class SQLAlchemyChatMessageRepository(ChatMessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, message: ChatMessage) -> ChatMessage:
        model = ChatMessageMapper.to_model(message)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return ChatMessageMapper.to_domain(model)

    async def get_by_id(self, message_id: UUID) -> ChatMessage | None:
        stmt = select(ChatMessageModel).where(ChatMessageModel.message_id == message_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ChatMessageMapper.to_domain(model) if model else None

    async def get_by_thread_id(self, thread_id: UUID) -> list[ChatMessage]:
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.thread_id == thread_id)
            .order_by(ChatMessageModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [ChatMessageMapper.to_domain(model) for model in models]

    async def update(self, message: ChatMessage) -> ChatMessage:
        stmt = select(ChatMessageModel).where(
            ChatMessageModel.message_id == message.message_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        ChatMessageMapper.update_model(model, message)
        await self.session.commit()
        await self.session.refresh(model)
        return ChatMessageMapper.to_domain(model)

    async def delete(self, message_id: UUID) -> bool:
        stmt = delete(ChatMessageModel).where(ChatMessageModel.message_id == message_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def get_recent_messages(
        self, thread_id: UUID, limit: int = 50
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.thread_id == thread_id)
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        # Reverse to get chronological order (oldest first)
        return [ChatMessageMapper.to_domain(model) for model in reversed(models)]
