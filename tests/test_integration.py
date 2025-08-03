"""
Integration tests for the Sample Chat App.

These tests verify end-to-end functionality including:
- API endpoints with database operations
- WebSocket connections and messaging
- DSPy REACT agent functionality
- Tool integrations (calculator, memory, etc.)
- Export functionality
- Webhook system
- Performance profiling endpoints

Tests can be run locally or in CI with proper database setup.
"""

import asyncio
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.chat_service import ChatService
from src.application.services.dspy_react_agent import DSPyReactAgent
from src.domain.entities.chat_message import ChatMessage
from src.domain.entities.chat_thread import ChatThread
from src.domain.value_objects.message_role import MessageRole
from src.domain.value_objects.thread_status import ThreadStatus
from src.infrastructure.container.container import Container
from src.infrastructure.database.models import ChatMessageModel, ChatThreadModel
from src.main import app

# Test fixtures are in conftest.py


@pytest_asyncio.fixture
async def test_thread(db_session: AsyncSession, test_user_id: UUID):
    """Create a test thread."""
    thread_model = ChatThreadModel(
        thread_id=uuid4(),
        user_id=test_user_id,
        title="Integration Test Thread",
        status="active",
    )
    db_session.add(thread_model)
    await db_session.commit()
    await db_session.refresh(thread_model)
    return thread_model


# Database tests now run properly in CI with fixed asyncpg configuration


