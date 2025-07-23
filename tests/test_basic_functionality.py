import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from src.main import app
from src.domain.entities.chat_thread import ChatThread
from src.domain.entities.chat_message import ChatMessage
from src.domain.value_objects.message_role import MessageRole
from src.domain.value_objects.thread_status import ThreadStatus
from src.application.services.echo_bot_service import EchoBotService


def test_app_imports():
    """Test that the main app can be imported without errors."""
    assert app is not None
    assert app.title == "Sample Chat App"


def test_domain_entities():
    """Test domain entity creation and methods."""
    user_id = uuid4()
    
    # Test ChatThread
    thread = ChatThread(user_id=user_id, title="Test Thread")
    assert thread.user_id == user_id
    assert thread.title == "Test Thread"
    assert thread.status == ThreadStatus.ACTIVE
    
    thread.archive()
    assert thread.status == ThreadStatus.ARCHIVED
    
    thread.restore()
    assert thread.status == ThreadStatus.ACTIVE
    
    # Test ChatMessage
    message = ChatMessage(
        thread_id=thread.thread_id,
        user_id=user_id,
        role=MessageRole.USER,
        content="Test message"
    )
    assert message.thread_id == thread.thread_id
    assert message.user_id == user_id
    assert message.role == MessageRole.USER
    assert message.content == "Test message"
    assert message.is_from_user()
    assert not message.is_from_ai()


@pytest.mark.asyncio
async def test_echo_bot_service():
    """Test the EchoBot service."""
    bot = EchoBotService()
    user_id = uuid4()
    thread_id = uuid4()
    
    message = ChatMessage(
        thread_id=thread_id,
        user_id=user_id,
        role=MessageRole.USER,
        content="Hello, bot!"
    )
    
    response = await bot.generate_response(message, thread_id)
    assert response == "Echo: Hello, bot!"


def test_api_endpoints_with_test_client():
    """Test API endpoints using TestClient for synchronous testing."""
    client = TestClient(app)
    
    # Test root endpoint returns HTML
    response = client.get("/")
    assert response.status_code == 200
    assert "Sample Chat App" in response.text
    
    # Test OpenAPI docs are available
    response = client.get("/docs")
    assert response.status_code == 200


def test_value_objects():
    """Test value objects."""
    # Test MessageRole
    assert MessageRole.USER == "user"
    assert MessageRole.AI == "ai"
    assert MessageRole.SYSTEM == "system"
    
    # Test ThreadStatus
    assert ThreadStatus.ACTIVE == "active"
    assert ThreadStatus.ARCHIVED == "archived"
    assert ThreadStatus.DELETED == "deleted"


if __name__ == "__main__":
    pytest.main([__file__])