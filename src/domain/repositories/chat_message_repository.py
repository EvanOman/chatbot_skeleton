from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.chat_message import ChatMessage


class ChatMessageRepository(ABC):
    @abstractmethod
    async def create(self, message: ChatMessage) -> ChatMessage:
        pass

    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> ChatMessage | None:
        pass

    @abstractmethod
    async def get_by_thread_id(self, thread_id: UUID) -> list[ChatMessage]:
        pass

    @abstractmethod
    async def update(self, message: ChatMessage) -> ChatMessage:
        pass

    @abstractmethod
    async def delete(self, message_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_recent_messages(
        self, thread_id: UUID, limit: int = 50
    ) -> list[ChatMessage]:
        pass
