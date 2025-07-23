from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from ...domain.value_objects.message_role import MessageRole
from ...domain.value_objects.thread_status import ThreadStatus


class CreateThreadRequest(BaseModel):
    user_id: UUID
    title: str | None = None


class ThreadResponse(BaseModel):
    thread_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    status: ThreadStatus
    title: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] = {}


class CreateMessageRequest(BaseModel):
    thread_id: UUID
    user_id: UUID
    role: MessageRole
    content: str
    message_type: str = "text"


class MessageResponse(BaseModel):
    message_id: UUID
    thread_id: UUID
    user_id: UUID
    role: MessageRole
    content: str
    type: str
    metadata: dict[str, Any] = {}
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"
