from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from ..value_objects.thread_status import ThreadStatus


class ChatThread:
    def __init__(
        self,
        user_id: UUID,
        thread_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        status: ThreadStatus = ThreadStatus.ACTIVE,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.thread_id = thread_id or uuid4()
        self.user_id = user_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.status = status
        self.title = title
        self.summary = summary
        self.metadata = metadata or {}
    
    def update_title(self, title: str) -> None:
        self.title = title
        self.updated_at = datetime.now()
    
    def update_summary(self, summary: str) -> None:
        self.summary = summary
        self.updated_at = datetime.now()
    
    def archive(self) -> None:
        self.status = ThreadStatus.ARCHIVED
        self.updated_at = datetime.now()
    
    def delete(self) -> None:
        self.status = ThreadStatus.DELETED
        self.updated_at = datetime.now()
    
    def restore(self) -> None:
        self.status = ThreadStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value
        self.updated_at = datetime.now()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChatThread):
            return False
        return self.thread_id == other.thread_id
    
    def __hash__(self) -> int:
        return hash(self.thread_id)