import json
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from ...application.dto.chat_dto import SendMessageRequest
from ...application.services.chat_service import ChatService
from ...application.services.dspy_react_agent import DSPyReactAgent
from ...application.services.file_processor import FileProcessor
from ...infrastructure.config.database import Database, DatabaseConfig
from ...infrastructure.database.repositories import (
    SQLAlchemyChatMessageRepository,
    SQLAlchemyChatThreadRepository,
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, set[WebSocket]] = {}

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

            # Handle file upload
            if message_data.get("type") == "file":
                try:
                    # Extract file data from message
                    file_data = message_data.get("file_data")  # base64 encoded
                    filename = message_data.get("filename")

                    if file_data and filename:
                        # Decode base64 file data
                        import base64

                        file_content = base64.b64decode(file_data)

                        # Process the file
                        result = FileProcessor.process_file(file_content, filename)

                        if result["success"]:
                            # Create a message with file analysis
                            content = f"📁 **File Upload: {filename}**\n\n{result['summary']}\n\n{result['content'][:500]}..."
                            if len(result["content"]) > 500:
                                content += f"\n\n*(Showing first 500 characters of {len(result['content'])} total)*"

                            # Send as regular message to be processed by AI
                            async for session in database.get_session():
                                thread_repo = SQLAlchemyChatThreadRepository(session)
                                message_repo = SQLAlchemyChatMessageRepository(session)
                                bot_service = DSPyReactAgent()
                                chat_service = ChatService(
                                    thread_repo, message_repo, bot_service
                                )

                                request = SendMessageRequest(
                                    content=content,
                                    message_type="file",
                                )

                                messages = await chat_service.send_message(
                                    thread_id, user_id, request
                                )

                                # Broadcast file processing result like a regular message
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
                                    await manager.broadcast_to_thread(
                                        thread_id, response
                                    )

                        else:
                            # Send error message
                            error_response = {
                                "type": "error",
                                "error": f"File processing failed: {result['error']}",
                            }
                            await websocket.send_text(json.dumps(error_response))

                except Exception as e:
                    error_response = {
                        "type": "error",
                        "error": f"File upload error: {str(e)}",
                    }
                    await websocket.send_text(json.dumps(error_response))

            # Handle incoming message
            elif message_data.get("type") == "message":
                try:
                    async for session in database.get_session():
                        thread_repo = SQLAlchemyChatThreadRepository(session)
                        message_repo = SQLAlchemyChatMessageRepository(session)
                        bot_service = DSPyReactAgent()
                        chat_service = ChatService(
                            thread_repo, message_repo, bot_service
                        )

                        request = SendMessageRequest(
                            content=message_data["content"],
                            message_type=message_data.get("message_type", "text"),
                        )

                        # Handle streaming response for user message
                        messages = await chat_service.send_message(
                            thread_id, user_id, request
                        )

                        # First broadcast the user message
                        user_msg = messages[
                            0
                        ]  # First message is always the user message
                        user_response = {
                            "type": "message",
                            "message_id": str(user_msg.message_id),
                            "thread_id": str(user_msg.thread_id),
                            "user_id": str(user_msg.user_id),
                            "role": user_msg.role.value,
                            "content": user_msg.content,
                            "message_type": user_msg.type,
                            "metadata": user_msg.metadata,
                            "created_at": user_msg.created_at.isoformat(),
                        }
                        await manager.broadcast_to_thread(thread_id, user_response)

                        # Now handle streaming AI response if there is one
                        if len(messages) > 1:
                            ai_msg = messages[1]  # Second message is the AI response

                            # Send streaming start signal
                            stream_start = {
                                "type": "stream_start",
                                "message_id": str(ai_msg.message_id),
                                "thread_id": str(ai_msg.thread_id),
                                "user_id": str(ai_msg.user_id),
                                "role": ai_msg.role.value,
                                "created_at": ai_msg.created_at.isoformat(),
                            }
                            await manager.broadcast_to_thread(thread_id, stream_start)

                            # Stream the response chunks
                            from ...domain.entities.chat_message import ChatMessage
                            from ...domain.value_objects.message_role import MessageRole

                            user_chat_msg = ChatMessage(
                                message_id=user_msg.message_id,
                                thread_id=user_msg.thread_id,
                                user_id=user_msg.user_id,
                                role=MessageRole.USER,
                                content=user_msg.content,
                                type=user_msg.type,
                                metadata=user_msg.metadata or {},
                                created_at=user_msg.created_at,
                            )

                            async for chunk in bot_service.generate_streaming_response(
                                user_chat_msg, thread_id
                            ):
                                stream_chunk = {
                                    "type": "stream_chunk",
                                    "message_id": str(ai_msg.message_id),
                                    "content": chunk,
                                }
                                await manager.broadcast_to_thread(
                                    thread_id, stream_chunk
                                )

                            # Send streaming end signal
                            stream_end = {
                                "type": "stream_end",
                                "message_id": str(ai_msg.message_id),
                                "final_content": ai_msg.content,
                            }
                            await manager.broadcast_to_thread(thread_id, stream_end)
                        else:
                            # Fallback: send all messages normally if streaming not available
                            for message in messages[1:]:
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
