"""
Performance and load testing for the Sample Chat App.

These tests verify that the application performs well under various conditions:
- Response time benchmarks
- Memory usage validation
- Concurrent request handling
- Database query performance
- WebSocket connection limits

Run with: pytest tests/test_performance.py -v
"""

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.dspy_react_agent import DSPyReactAgent

# Database tests now run properly in CI with fixed asyncpg configuration


@pytest.mark.slow
class TestResponseTimes:
    """Test API response time benchmarks."""

    @pytest.mark.asyncio
    async def test_api_response_times(
        self, async_client: AsyncClient, performance_timer, test_user_id: UUID
    ):
        """Test that API endpoints respond within acceptable time limits."""

        # Test thread creation time
        performance_timer.start()
        response = await async_client.post(
            "/api/threads/",
            json={"user_id": str(test_user_id), "title": "Performance Test Thread"},
        )
        performance_timer.stop()

        assert response.status_code == 200
        performance_timer.assert_under(2.0)  # Should create thread in under 2 seconds

        thread_id = response.json()["thread_id"]

        # Test message sending time
        performance_timer.start()
        response = await async_client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "Test message", "message_type": "text"},
            params={"user_id": str(test_user_id)},
        )
        performance_timer.stop()

        assert response.status_code == 200
        performance_timer.assert_under(5.0)  # Should process message in under 5 seconds

        # Test message retrieval time
        performance_timer.start()
        response = await async_client.get(f"/api/threads/{thread_id}/messages")
        performance_timer.stop()

        assert response.status_code == 200
        performance_timer.assert_under(
            1.0
        )  # Should retrieve messages in under 1 second

    def test_static_endpoint_performance(
        self, test_client: TestClient, performance_timer
    ):
        """Test performance of static endpoints."""
        endpoints = ["/", "/docs", "/redoc"]

        for endpoint in endpoints:
            performance_timer.start()
            response = test_client.get(endpoint)
            performance_timer.stop()

            assert response.status_code == 200
            performance_timer.assert_under(1.0)  # Static content should be fast

    @pytest.mark.asyncio
    async def test_export_performance(
        self, async_client: AsyncClient, performance_timer
    ):
        """Test export functionality performance."""
        # Create a thread with multiple messages first
        thread_response = await async_client.post(
            "/api/threads/",
            json={"user_id": str(uuid4()), "title": "Export Performance Test"},
        )
        thread_id = thread_response.json()["thread_id"]

        # Add several messages
        for i in range(10):
            await async_client.post(
                f"/api/threads/{thread_id}/messages",
                json={"content": f"Message {i+1}", "message_type": "text"},
                params={"user_id": str(uuid4())},
            )

        # Test JSON export performance
        performance_timer.start()
        response = await async_client.get(
            f"/api/export/thread/{thread_id}", params={"format": "json"}
        )
        performance_timer.stop()

        assert response.status_code == 200
        performance_timer.assert_under(3.0)  # Export should complete in under 3 seconds


