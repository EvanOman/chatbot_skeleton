from uuid import UUID

from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    """Request to create a new chat thread."""

    user_id: UUID = Field(
        ...,
        description="The UUID of the user creating the thread",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    title: str | None = Field(
        None,
        description="Optional title for the thread",
        examples=[
            "General Discussion",
            "Tech Support",
            "Project Planning",
            "Quick Questions",
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "General Discussion",
                },
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "title": "Tech Support Request",
                },
                {"user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "title": None},
            ]
        }
    }


class SendMessageRequest(BaseModel):
    """Request to send a message to a thread."""

    content: str = Field(
        ...,
        description="The message content",
        examples=[
            "Hello! How can I help you today?",
            "Can you explain how machine learning works?",
            "What's the weather like in San Francisco?",
            "Calculate 25 * 18 + 42",
            "Search for the latest news about artificial intelligence",
        ],
    )
    message_type: str = Field(
        "text",
        description="Type of message (text, file, etc.)",
        examples=["text", "file", "image"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"content": "Hello! How can I help you today?", "message_type": "text"},
                {
                    "content": "Can you explain how machine learning works?",
                    "message_type": "text",
                },
                {
                    "content": "What's the weather like in San Francisco?",
                    "message_type": "text",
                },
                {"content": "Calculate 25 * 18 + 42", "message_type": "text"},
            ]
        }
    }
