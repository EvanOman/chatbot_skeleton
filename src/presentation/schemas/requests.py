from uuid import UUID

from pydantic import BaseModel


class CreateThreadRequest(BaseModel):
    user_id: UUID
    title: str | None = None


class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"