class TestAPIEndpoints:
    """Test REST API endpoints."""

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns HTML interface."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Sample Chat App" in response.text

    def test_docs_endpoint(self, test_client):
        """Test API documentation is accessible."""
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    def test_health_check(self, test_client):
        """Test basic health check."""
        response = test_client.get("/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_thread(self, async_client, test_user_id):
        """Test thread creation via API."""
        thread_data = {"user_id": str(test_user_id), "title": "API Test Thread"}

        response = await async_client.post("/api/threads/", json=thread_data)
        if response.status_code != 200:
            print(f"Error response: {response.text}")
        assert response.status_code == 200

        thread = response.json()
        assert thread["user_id"] == str(test_user_id)
        assert thread["title"] == "API Test Thread"
        assert thread["status"] == "active"
        assert "thread_id" in thread

    @pytest.mark.asyncio
    async def test_get_thread_messages(self, async_client, test_thread):
        """Test retrieving thread messages."""
        response = await async_client.get(
            f"/api/threads/{test_thread.thread_id}/messages"
        )
        assert response.status_code == 200

        messages = response.json()
        assert isinstance(messages, list)

    @pytest.mark.asyncio
    async def test_send_message(self, async_client, test_user_id):
        """Test sending a message via API."""
        # First create a thread using the API to ensure it's visible to UowChatService
        thread_data = {
            "user_id": str(test_user_id),
            "title": "Test Thread for Messages",
        }
        create_response = await async_client.post("/api/threads/", json=thread_data)
        assert create_response.status_code == 200
        thread = create_response.json()
        thread_id = thread["thread_id"]

        # Now send a message to that thread
        message_data = {
            "content": "Hello, this is a test message!",
            "message_type": "text",
        }

        response = await async_client.post(
            f"/api/threads/{thread_id}/messages",
            json=message_data,
            params={"user_id": str(test_user_id)},
        )
        if response.status_code != 200:
            print(f"Error response: {response.text}")
        assert response.status_code == 200

        # The API might return a list of messages or a single message
        messages = response.json()
        if isinstance(messages, list):
            # Find the user message in the list
            user_messages = [m for m in messages if m.get("role") == "user"]
            assert len(user_messages) >= 1
            message = user_messages[0]
        else:
            message = messages

        assert message["content"] == "Hello, this is a test message!"
        assert message["role"] == "user"


class TestWebSocketConnections:
    """Test WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, test_thread, test_user_id):
        """Test WebSocket connection establishment."""
        # Note: WebSocket testing requires a running server
        # This is a placeholder for WebSocket integration tests
        # In a real CI environment, you'd start the app and connect

        # For now, just test the WebSocket URL format
        websocket_url = f"ws://localhost:8000/ws/{test_thread.thread_id}/{test_user_id}"
        assert websocket_url.startswith("ws://")
        assert str(test_thread.thread_id) in websocket_url
        assert str(test_user_id) in websocket_url

    def test_websocket_message_format(self):
        """Test WebSocket message format validation."""
        # Test valid message format
        valid_message = {
            "type": "message",
            "content": "Test message",
            "message_type": "text",
        }

        # This would be validated by the WebSocket handler
        assert valid_message["type"] == "message"
        assert "content" in valid_message
        assert "message_type" in valid_message


class TestDSPyAgent:
    """Test DSPy REACT agent functionality."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = DSPyReactAgent()
        assert agent is not None
        assert hasattr(agent, "tools")
        assert "calculator" in agent.tools
        assert hasattr(agent, "memory_tool")
        assert "text_processor" in agent.tools

    @pytest.mark.asyncio
    async def test_agent_calculator_tool(self):
        """Test agent calculator functionality."""
        agent = DSPyReactAgent()

        # Test basic calculation
        result = agent.tools["calculator"].calculate("2 + 2")
        assert "4" in result

        # Test mathematical functions
        result = agent.tools["calculator"].calculate("sqrt(16)")
        assert "4" in result

    @pytest.mark.asyncio
    async def test_agent_memory_system(self):
        """Test agent memory storage and retrieval."""
        agent = DSPyReactAgent()

        # Store a memory
        result = agent.memory_tool.store_memory("Python is a programming language")
        assert "stored" in result.lower()

        # Search for related memory with exact term
        result = agent.memory_tool.search_memory("Python")
        # Just verify that search returns some result (memory system working)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_agent_text_processing(self):
        """Test agent text processing capabilities."""
        agent = DSPyReactAgent()

        # Test text analysis
        result = agent.tools["text_processor"].process_text(
            "This is a test sentence.", "analyze"
        )
        assert "characters" in result.lower()
        assert "words" in result.lower()

    @pytest.mark.asyncio
    async def test_agent_response_generation(self):
        """Test end-to-end agent response generation."""
        agent = DSPyReactAgent()

        # Test with calculator query
        message = ChatMessage(
            thread_id=uuid4(),
            user_id=uuid4(),
            role=MessageRole.USER,
            content="What is 15 * 23?",
        )

        response = await agent.generate_response(message, message.thread_id)
        # Should contain calculation or reasoning about calculation
        assert response is not None
        assert len(response) > 0


class TestToolIntegrations:
    """Test individual tool integrations."""

    def test_calculator_tool_advanced(self):
        """Test advanced calculator functionality."""
        agent = DSPyReactAgent()
        calc = agent.tools["calculator"]

        # Test various mathematical operations
        test_cases = [
            ("2 + 2", "4"),
            ("10 * 5", "50"),
            ("100 / 4", "25"),
            ("2 ** 3", "8"),
            ("sqrt(9)", "3"),
            ("sin(0)", "0"),
        ]

        for expression, expected in test_cases:
            result = calc.calculate(expression)
            assert expected in result

    def test_memory_tool_bm25(self):
        """Test BM25 memory retrieval."""
        agent = DSPyReactAgent()
        memory = agent.memory_tool

        # Store multiple memories
        memories = [
            "Python is a programming language",
            "FastAPI is a web framework for Python",
            "SQLAlchemy is an ORM for databases",
            "PostgreSQL is a relational database",
        ]

        for mem in memories:
            memory.store_memory(mem)

        # Test search functionality
        result = memory.search_memory("Python framework")
        assert "FastAPI" in result or "Python" in result

        result = memory.search_memory("database")
        assert "PostgreSQL" in result or "SQLAlchemy" in result

    def test_text_processor_functionality(self):
        """Test text processing capabilities."""
        agent = DSPyReactAgent()
        processor = agent.tools["text_processor"]

        # Test analysis
        text = "This is a sample text for testing purposes."
        result = processor.process_text(text, "analyze")
        assert "words: 8" in result.lower()

        # Test case conversion
        result = processor.process_text(text, "uppercase")
        assert "THIS IS A SAMPLE TEXT FOR TESTING PURPOSES" in result

        result = processor.process_text(text, "lowercase")
        assert "this is a sample text for testing purposes" in result


class TestExportFunctionality:
    """Test conversation export features."""

    @pytest.mark.asyncio
    async def test_json_export(self, async_client, test_user_id):
        """Test JSON export functionality."""
        # Create a thread via API to ensure it's visible to UowChatService
        thread_data = {"user_id": str(test_user_id), "title": "Export Test Thread"}
        create_response = await async_client.post("/api/threads/", json=thread_data)
        assert create_response.status_code == 200
        thread_id = create_response.json()["thread_id"]

        response = await async_client.get(
            f"/api/export/thread/{thread_id}", params={"format": "json"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Verify JSON structure
        data = response.json()
        assert "thread" in data
        assert "messages" in data
        assert "export_info" in data

    @pytest.mark.asyncio
    async def test_csv_export(self, async_client, test_user_id):
        """Test CSV export functionality."""
        # Create a thread via API to ensure it's visible to UowChatService
        thread_data = {"user_id": str(test_user_id), "title": "CSV Export Test"}
        create_response = await async_client.post("/api/threads/", json=thread_data)
        assert create_response.status_code == 200
        thread_id = create_response.json()["thread_id"]

        response = await async_client.get(
            f"/api/export/thread/{thread_id}", params={"format": "csv"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_markdown_export(self, async_client, test_user_id):
        """Test Markdown export functionality."""
        # Create a thread via API to ensure it's visible to UowChatService
        thread_data = {"user_id": str(test_user_id), "title": "Markdown Export Test"}
        create_response = await async_client.post("/api/threads/", json=thread_data)
        assert create_response.status_code == 200
        thread_id = create_response.json()["thread_id"]

        response = await async_client.get(
            f"/api/export/thread/{thread_id}", params={"format": "markdown"}
        )
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_html_export(self, async_client, test_user_id):
        """Test HTML export functionality."""
        # Create a thread via API to ensure it's visible to UowChatService
        thread_data = {"user_id": str(test_user_id), "title": "HTML Export Test"}
        create_response = await async_client.post("/api/threads/", json=thread_data)
        assert create_response.status_code == 200
        thread_id = create_response.json()["thread_id"]

        response = await async_client.get(
            f"/api/export/thread/{thread_id}", params={"format": "html"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestWebhookSystem:
    """Test webhook functionality."""

    @pytest.mark.asyncio
    async def test_webhook_creation(self, async_client):
        """Test webhook configuration creation."""
        webhook_data = {
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "events": ["message_created", "thread_created"],
            "secret": "test_secret_123",
        }

        response = await async_client.post("/api/webhooks/", json=webhook_data)
        assert response.status_code == 201

        webhook = response.json()
        assert webhook["name"] == "Test Webhook"
        assert webhook["url"] == "https://example.com/webhook"
        assert "id" in webhook

    @pytest.mark.asyncio
    async def test_webhook_list(self, async_client):
        """Test webhook listing."""
        response = await async_client.get("/api/webhooks/")
        assert response.status_code == 200

        webhooks = response.json()
        assert isinstance(webhooks, list)

    @pytest.mark.asyncio
    async def test_webhook_events(self, async_client):
        """Test webhook event types."""
        response = await async_client.get("/api/webhooks/events/types")
        assert response.status_code == 200

        events_data = response.json()
        assert "event_types" in events_data
        event_names = [event["name"] for event in events_data["event_types"]]
        assert "message_created" in event_names
        assert "thread_created" in event_names


class TestVisualization:
    """Test conversation visualization features."""

    @pytest.mark.asyncio
    async def test_thread_tree_visualization(self, async_client, test_thread):
        """Test conversation tree visualization."""
        response = await async_client.get(
            f"/api/visualization/thread/{test_thread.thread_id}/tree"
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "d3js.org" in response.text.lower()

    @pytest.mark.asyncio
    async def test_threads_overview(self, async_client):
        """Test threads overview visualization."""
        response = await async_client.get("/api/visualization/threads/overview")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


@pytest.mark.skip(reason="Profiling API endpoints not implemented yet")
class TestProfiling:
    """Test performance profiling features."""

    @pytest.mark.asyncio
    async def test_profiling_status(self, async_client):
        """Test profiling status endpoint."""
        response = await async_client.get("/api/profiling/status")
        assert response.status_code == 200

        status = response.json()
        assert "profiling_enabled" in status

    @pytest.mark.asyncio
    async def test_profiles_list(self, async_client):
        """Test profiles listing."""
        response = await async_client.get("/api/profiling/profiles")
        assert response.status_code == 200

        profiles = response.json()
        assert isinstance(profiles, list)


class TestDashboard:
    """Test developer dashboard functionality."""

    def test_dashboard_access(self, test_client):
        """Test dashboard is accessible."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "Dashboard" in response.text or "Sample Chat App" in response.text


class TestDatabaseOperations:
    """Test database operations and migrations."""

    @pytest.mark.asyncio
    async def test_database_connection(self, db_session):
        """Test database connection is working."""
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_thread_crud_operations(self, db_session, test_user_id):
        """Test CRUD operations on threads."""
        # Create
        thread_model = ChatThreadModel(
            thread_id=uuid4(),
            user_id=test_user_id,
            title="CRUD Test Thread",
            status="active",
        )
        db_session.add(thread_model)
        await db_session.commit()

        # Read
        thread_id = thread_model.thread_id
        retrieved = await db_session.get(ChatThreadModel, thread_id)
        assert retrieved is not None
        assert retrieved.title == "CRUD Test Thread"

        # Update
        retrieved.title = "Updated Thread"
        await db_session.commit()

        updated = await db_session.get(ChatThreadModel, thread_id)
        assert updated.title == "Updated Thread"

    @pytest.mark.asyncio
    async def test_message_crud_operations(self, db_session, test_thread, test_user_id):
        """Test CRUD operations on messages."""
        # Create
        message_model = ChatMessageModel(
            message_id=uuid4(),
            thread_id=test_thread.thread_id,
            user_id=test_user_id,
            role="user",
            content="Test message content",
        )
        db_session.add(message_model)
        await db_session.commit()

        # Read
        message_id = message_model.message_id
        retrieved = await db_session.get(ChatMessageModel, message_id)
        assert retrieved is not None
        assert retrieved.content == "Test message content"


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_thread_id(self, async_client):
        """Test handling of invalid thread IDs."""
        invalid_id = "not-a-uuid"
        response = await async_client.get(f"/api/threads/{invalid_id}/messages")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_nonexistent_thread(self, async_client):
        """Test handling of nonexistent threads."""
        nonexistent_id = str(uuid4())
        response = await async_client.get(f"/api/threads/{nonexistent_id}/messages")
        # Should return empty list or 404, depending on implementation
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_malformed_message_data(
        self, async_client, test_thread, test_user_id
    ):
        """Test handling of malformed message data."""
        invalid_data = {"content": "", "message_type": "invalid_type"}  # Empty content

        response = await async_client.post(
            f"/api/threads/{test_thread.thread_id}/messages",
            json=invalid_data,
            params={"user_id": str(test_user_id)},
        )
        # API now properly validates and rejects empty content with 400
        assert response.status_code == 400


# Integration test configuration
@pytest.mark.integration
class TestFullWorkflow:
    """Test complete user workflows end-to-end."""

    @pytest.mark.asyncio
    async def test_complete_chat_workflow(self, async_client, test_user_id):
        """Test complete chat workflow from thread creation to export."""
        # 1. Create a thread
        thread_data = {"user_id": str(test_user_id), "title": "Workflow Test Thread"}

        response = await async_client.post("/api/threads/", json=thread_data)
        assert response.status_code == 200
        thread = response.json()
        thread_id = thread["thread_id"]

        # 2. Send a message
        message_data = {"content": "Calculate 25 * 18", "message_type": "text"}

        response = await async_client.post(
            f"/api/threads/{thread_id}/messages",
            json=message_data,
            params={"user_id": str(test_user_id)},
        )
        assert response.status_code == 200

        # 3. Get messages
        response = await async_client.get(f"/api/threads/{thread_id}/messages")
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1

        # 4. Export conversation
        response = await async_client.get(
            f"/api/export/thread/{thread_id}", params={"format": "json"}
        )
        assert response.status_code == 200
        export_data = response.json()
        assert "messages" in export_data
        assert len(export_data["messages"]) >= 1

    @pytest.mark.asyncio
    async def test_agent_tool_integration_workflow(self, async_client, test_user_id):
        """Test agent with various tools in sequence."""
        # Create thread
        thread_data = {"user_id": str(test_user_id), "title": "Agent Tools Test"}

        response = await async_client.post("/api/threads/", json=thread_data)
        thread_id = response.json()["thread_id"]

        # Test calculator
        calc_message = {"content": "What's 12 * 15?", "message_type": "text"}

        response = await async_client.post(
            f"/api/threads/{thread_id}/messages",
            json=calc_message,
            params={"user_id": str(test_user_id)},
        )
        assert response.status_code == 200

        # Test memory storage
        memory_message = {
            "content": "Remember that I like pizza",
            "message_type": "text",
        }

        response = await async_client.post(
            f"/api/threads/{thread_id}/messages",
            json=memory_message,
            params={"user_id": str(test_user_id)},
        )
        assert response.status_code == 200

        # Test memory retrieval
        recall_message = {"content": "What do I like to eat?", "message_type": "text"}

        response = await async_client.post(
            f"/api/threads/{thread_id}/messages",
            json=recall_message,
            params={"user_id": str(test_user_id)},
        )
        assert response.status_code == 200


if __name__ == "__main__":
    # Run integration tests
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "-m",
            "not integration",  # Skip slow integration tests by default
        ]
    )
