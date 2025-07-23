from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.chat_thread import ChatThread


class ChatThreadRepository(ABC):
    @abstractmethod
    async def create(self, thread: ChatThread) -> ChatThread:
        pass

    @abstractmethod
    async def get_by_id(self, thread_id: UUID) -> ChatThread | None:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[ChatThread]:
        pass

    @abstractmethod
    async def update(self, thread: ChatThread) -> ChatThread:
        pass

    @abstractmethod
    async def delete(self, thread_id: UUID) -> bool:
        pass

    @abstractmethod
    async def exists(self, thread_id: UUID) -> bool:
        pass
