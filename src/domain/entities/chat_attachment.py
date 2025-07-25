from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


class ChatAttachment:
    def __init__(
        self,
        message_id: UUID,
        thread_id: UUID,
        url: str,
        attachment_id: UUID | None = None,
        file_type: str | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ):
        self.attachment_id = attachment_id or uuid4()
        self.message_id = message_id
        self.thread_id = thread_id
        self.url = url
        self.file_type = file_type
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()

    def update_url(self, url: str) -> None:
        self.url = url

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChatAttachment):
            return False
        return self.attachment_id == other.attachment_id

    def __hash__(self) -> int:
        return hash(self.attachment_id)
