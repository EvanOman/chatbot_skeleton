from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.services.chat_service import ChatService
from ...application.services.dspy_react_agent import DSPyReactAgent
from ...application.dto.chat_dto import CreateThreadRequest as ServiceCreateThreadRequest
from ...application.dto.chat_dto import SendMessageRequest as ServiceSendMessageRequest
from ...infrastructure.database.repositories import SQLAlchemyChatThreadRepository, SQLAlchemyChatMessageRepository
from ..schemas.requests import CreateThreadRequest, SendMessageRequest
from ..schemas.responses import ThreadResponse, MessageResponse, ErrorResponse
from .dependencies import get_database_session


router = APIRouter(prefix="/api/threads", tags=["chat"])


def get_chat_service(session: AsyncSession = Depends(get_database_session)) -> ChatService:
    thread_repo = SQLAlchemyChatThreadRepository(session)
    message_repo = SQLAlchemyChatMessageRepository(session)
    bot_service = DSPyReactAgent()
    return ChatService(thread_repo, message_repo, bot_service)


@router.post("/", response_model=ThreadResponse)
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: UUID,
    chat_service: ChatService = Depends(get_chat_service),
) -> ThreadResponse:
    thread = await chat_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
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


@router.get("/user/{user_id}", response_model=List[ThreadResponse])
async def get_user_threads(
    user_id: UUID,
    chat_service: ChatService = Depends(get_chat_service),
) -> List[ThreadResponse]:
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


@router.post("/{thread_id}/messages", response_model=List[MessageResponse])
async def send_message(
    thread_id: UUID,
    user_id: UUID,
    request: SendMessageRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> List[MessageResponse]:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{thread_id}/messages", response_model=List[MessageResponse])
async def get_thread_messages(
    thread_id: UUID,
    chat_service: ChatService = Depends(get_chat_service),
) -> List[MessageResponse]:
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