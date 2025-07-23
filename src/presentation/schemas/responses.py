from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ...domain.value_objects.message_role import MessageRole
from ...domain.value_objects.thread_status import ThreadStatus


class ThreadResponse(BaseModel):
    """Response containing thread information."""
    
    thread_id: UUID = Field(
        ..., 
        description="Unique identifier for the thread",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    user_id: UUID = Field(
        ..., 
        description="UUID of the user who created the thread",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    created_at: datetime = Field(
        ..., 
        description="Timestamp when the thread was created",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: datetime = Field(
        ..., 
        description="Timestamp when the thread was last updated",
        examples=["2024-01-15T14:22:30Z"]
    )
    status: ThreadStatus = Field(
        ..., 
        description="Current status of the thread"
    )
    title: str | None = Field(
        None, 
        description="Optional title for the thread",
        examples=["General Discussion", "Tech Support", None]
    )
    summary: str | None = Field(
        None, 
        description="Optional summary of the thread conversation",
        examples=["Discussion about machine learning concepts", None]
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata for the thread",
        examples=[{}, {"priority": "high", "category": "support"}]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "thread_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T14:22:30Z",
                    "status": "active",
                    "title": "General Discussion",
                    "summary": "Discussion about machine learning concepts",
                    "metadata": {"priority": "high", "category": "support"}
                }
            ]
        }
    }


class MessageResponse(BaseModel):
    """Response containing message information."""
    
    message_id: UUID = Field(
        ..., 
        description="Unique identifier for the message",
        examples=["789e0123-e45b-67d8-a901-234567890abc"]
    )
    thread_id: UUID = Field(
        ..., 
        description="UUID of the thread this message belongs to",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    user_id: UUID = Field(
        ..., 
        description="UUID of the user who sent the message",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    role: MessageRole = Field(
        ..., 
        description="Role of the message sender (user or assistant)"
    )
    content: str = Field(
        ..., 
        description="The message content",
        examples=[
            "Hello! How can I help you today?",
            "I calculated: 25 * 18 + 42 = 492",
            "The weather in San Francisco is currently 72°F and sunny."
        ]
    )
    type: str = Field(
        ..., 
        description="Type of message",
        examples=["text", "file", "image"]
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata for the message",
        examples=[{}, {"processed_by": "dspy_agent", "tools_used": ["calculator"]}]
    )
    created_at: datetime = Field(
        ..., 
        description="Timestamp when the message was created",
        examples=["2024-01-15T10:31:15Z"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message_id": "789e0123-e45b-67d8-a901-234567890abc",
                    "thread_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "role": "user",
                    "content": "Hello! How can I help you today?",
                    "type": "text",
                    "metadata": {},
                    "created_at": "2024-01-15T10:31:15Z"
                },
                {
                    "message_id": "def1234-e45b-67d8-a901-567890abcdef",
                    "thread_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "role": "assistant",
                    "content": "I calculated: 25 * 18 + 42 = 492",
                    "type": "text",
                    "metadata": {"processed_by": "dspy_agent", "tools_used": ["calculator"]},
                    "created_at": "2024-01-15T10:31:30Z"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Error response format."""
    
    error: str = Field(
        ..., 
        description="Error type or category",
        examples=["ValidationError", "NotFound", "InternalServerError"]
    )
    detail: str | None = Field(
        None, 
        description="Detailed error message",
        examples=["Thread not found", "Invalid UUID format", "Database connection failed"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "NotFound",
                    "detail": "Thread not found"
                },
                {
                    "error": "ValidationError", 
                    "detail": "Invalid UUID format"
                }
            ]
        }
    }
