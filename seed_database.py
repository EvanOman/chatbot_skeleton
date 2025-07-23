#!/usr/bin/env python3
"""
Database seeding script for Sample Chat App.

This script creates example data that matches the UUIDs referenced in the API documentation,
making the "Try It Out" examples in Swagger UI work seamlessly.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.config.database import Database, DatabaseConfig
from src.infrastructure.database.models import ChatThreadModel, ChatMessageModel
from src.domain.value_objects.thread_status import ThreadStatus
from src.domain.value_objects.message_role import MessageRole


async def seed_database():
    """Seed the database with example data for API documentation."""
    
    # Initialize database
    config = DatabaseConfig.from_env()
    database = Database(config)
    
    async with database.get_session() as session:
        # Example users and threads referenced in API docs
        example_users = [
            uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
            uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
            uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
        ]
        
        example_threads = [
            {
                "thread_id": uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
                "user_id": example_users[0],
                "title": "General Discussion",
                "summary": "Discussion about machine learning concepts",
            },
            {
                "thread_id": uuid.UUID("234e5678-f89c-23d4-b567-537725285111"),
                "user_id": example_users[1],
                "title": "Tech Support Request",
                "summary": "Help with API integration",
            },
            {
                "thread_id": uuid.UUID("345e6789-089d-34e5-c678-648836396222"),
                "user_id": example_users[0],
                "title": "Project Planning",
                "summary": "Planning chat application features",
            },
        ]
        
        # Create threads
        created_threads = []
        for thread_data in example_threads:
            thread = ChatThreadModel(
                thread_id=thread_data["thread_id"],
                user_id=thread_data["user_id"],
                status=ThreadStatus.ACTIVE.value,
                title=thread_data["title"],
                summary=thread_data["summary"],
                metadata_json={"seeded": True, "priority": "high", "category": "support"},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(thread)
            created_threads.append(thread)
        
        # Create example messages for the first thread
        example_messages = [
            {
                "message_id": uuid.UUID("789e0123-e45b-67d8-a901-234567890abc"),
                "thread_id": example_threads[0]["thread_id"],
                "user_id": example_threads[0]["user_id"], 
                "role": MessageRole.USER,
                "content": "Hello! How can you help me today?",
                "type": "text",
                "metadata": {},
            },
            {
                "message_id": uuid.UUID("def1234-e45b-67d8-a901-567890abcdef"),
                "thread_id": example_threads[0]["thread_id"],
                "user_id": example_threads[0]["user_id"],
                "role": MessageRole.ASSISTANT,
                "content": "Hello! I'm an AI assistant with various capabilities. I can help you with calculations, answer questions, search for information, check the weather, process files, and much more. What would you like to explore?",
                "type": "text",
                "metadata": {"processed_by": "dspy_agent", "tools_available": ["calculator", "search", "weather"]},
            },
            {
                "message_id": uuid.UUID("abc5678-e45b-67d8-a901-9012345678ef"),
                "thread_id": example_threads[0]["thread_id"],
                "user_id": example_threads[0]["user_id"],
                "role": MessageRole.USER,
                "content": "What is 25 * 18 + 42?",
                "type": "text",
                "metadata": {},
            },
            {
                "message_id": uuid.UUID("fed9876-e45b-67d8-a901-543210987abc"),
                "thread_id": example_threads[0]["thread_id"],
                "user_id": example_threads[0]["user_id"],
                "role": MessageRole.ASSISTANT,
                "content": "I calculated: 25 * 18 + 42 = 492",
                "type": "text",
                "metadata": {"processed_by": "dspy_agent", "tools_used": ["calculator"]},
            },
        ]
        
        # Create messages
        for i, msg_data in enumerate(example_messages):
            message = ChatMessageModel(
                message_id=msg_data["message_id"],
                thread_id=msg_data["thread_id"],
                user_id=msg_data["user_id"],
                role=msg_data["role"].value,
                content=msg_data["content"],
                type=msg_data["type"],
                metadata_json=msg_data["metadata"],
                created_at=datetime.now(timezone.utc),
            )
            session.add(message)
        
        # Additional messages for the second thread
        tech_support_messages = [
            {
                "message_id": uuid.UUID("111a1111-e45b-67d8-a901-111111111111"),
                "thread_id": example_threads[1]["thread_id"],
                "user_id": example_threads[1]["user_id"],
                "role": MessageRole.USER,
                "content": "I'm having trouble integrating your API. Can you help?",
                "type": "text",
                "metadata": {},
            },
            {
                "message_id": uuid.UUID("222b2222-e45b-67d8-a901-222222222222"),
                "thread_id": example_threads[1]["thread_id"],
                "user_id": example_threads[1]["user_id"],
                "role": MessageRole.ASSISTANT,
                "content": "I'd be happy to help with API integration! What specific issue are you encountering? Are you getting error messages, or is it a question about authentication, endpoints, or request formatting?",
                "type": "text",
                "metadata": {"processed_by": "dspy_agent", "category": "support"},
            },
        ]
        
        for msg_data in tech_support_messages:
            message = ChatMessageModel(
                message_id=msg_data["message_id"],
                thread_id=msg_data["thread_id"],
                user_id=msg_data["user_id"],
                role=msg_data["role"].value,
                content=msg_data["content"],
                type=msg_data["type"],
                metadata_json=msg_data["metadata"],
                created_at=datetime.now(timezone.utc),
            )
            session.add(message)
        
        # Commit all changes
        await session.commit()
        
        print("✅ Database seeded successfully!")
        print(f"📊 Created {len(example_threads)} threads")
        print(f"💬 Created {len(example_messages) + len(tech_support_messages)} messages")
        print(f"👥 Using {len(example_users)} example users")
        print("\n🔗 Try these in the API docs at http://localhost:8000/docs:")
        print(f"   • User ID: {example_users[0]}")
        print(f"   • Thread ID: {example_threads[0]['thread_id']}")
        print("   • Test message: 'What is 15 * 23?'")


if __name__ == "__main__":
    print("🌱 Seeding database with example data...")
    asyncio.run(seed_database())