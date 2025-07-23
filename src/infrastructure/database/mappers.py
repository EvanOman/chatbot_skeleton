from ...domain.entities.chat_attachment import ChatAttachment
from ...domain.entities.chat_message import ChatMessage
from ...domain.entities.chat_thread import ChatThread
from ...domain.value_objects.message_role import MessageRole
from ...domain.value_objects.thread_status import ThreadStatus
from .models import ChatAttachmentModel, ChatMessageModel, ChatThreadModel


class ChatThreadMapper:
    @staticmethod
    def to_domain(model: ChatThreadModel) -> ChatThread:
        return ChatThread(
            thread_id=model.thread_id,
            user_id=model.user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            status=ThreadStatus(model.status),
            title=model.title,
            summary=model.summary,
            metadata=model.metadata_json or {},
        )

    @staticmethod
    def to_model(entity: ChatThread) -> ChatThreadModel:
        return ChatThreadModel(
            thread_id=entity.thread_id,
            user_id=entity.user_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            status=entity.status.value,
            title=entity.title,
            summary=entity.summary,
            metadata_json=entity.metadata,
        )

    @staticmethod
    def update_model(model: ChatThreadModel, entity: ChatThread) -> None:
        model.user_id = entity.user_id
        model.updated_at = entity.updated_at
        model.status = entity.status.value
        model.title = entity.title
        model.summary = entity.summary
        model.metadata_json = entity.metadata


class ChatMessageMapper:
    @staticmethod
    def to_domain(model: ChatMessageModel) -> ChatMessage:
        return ChatMessage(
            message_id=model.message_id,
            thread_id=model.thread_id,
            user_id=model.user_id,
            role=MessageRole(model.role),
            content=model.content,
            message_type=model.type,
            metadata=model.metadata_json or {},
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(entity: ChatMessage) -> ChatMessageModel:
        return ChatMessageModel(
            message_id=entity.message_id,
            thread_id=entity.thread_id,
            user_id=entity.user_id,
            role=entity.role.value,
            content=entity.content,
            type=entity.type,
            metadata_json=entity.metadata,
            created_at=entity.created_at,
        )

    @staticmethod
    def update_model(model: ChatMessageModel, entity: ChatMessage) -> None:
        model.thread_id = entity.thread_id
        model.user_id = entity.user_id
        model.role = entity.role.value
        model.content = entity.content
        model.type = entity.type
        model.metadata_json = entity.metadata


class ChatAttachmentMapper:
    @staticmethod
    def to_domain(model: ChatAttachmentModel) -> ChatAttachment:
        return ChatAttachment(
            attachment_id=model.attachment_id,
            message_id=model.message_id,
            thread_id=model.thread_id,
            url=model.url,
            file_type=model.file_type,
            metadata=model.metadata_json or {},
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(entity: ChatAttachment) -> ChatAttachmentModel:
        return ChatAttachmentModel(
            attachment_id=entity.attachment_id,
            message_id=entity.message_id,
            thread_id=entity.thread_id,
            url=entity.url,
            file_type=entity.file_type,
            metadata_json=entity.metadata,
            created_at=entity.created_at,
        )

    @staticmethod
    def update_model(model: ChatAttachmentModel, entity: ChatAttachment) -> None:
        model.message_id = entity.message_id
        model.thread_id = entity.thread_id
        model.url = entity.url
        model.file_type = entity.file_type
        model.metadata_json = entity.metadata
