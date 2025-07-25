import os
from uuid import UUID

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .infrastructure.container.container import Container
from .infrastructure.middleware.logging_middleware import RichLoggingMiddleware
from .presentation.api.chat_routes import router as chat_router
from .presentation.api.export_routes import router as export_router
from .presentation.api.visualization_routes import router as visualization_router
from .presentation.api.webhook_routes import router as webhook_router
from .presentation.websocket.chat_websocket import websocket_endpoint


def create_app() -> FastAPI:
    # Initialize container
    Container()

    app = FastAPI(
        title="🤖 Sample Chat App API",
        description="""
        A modern Python chat application with FastAPI and WebSocket support.

        ## Features

        * **Advanced AI Agent**: DSPy REACT agent with sophisticated reasoning
        * **Tool Integration**: Calculator, web search, weather APIs, file processing
        * **Real-time Chat**: WebSocket support for instant messaging
        * **Memory System**: BM25-based conversation memory and context
        * **Streaming Responses**: Real-time typing effects

        ## Getting Started

        1. **Create a Thread**: Start by creating a new chat thread
        2. **Send Messages**: Use the message endpoint to chat with the AI
        3. **Explore Tools**: Try calculator, weather, or search queries

        ## Example Interactions

        * **Calculator**: "What is 25 * 18 + 42?"
        * **Weather**: "What's the weather like in San Francisco?"
        * **Search**: "Search for the latest AI news"
        * **General**: "Explain how machine learning works"

        ## Try It Out

        Use these example UUIDs in the interactive documentation below:
        * **User ID**: `123e4567-e89b-12d3-a456-426614174000`
        * **Thread ID**: `123e4567-e89b-12d3-a456-426614174000`

        ---

        **💡 Tip**: All endpoints include detailed examples in their "Try it out" sections.
        """,
        version="0.1.0",
        contact={
            "name": "Sample Chat App",
            "url": "https://github.com/EvanOman/chatbot_skeleton",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        tags_metadata=[
            {
                "name": "chat",
                "description": "Chat thread and message operations. Create threads, send messages, and interact with the AI assistant.",
            },
            {
                "name": "visualization",
                "description": "Interactive visualization features. Visualize chat threads as conversation trees and view thread overviews.",
            },
            {
                "name": "export",
                "description": "Conversation export features. Export chat threads in multiple formats (JSON, CSV, Markdown, HTML).",
            },
            {
                "name": "webhooks",
                "description": "Webhook management and external integrations. Configure webhooks to receive notifications about chat events.",
            },
        ],
    )

    # Add rich logging middleware for development
    development_mode = os.getenv("ENVIRONMENT", "development").lower() == "development"
    if development_mode:
        app.add_middleware(RichLoggingMiddleware, enable_logging=True)

    # Include routers
    app.include_router(chat_router)
    app.include_router(export_router)
    app.include_router(visualization_router)
    app.include_router(webhook_router)

    # WebSocket endpoint
    @app.websocket("/ws/{thread_id}/{user_id}")
    async def websocket_route(websocket: WebSocket, thread_id: UUID, user_id: UUID) -> None:
        await websocket_endpoint(websocket, thread_id, user_id)

    # Serve static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Configure Jinja2 templates
    templates = Jinja2Templates(directory="templates")

    # Root endpoint - Developer Dashboard in dev mode, Chat interface in production
    @app.get("/", response_class=HTMLResponse)
    async def get_root_interface(request: Request) -> HTMLResponse:
        if development_mode:
            return await get_developer_dashboard(request, templates)
        else:
            return await get_chat_interface(request)

    # Chat interface endpoint
    @app.get("/chat", response_class=HTMLResponse)
    async def get_chat_interface(request: Request) -> HTMLResponse:
        context = {"request": request, "app_name": "Sample Chat App"}
        return templates.TemplateResponse("chat/interface.html", context)

    async def get_developer_dashboard(request: Request, templates: Jinja2Templates) -> HTMLResponse:
        """Developer dashboard with links to all development tools."""
        # TODO: Get database stats from the database
        # For now, using placeholder values
        thread_count = "N/A"
        message_count = "N/A"

        context = {
            "request": request,
            "thread_count": thread_count,
            "message_count": message_count,
            "app_name": "Sample Chat App",
        }
        return templates.TemplateResponse("dashboard/index.html", context)

    return app


app = create_app()
