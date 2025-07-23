from uuid import UUID, uuid4

from ...domain.entities.chat_message import ChatMessage
from ...domain.entities.chat_thread import ChatThread
from ...domain.repositories.chat_message_repository import ChatMessageRepository
from ...domain.repositories.chat_thread_repository import ChatThreadRepository
from ...domain.value_objects.message_role import MessageRole
from ..dto.chat_dto import (
    CreateThreadRequest,
    MessageResponse,
    SendMessageRequest,
    ThreadResponse,
)
from ..interfaces.bot_service import BotService


class ChatService:
    def __init__(
        self,
        thread_repository: ChatThreadRepository,
        message_repository: ChatMessageRepository,
        bot_service: BotService,
    ):
        self.thread_repository = thread_repository
        self.message_repository = message_repository
        self.bot_service = bot_service

    async def create_thread(self, request: CreateThreadRequest) -> ThreadResponse:
        thread = ChatThread(
            user_id=request.user_id,
            title=request.title,
        )

        created_thread = await self.thread_repository.create(thread)

        return ThreadResponse(
            thread_id=created_thread.thread_id,
            user_id=created_thread.user_id,
            created_at=created_thread.created_at,
            updated_at=created_thread.updated_at,
            status=created_thread.status,
            title=created_thread.title,
            summary=created_thread.summary,
            metadata=created_thread.metadata,
        )

    async def get_thread(self, thread_id: UUID) -> ThreadResponse | None:
        thread = await self.thread_repository.get_by_id(thread_id)
        if not thread:
            return None

        return ThreadResponse(
            thread_id=thread.thread_id,
            user_id=thread.user_id,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            status=thread.status,
            title=thread.title,
            summary=thread.summary,
            metadata=thread.metadata,
        )

    async def get_user_threads(self, user_id: UUID) -> list[ThreadResponse]:
        threads = await self.thread_repository.get_by_user_id(user_id)

        return [
            ThreadResponse(
                thread_id=thread.thread_id,
                user_id=thread.user_id,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                status=thread.status,
                title=thread.title,
                summary=thread.summary,
                metadata=thread.metadata,
            )
            for thread in threads
        ]

    async def send_message(
        self, thread_id: UUID, user_id: UUID, request: SendMessageRequest
    ) -> list[MessageResponse]:
        # Verify thread exists
        if not await self.thread_repository.exists(thread_id):
            raise ValueError(f"Thread {thread_id} not found")

        # Create user message
        user_message = ChatMessage(
            thread_id=thread_id,
            user_id=user_id,
            role=MessageRole.USER,
            content=request.content,
            message_type=request.message_type,
        )

        # Save user message
        saved_user_message = await self.message_repository.create(user_message)

        # Generate bot response
        bot_response_content = await self.bot_service.generate_response(
            saved_user_message, thread_id
        )

        # Create bot message (using system user ID)
        bot_message = ChatMessage(
            thread_id=thread_id,
            user_id=uuid4(),  # Bot system user ID
            role=MessageRole.AI,
            content=bot_response_content,
        )

        # Save bot message
        saved_bot_message = await self.message_repository.create(bot_message)

        return [
            MessageResponse(
                message_id=saved_user_message.message_id,
                thread_id=saved_user_message.thread_id,
                user_id=saved_user_message.user_id,
                role=saved_user_message.role,
                content=saved_user_message.content,
                type=saved_user_message.type,
                metadata=saved_user_message.metadata,
                created_at=saved_user_message.created_at,
            ),
            MessageResponse(
                message_id=saved_bot_message.message_id,
                thread_id=saved_bot_message.thread_id,
                user_id=saved_bot_message.user_id,
                role=saved_bot_message.role,
                content=saved_bot_message.content,
                type=saved_bot_message.type,
                metadata=saved_bot_message.metadata,
                created_at=saved_bot_message.created_at,
            ),
        ]

    async def get_thread_messages(self, thread_id: UUID) -> list[MessageResponse]:
        messages = await self.message_repository.get_by_thread_id(thread_id)

        return [
            MessageResponse(
                message_id=message.message_id,
                thread_id=message.thread_id,
                user_id=message.user_id,
                role=message.role,
                content=message.content,
                type=message.type,
                metadata=message.metadata,
                created_at=message.created_at,
            )
            for message in messages
        ]
