from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.chat_message import ChatMessage


class ChatMessageRepository(ABC):
    @abstractmethod
    async def create(self, message: ChatMessage) -> ChatMessage:
        pass
    
    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> Optional[ChatMessage]:
        pass
    
    @abstractmethod
    async def get_by_thread_id(self, thread_id: UUID) -> List[ChatMessage]:
        pass
    
    @abstractmethod
    async def update(self, message: ChatMessage) -> ChatMessage:
        pass
    
    @abstractmethod
    async def delete(self, message_id: UUID) -> bool:
        pass
    
    @abstractmethod
    async def get_recent_messages(self, thread_id: UUID, limit: int = 50) -> List[ChatMessage]:
        pass