from abc import ABC, abstractmethod
from uuid import UUID

from ...domain.entities.chat_message import ChatMessage


class BotService(ABC):
    @abstractmethod
    async def generate_response(self, user_message: ChatMessage, thread_id: UUID) -> str:
        pass