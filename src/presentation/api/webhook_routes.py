"""
API routes for webhook functionality.

This module provides endpoints for managing webhooks that can be triggered
by various events in the chat application, enabling external integrations.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.services.chat_service import ChatService
from ...application.services.dspy_react_agent import DSPyReactAgent
from ...infrastructure.database.repositories import (
    SQLAlchemyChatMessageRepository,
    SQLAlchemyChatThreadRepository,
)
from .dependencies import get_database_session

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class WebhookConfig(BaseModel):
    """Configuration for a webhook endpoint."""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique webhook ID"
    )
    name: str = Field(..., description="Human-readable name for the webhook")
    url: HttpUrl = Field(..., description="Target URL to POST webhook data")
    events: list[str] = Field(
        default=["message_created", "thread_created"],
        description="List of events that trigger this webhook",
    )
    active: bool = Field(default=True, description="Whether the webhook is active")
    secret: str | None = Field(
        None, description="Optional secret for webhook signature validation"
    )
    headers: dict[str, str] = Field(
        default_factory=dict, description="Additional headers to send with webhook"
    )
    timeout: int = Field(
        default=30, description="Request timeout in seconds", ge=1, le=300
    )
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts on failure", ge=0, le=10
    )
    created_at: datetime = Field(default_factory=datetime.now)
    last_triggered: datetime | None = Field(None)


class WebhookEvent(BaseModel):
    """Webhook event payload."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.now)
    data: dict[str, Any] = Field(..., description="Event data")


class WebhookResponse(BaseModel):
    """Response from webhook delivery attempt."""

    webhook_id: str
    event_id: str
    success: bool
    status_code: int | None = None
    response_body: str | None = None
    error: str | None = None
    delivered_at: datetime = Field(default_factory=datetime.now)


# In-memory webhook storage (in production, use database)
webhooks: dict[str, WebhookConfig] = {}
webhook_history: list[WebhookResponse] = []


def get_chat_service(
    session: AsyncSession = Depends(get_database_session),
) -> ChatService:
    thread_repo = SQLAlchemyChatThreadRepository(session)
    message_repo = SQLAlchemyChatMessageRepository(session)
    bot_service = DSPyReactAgent()
    return ChatService(thread_repo, message_repo, bot_service)


@router.post(
    "/",
    response_model=WebhookConfig,
    summary="Create a new webhook",
    description="""
    Register a new webhook endpoint that will receive HTTP POST requests
    when specified events occur in the chat application.

    **Supported Events:**
    - `message_created`: Triggered when a new message is created
    - `thread_created`: Triggered when a new thread is created
    - `agent_response`: Triggered when the AI agent responds
    - `file_uploaded`: Triggered when a file is uploaded
    - `error_occurred`: Triggered when an error occurs

    **Webhook Payload:**
    ```json
    {
        "event_id": "uuid4",
        "event_type": "message_created",
        "timestamp": "2024-01-15T10:30:00Z",
        "data": {
            "message_id": "uuid4",
            "thread_id": "uuid4",
            "content": "Hello!",
            "role": "user"
        }
    }
    ```

    **Security:**
    - Optional secret for HMAC signature validation
    - Custom headers support for authentication
    - Configurable timeout and retry logic

    **Use Cases:**
    - External system notifications
    - Analytics and monitoring
    - Backup and archival
    - Integration with CRM or support systems
    """,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook(webhook_config: WebhookConfig) -> WebhookConfig:
    """Create a new webhook configuration."""
    webhook_config.id = str(uuid4())  # Generate new ID
    webhook_config.created_at = datetime.now()
    webhook_config.last_triggered = None

    webhooks[webhook_config.id] = webhook_config

    return webhook_config


@router.get(
    "/",
    response_model=list[WebhookConfig],
    summary="List all webhooks",
    description="Retrieve all registered webhook configurations.",
)
async def list_webhooks() -> list[WebhookConfig]:
    """List all registered webhooks."""
    return list(webhooks.values())


@router.get(
    "/{webhook_id}",
    response_model=WebhookConfig,
    summary="Get webhook details",
    description="Retrieve details for a specific webhook configuration.",
)
async def get_webhook(webhook_id: str) -> WebhookConfig:
    """Get webhook configuration by ID."""
    if webhook_id not in webhooks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )

    return webhooks[webhook_id]


@router.put(
    "/{webhook_id}",
    response_model=WebhookConfig,
    summary="Update webhook configuration",
    description="Update an existing webhook configuration.",
)
async def update_webhook(
    webhook_id: str, webhook_config: WebhookConfig
) -> WebhookConfig:
    """Update webhook configuration."""
    if webhook_id not in webhooks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )

    webhook_config.id = webhook_id  # Preserve ID
    webhooks[webhook_id] = webhook_config

    return webhook_config


@router.delete(
    "/{webhook_id}",
    summary="Delete webhook",
    description="Remove a webhook configuration.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_webhook(webhook_id: str):
    """Delete a webhook configuration."""
    if webhook_id not in webhooks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )

    del webhooks[webhook_id]


