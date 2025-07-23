from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from ..value_objects.message_role import MessageRole


class ChatMessage:
    def __init__(
        self,
        thread_id: UUID,
        user_id: UUID,
        role: MessageRole,
        content: str,
        message_id: UUID | None = None,
        message_type: str = "text",
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ):
        self.message_id = message_id or uuid4()
        self.thread_id = thread_id
        self.user_id = user_id
        self.role = role
        self.content = content
        self.type = message_type
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()

    def update_content(self, content: str) -> None:
        self.content = content

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def is_from_user(self) -> bool:
        return self.role == MessageRole.USER

    def is_from_ai(self) -> bool:
        return self.role == MessageRole.AI

    def is_system_message(self) -> bool:
        return self.role == MessageRole.SYSTEM

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChatMessage):
            return False
        return self.message_id == other.message_id

    def __hash__(self) -> int:
        return hash(self.message_id)
