from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.dto.chat_dto import (
    CreateThreadRequest as ServiceCreateThreadRequest,
)
from ...application.dto.chat_dto import SendMessageRequest as ServiceSendMessageRequest
from ...application.services.chat_service import ChatService
from ...application.services.dspy_react_agent import DSPyReactAgent
from ...infrastructure.database.repositories import (
    SQLAlchemyChatMessageRepository,
    SQLAlchemyChatThreadRepository,
)
from ..schemas.requests import CreateThreadRequest, SendMessageRequest
from ..schemas.responses import MessageResponse, ThreadResponse
from .dependencies import get_database_session

router = APIRouter(prefix="/api/threads", tags=["chat"])


def get_chat_service(
    session: AsyncSession = Depends(get_database_session),
) -> ChatService:
    thread_repo = SQLAlchemyChatThreadRepository(session)
    message_repo = SQLAlchemyChatMessageRepository(session)
    bot_service = DSPyReactAgent()
    return ChatService(thread_repo, message_repo, bot_service)


@router.post(
    "/", 
    response_model=ThreadResponse,
    summary="Create a new chat thread",
    description="""
    Create a new chat thread for a user. A thread is a conversation container
    that holds multiple messages between a user and the AI assistant.
    
    **Example Usage:**
    - Create a thread for general discussion
    - Start a new support conversation
    - Begin a project planning session
    
    **Try It Out:**
    Use these example UUIDs that would exist in a seeded database:
    - User ID: `123e4567-e89b-12d3-a456-426614174000`
    - User ID: `550e8400-e29b-41d4-a716-446655440000`
    """,
    response_description="The created thread with its unique ID and metadata"
)
async def create_thread(
    request: CreateThreadRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ThreadResponse:
    try:
        service_request = ServiceCreateThreadRequest(
            user_id=request.user_id,
            title=request.title,
        )
        thread = await chat_service.create_thread(service_request)
        return ThreadResponse(
            thread_id=thread.thread_id,
            user_id=thread.user_id,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            status=thread.status,
            title=thread.title,
            summary=thread.summary,
            metadata=thread.metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{thread_id}", 
    response_model=ThreadResponse,
    summary="Get a thread by ID",
    description="""
    Retrieve detailed information about a specific chat thread.
    
    **Try It Out:**
    Use these example Thread IDs that would exist in a seeded database:
    - `123e4567-e89b-12d3-a456-426614174000`
    - `234e5678-f89c-23d4-b567-537725285111`
    """,
    response_description="Thread information including metadata and status"
)
async def get_thread(
    thread_id: UUID,
    chat_service: ChatService = Depends(get_chat_service),
) -> ThreadResponse:
    thread = await chat_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )

    return ThreadResponse(
        thread_id=thread.thread_id,
        user_id=thread.user_id,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        status=thread.status,
        title=thread.title,
        summary=thread.summary,
        metadata=thread.metadata,
    )


@router.get(
    "/user/{user_id}", 
    response_model=list[ThreadResponse],
    summary="Get all threads for a user",
    description="""
    Retrieve all chat threads created by a specific user.
    
    **Try It Out:**
    Use these example User IDs that would exist in a seeded database:
    - `123e4567-e89b-12d3-a456-426614174000` (has 3 threads)
    - `550e8400-e29b-41d4-a716-446655440000` (has 2 threads)
    """,
    response_description="List of all threads for the specified user"
)
async def get_user_threads(
    user_id: UUID,
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ThreadResponse]:
    threads = await chat_service.get_user_threads(user_id)
    return [
        ThreadResponse(
            thread_id=thread.thread_id,
            user_id=thread.user_id,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            status=thread.status,
            title=thread.title,
            summary=thread.summary,
            metadata=thread.metadata,
        )
        for thread in threads
    ]


@router.post(
    "/{thread_id}/messages", 
    response_model=list[MessageResponse],
    summary="Send a message to a thread",
    description="""
    Send a message to a chat thread and get an AI assistant response.
    
    This endpoint processes the user message through our advanced DSPy REACT agent,
    which can use various tools like calculators, web search, weather APIs, and more.
    
    **Example Messages to Try:**
    - `"Hello! How can you help me today?"` - General greeting
    - `"What is 25 * 18 + 42?"` - Calculator test
    - `"What's the weather like in San Francisco?"` - Weather API test
    - `"Search for the latest AI news"` - Web search test
    - `"Explain how machine learning works"` - Knowledge test
    
    **Try It Out:**
    Use these example values that would exist in a seeded database:
    - Thread ID: `123e4567-e89b-12d3-a456-426614174000`
    - User ID: `550e8400-e29b-41d4-a716-446655440000`
    """,
    response_description="List containing both the user message and AI assistant response"
)
async def send_message(
    thread_id: UUID,
    user_id: UUID,
    request: SendMessageRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> list[MessageResponse]:
    try:
        service_request = ServiceSendMessageRequest(
            content=request.content,
            message_type=request.message_type,
        )
        messages = await chat_service.send_message(thread_id, user_id, service_request)
        return [
            MessageResponse(
                message_id=message.message_id,
                thread_id=message.thread_id,
                user_id=message.user_id,
                role=message.role,
                content=message.content,
                type=message.type,
                metadata=message.metadata,
                created_at=message.created_at,
            )
            for message in messages
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{thread_id}/messages", 
    response_model=list[MessageResponse],
    summary="Get all messages from a thread",
    description="""
    Retrieve all messages from a specific chat thread, ordered chronologically.
    
    This includes both user messages and AI assistant responses, showing
    the complete conversation history.
    
    **Try It Out:**
    Use these example Thread IDs that would exist in a seeded database:
    - `123e4567-e89b-12d3-a456-426614174000` (has 8 messages)
    - `234e5678-f89c-23d4-b567-537725285111` (has 12 messages)
    """,
    response_description="List of all messages in the thread, ordered by creation time"
)
async def get_thread_messages(
    thread_id: UUID,
    chat_service: ChatService = Depends(get_chat_service),
) -> list[MessageResponse]:
    messages = await chat_service.get_thread_messages(thread_id)
    return [
        MessageResponse(
            message_id=message.message_id,
            thread_id=message.thread_id,
            user_id=message.user_id,
            role=message.role,
            content=message.content,
            type=message.type,
            metadata=message.metadata,
            created_at=message.created_at,
        )
        for message in messages
    ]
