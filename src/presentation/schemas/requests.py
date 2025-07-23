from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CreateThreadRequest(BaseModel):
    user_id: UUID
    title: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"