@router.post(
    "/{webhook_id}/test",
    response_model=WebhookResponse,
    summary="Test webhook delivery",
    description="""
    Send a test event to a webhook endpoint to verify connectivity
    and configuration.

    This sends a sample `test_event` with mock data to help debug
    webhook integrations before going live.
    """,
)
async def test_webhook(
    webhook_id: str, background_tasks: BackgroundTasks
) -> WebhookResponse:
    """Send a test event to the webhook."""
    if webhook_id not in webhooks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )

    webhook = webhooks[webhook_id]

    # Create test event
    test_event = WebhookEvent(
        event_type="test_event",
        data={
            "message": "This is a test webhook delivery",
            "webhook_id": webhook_id,
            "webhook_name": webhook.name,
            "test": True,
        },
    )

    # Deliver webhook in background
    response = await _deliver_webhook(webhook, test_event)

    return response


@router.get(
    "/{webhook_id}/history",
    response_model=list[WebhookResponse],
    summary="Get webhook delivery history",
    description="Retrieve delivery history for a specific webhook.",
)
async def get_webhook_history(webhook_id: str) -> list[WebhookResponse]:
    """Get delivery history for a webhook."""
    if webhook_id not in webhooks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )

    # Filter history for this webhook
    return [h for h in webhook_history if h.webhook_id == webhook_id]


@router.get(
    "/events/types",
    summary="List available event types",
    description="Get a list of all available event types that can trigger webhooks.",
)
async def list_event_types():
    """List all available webhook event types."""
    return {
        "event_types": [
            {
                "name": "message_created",
                "description": "Triggered when a new message is created by a user",
                "example_data": {
                    "message_id": "uuid4",
                    "thread_id": "uuid4",
                    "user_id": "uuid4",
                    "content": "Hello!",
                    "role": "user",
                    "type": "text",
                },
            },
            {
                "name": "agent_response",
                "description": "Triggered when the AI agent generates a response",
                "example_data": {
                    "message_id": "uuid4",
                    "thread_id": "uuid4",
                    "content": "Hello! How can I help you?",
                    "role": "assistant",
                    "tools_used": ["search", "calculator"],
                    "processing_time": 1.23,
                },
            },
            {
                "name": "thread_created",
                "description": "Triggered when a new chat thread is created",
                "example_data": {
                    "thread_id": "uuid4",
                    "user_id": "uuid4",
                    "title": "New Chat",
                    "status": "active",
                },
            },
            {
                "name": "file_uploaded",
                "description": "Triggered when a file is uploaded to a chat",
                "example_data": {
                    "thread_id": "uuid4",
                    "filename": "document.pdf",
                    "file_size": 1024,
                    "file_type": "application/pdf",
                },
            },
            {
                "name": "error_occurred",
                "description": "Triggered when an error occurs in the application",
                "example_data": {
                    "error_type": "ValidationError",
                    "error_message": "Invalid input format",
                    "thread_id": "uuid4",
                    "user_id": "uuid4",
                },
            },
        ]
    }


async def _deliver_webhook(
    webhook: WebhookConfig, event: WebhookEvent
) -> WebhookResponse:
    """Deliver a webhook event with retry logic."""

    payload = event.model_dump()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SampleChatApp-Webhook/1.0",
        **webhook.headers,
    }

    # Add signature if secret is provided
    if webhook.secret:
        import hashlib
        import hmac

        signature = hmac.new(
            webhook.secret.encode(), json.dumps(payload).encode(), hashlib.sha256
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    last_error = None

    for attempt in range(webhook.retry_attempts + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    str(webhook.url),
                    json=payload,
                    headers=headers,
                    timeout=webhook.timeout,
                )

                webhook_response = WebhookResponse(
                    webhook_id=webhook.id,
                    event_id=event.event_id,
                    success=response.is_success,
                    status_code=response.status_code,
                    response_body=(
                        response.text[:1000] if response.text else None
                    ),  # Truncate
                    error=(
                        None if response.is_success else f"HTTP {response.status_code}"
                    ),
                )

                # Update webhook last triggered time if successful
                if response.is_success:
                    webhook.last_triggered = datetime.now()

                webhook_history.append(webhook_response)
                return webhook_response

        except Exception as e:
            last_error = str(e)
            if attempt < webhook.retry_attempts:
                await asyncio.sleep(2**attempt)  # Exponential backoff

    # All attempts failed
    webhook_response = WebhookResponse(
        webhook_id=webhook.id,
        event_id=event.event_id,
        success=False,
        status_code=None,
        response_body=None,
        error=f"Failed after {webhook.retry_attempts + 1} attempts: {last_error}",
    )

    webhook_history.append(webhook_response)
    return webhook_response


async def trigger_webhook_event(event_type: str, data: dict[str, Any]):
    """Trigger webhooks for a specific event type."""

    # Find active webhooks for this event type
    active_webhooks = [
        webhook
        for webhook in webhooks.values()
        if webhook.active and event_type in webhook.events
    ]

    if not active_webhooks:
        return

    # Create event
    event = WebhookEvent(event_type=event_type, data=data)

    # Deliver to all matching webhooks concurrently
    tasks = [_deliver_webhook(webhook, event) for webhook in active_webhooks]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


# Example usage function that would be called from other parts of the application
async def notify_message_created(message_data: dict[str, Any]):
    """Helper function to trigger message_created webhooks."""
    await trigger_webhook_event("message_created", message_data)


async def notify_thread_created(thread_data: dict[str, Any]):
    """Helper function to trigger thread_created webhooks."""
    await trigger_webhook_event("thread_created", thread_data)


async def notify_agent_response(response_data: dict[str, Any]):
    """Helper function to trigger agent_response webhooks."""
    await trigger_webhook_event("agent_response", response_data)
