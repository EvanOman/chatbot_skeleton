import json
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from ...application.services.chat_service import ChatService
from ...application.services.echo_bot_service import EchoBotService
from ...application.dto.chat_dto import SendMessageRequest
from ...infrastructure.database.repositories import SQLAlchemyChatThreadRepository, SQLAlchemyChatMessageRepository
from ...infrastructure.config.database import DatabaseConfig, Database


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, thread_id: UUID):
        await websocket.accept()
        if thread_id not in self.active_connections:
            self.active_connections[thread_id] = set()
        self.active_connections[thread_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, thread_id: UUID):
        if thread_id in self.active_connections:
            self.active_connections[thread_id].discard(websocket)
            if not self.active_connections[thread_id]:
                del self.active_connections[thread_id]
    
    async def broadcast_to_thread(self, thread_id: UUID, message: dict):
        if thread_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[thread_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[thread_id].discard(connection)


manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    thread_id: UUID,
    user_id: UUID,
):
    await manager.connect(websocket, thread_id)
    
    # Setup database and services
    db_config = DatabaseConfig.from_env()
    database = Database(db_config)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle incoming message
            if message_data.get("type") == "message":
                try:
                    async for session in database.get_session():
                        thread_repo = SQLAlchemyChatThreadRepository(session)
                        message_repo = SQLAlchemyChatMessageRepository(session)
                        bot_service = EchoBotService()
                        chat_service = ChatService(thread_repo, message_repo, bot_service)
                        
                        request = SendMessageRequest(
                            content=message_data["content"],
                            message_type=message_data.get("message_type", "text"),
                        )
                        
                        messages = await chat_service.send_message(thread_id, user_id, request)
                        
                        # Broadcast messages to all connections in this thread
                        for message in messages:
                            response = {
                                "type": "message",
                                "message_id": str(message.message_id),
                                "thread_id": str(message.thread_id),
                                "user_id": str(message.user_id),
                                "role": message.role.value,
                                "content": message.content,
                                "message_type": message.type,
                                "metadata": message.metadata,
                                "created_at": message.created_at.isoformat(),
                            }
                            await manager.broadcast_to_thread(thread_id, response)
                        break
                
                except Exception as e:
                    error_response = {
                        "type": "error",
                        "error": str(e),
                    }
                    await websocket.send_text(json.dumps(error_response))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, thread_id)