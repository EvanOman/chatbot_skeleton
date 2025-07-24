from uuid import UUID

from ...domain.entities.chat_message import ChatMessage
from ..interfaces.bot_service import BotService


class EchoBot(BotService):
    async def generate_response(
        self, user_message: ChatMessage, thread_id: UUID
    ) -> str:
        return f"Echo: {user_message.content}"