@pytest.mark.slow
class TestConcurrentRequests:
    """Test handling of concurrent requests."""

    @pytest.mark.asyncio
    async def test_concurrent_thread_creation(self, async_client: AsyncClient):
        """Test creating multiple threads concurrently."""

        async def create_thread(user_id: UUID):
            response = await async_client.post(
                "/api/threads/",
                json={
                    "user_id": str(user_id),
                    "title": f"Concurrent Test Thread {user_id}",
                },
            )
            return response.status_code == 200

        # Create 10 threads concurrently
        tasks = [create_thread(uuid4()) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All requests should succeed
        assert all(results), "Some concurrent thread creations failed"

    @pytest.mark.asyncio
    async def test_concurrent_message_sending(
        self, async_client: AsyncClient, test_user_id: UUID
    ):
        """Test sending messages to the same thread concurrently."""
        # Create a thread first
        thread_response = await async_client.post(
            "/api/threads/",
            json={"user_id": str(test_user_id), "title": "Concurrent Messages Test"},
        )
        thread_id = thread_response.json()["thread_id"]

        async def send_message(message_num: int):
            response = await async_client.post(
                f"/api/threads/{thread_id}/messages",
                json={
                    "content": f"Concurrent message {message_num}",
                    "message_type": "text",
                },
                params={"user_id": str(test_user_id)},
            )
            return response.status_code == 200

        # Send 5 messages concurrently
        tasks = [send_message(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert all(results), "Some concurrent message sends failed"

    def test_concurrent_static_requests(self, test_client: TestClient):
        """Test concurrent requests to static endpoints."""

        def make_request():
            response = test_client.get("/")
            return response.status_code == 200

        # Make 20 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]

        assert all(results), "Some concurrent static requests failed"


@pytest.mark.slow
class TestAgentPerformance:
    """Test AI agent performance characteristics."""

    @pytest.mark.asyncio
    async def test_agent_response_time(self, performance_timer):
        """Test agent response generation time."""
        agent = DSPyReactAgent()

        from src.domain.entities.chat_message import ChatMessage
        from src.domain.value_objects.message_role import MessageRole

        message = ChatMessage(
            thread_id=uuid4(),
            user_id=uuid4(),
            role=MessageRole.USER,
            content="What is 25 * 18?",
        )

        performance_timer.start()
        response = await agent.generate_response(message, message.thread_id)
        performance_timer.stop()

        assert response is not None
        assert len(response) > 0
        performance_timer.assert_under(10.0)  # Agent should respond in under 10 seconds

    @pytest.mark.asyncio
    async def test_calculator_performance(self, performance_timer):
        """Test calculator tool performance."""
        agent = DSPyReactAgent()

        test_calculations = ["2 + 2", "100 * 50", "sqrt(144)", "2 ** 10", "sin(30)"]

        for calc in test_calculations:
            performance_timer.start()
            result = agent.tools["calculator"].calculate(calc)
            performance_timer.stop()

            assert result is not None
            performance_timer.assert_under(1.0)  # Calculations should be near-instant

    @pytest.mark.asyncio
    async def test_memory_system_performance(self, performance_timer):
        """Test memory system performance with large datasets."""
        agent = DSPyReactAgent()

        # Store many memories
        memories = [
            f"This is test memory number {i} with various content about topic {i % 5}"
            for i in range(100)
        ]

        # Test storage performance
        performance_timer.start()
        for memory in memories:
            agent.memory_tool.store_memory(memory)
        performance_timer.stop()

        performance_timer.assert_under(
            5.0
        )  # Should store 100 memories in under 5 seconds

        # Test search performance
        performance_timer.start()
        result = agent.memory_tool.search_memory("topic 3")
        performance_timer.stop()

        assert "topic 3" in result.lower()
        performance_timer.assert_under(
            2.0
        )  # Search should be fast even with many memories


@pytest.mark.slow
class TestDatabasePerformance:
    """Test database operation performance."""

    @pytest.mark.asyncio
    async def test_bulk_thread_creation(
        self, db_session: AsyncSession, performance_timer
    ):
        """Test performance of creating many threads."""
        from src.infrastructure.database.models import ChatThreadModel

        user_id = uuid4()
        threads = [
            ChatThreadModel(
                thread_id=uuid4(),
                user_id=user_id,
                title=f"Bulk Test Thread {i}",
                status="active",
            )
            for i in range(50)
        ]

        performance_timer.start()
        db_session.add_all(threads)
        await db_session.commit()
        performance_timer.stop()

        performance_timer.assert_under(
            5.0
        )  # Should create 50 threads in under 5 seconds

    @pytest.mark.asyncio
    async def test_bulk_message_creation(
        self, db_session: AsyncSession, performance_timer
    ):
        """Test performance of creating many messages."""
        from src.infrastructure.database.models import ChatMessageModel, ChatThreadModel

        # Create a thread first
        user_id = uuid4()
        thread = ChatThreadModel(
            thread_id=uuid4(),
            user_id=user_id,
            title="Bulk Messages Test",
            status="active",
        )
        db_session.add(thread)
        await db_session.commit()

        # Create many messages
        messages = [
            ChatMessageModel(
                message_id=uuid4(),
                thread_id=thread.thread_id,
                user_id=user_id,
                role="user",
                content=f"Bulk test message {i}",
            )
            for i in range(100)
        ]

        performance_timer.start()
        db_session.add_all(messages)
        await db_session.commit()
        performance_timer.stop()

        performance_timer.assert_under(
            10.0
        )  # Should create 100 messages in under 10 seconds

    @pytest.mark.asyncio
    async def test_message_query_performance(
        self, db_session: AsyncSession, performance_timer
    ):
        """Test performance of querying messages."""
        from sqlalchemy import select

        from src.infrastructure.database.models import ChatMessageModel, ChatThreadModel

        # Create test data
        user_id = uuid4()
        thread = ChatThreadModel(
            thread_id=uuid4(),
            user_id=user_id,
            title="Query Performance Test",
            status="active",
        )
        db_session.add(thread)
        await db_session.commit()

        # Add messages
        messages = [
            ChatMessageModel(
                message_id=uuid4(),
                thread_id=thread.thread_id,
                user_id=user_id,
                role="user" if i % 2 == 0 else "ai",
                content=f"Query test message {i}",
            )
            for i in range(200)
        ]
        db_session.add_all(messages)
        await db_session.commit()

        # Test query performance
        performance_timer.start()
        result = await db_session.execute(
            select(ChatMessageModel)
            .where(ChatMessageModel.thread_id == thread.thread_id)
            .order_by(ChatMessageModel.created_at)
        )
        messages_result = result.scalars().all()
        performance_timer.stop()

        assert len(messages_result) == 200
        performance_timer.assert_under(
            2.0
        )  # Should query 200 messages in under 2 seconds


@pytest.mark.slow
class TestMemoryUsage:
    """Test memory usage characteristics."""

    @pytest.mark.asyncio
    async def test_large_conversation_memory(self, async_client: AsyncClient):
        """Test memory usage with large conversations."""

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create a thread
        thread_response = await async_client.post(
            "/api/threads/",
            json={"user_id": str(uuid4()), "title": "Large Conversation Test"},
        )
        thread_id = thread_response.json()["thread_id"]

        # Send many messages
        for i in range(50):
            await async_client.post(
                f"/api/threads/{thread_id}/messages",
                json={
                    "content": f"This is a longer test message {i} "
                    * 10,  # Make messages longer
                    "message_type": "text",
                },
                params={"user_id": str(uuid4())},
            )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for 50 messages)
        assert (
            memory_increase < 100
        ), f"Memory increased by {memory_increase:.2f}MB, which seems excessive"

    def test_agent_memory_cleanup(self):
        """Test that agent memory is properly managed."""
        import gc

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create and use many agents
        agents = []
        for i in range(10):
            agent = DSPyReactAgent()

            # Use the agent to store memories
            for j in range(20):
                agent.memory_tool.store_memory(f"Agent {i} memory {j} with content")

            agents.append(agent)

        # Clear references and force garbage collection
        del agents
        gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert (
            memory_increase < 200
        ), f"Memory increased by {memory_increase:.2f}MB after agent cleanup"


@pytest.mark.slow
class TestStressTests:
    """Stress tests for system limits."""

    @pytest.mark.asyncio
    async def test_rapid_api_requests(self, async_client: AsyncClient):
        """Test handling of rapid successive API requests."""

        async def rapid_requests():
            tasks = []
            for _ in range(20):
                task = async_client.get("/")
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            return responses

        start_time = time.time()
        responses = await rapid_requests()
        end_time = time.time()

        # All requests should complete
        successful_responses = [
            r for r in responses if hasattr(r, "status_code") and r.status_code == 200
        ]
        assert (
            len(successful_responses) >= 15
        ), "Too many requests failed under rapid load"

        # Should complete in reasonable time
        total_time = end_time - start_time
        assert (
            total_time < 10
        ), f"Rapid requests took {total_time:.2f}s, which is too slow"

    @pytest.mark.asyncio
    async def test_large_message_handling(
        self, async_client: AsyncClient, test_user_id: UUID
    ):
        """Test handling of very large messages."""
        # Create thread
        thread_response = await async_client.post(
            "/api/threads/",
            json={"user_id": str(test_user_id), "title": "Large Message Test"},
        )
        thread_id = thread_response.json()["thread_id"]

        # Create a large message (10KB)
        large_content = "This is a large message. " * 500  # ~12.5KB

        response = await async_client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": large_content, "message_type": "text"},
            params={"user_id": str(test_user_id)},
        )

        assert response.status_code == 200

        # Verify message was stored correctly
        messages_response = await async_client.get(f"/api/threads/{thread_id}/messages")
        messages = messages_response.json()

        user_messages = [m for m in messages if m["role"] == "user"]
        assert len(user_messages) >= 1
        assert (
            len(user_messages[0]["content"]) > 10000
        )  # Verify large content was stored


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "slow"])
