"""Service for generating AI-based thread titles using DSPy."""

from typing import List
from uuid import UUID

import dspy

from ...domain.entities.chat_message import ChatMessage
from ...domain.repositories.chat_message_repository import ChatMessageRepository


class ThreadTitleSignature(dspy.Signature):
    """Generate a concise, descriptive one-line title for a chat thread based on its messages."""
    
    messages: str = dspy.InputField(desc="Recent messages from the chat thread")
    title: str = dspy.OutputField(desc="A concise, descriptive one-line title (max 50 characters)")


class ThreadTitleService:
    """Service for generating AI-powered thread titles."""
    
    def __init__(self, message_repository: ChatMessageRepository):
        self.message_repository = message_repository
        self.title_generator = dspy.Predict(ThreadTitleSignature)
        
    async def generate_title_for_thread(self, thread_id: UUID) -> str:
        """
        Generate an AI-powered title for a thread based on its messages.
        
        Args:
            thread_id: The UUID of the thread to generate a title for
            
        Returns:
            A concise, descriptive title for the thread
        """
        # Get recent messages from the thread (up to 5 for context)
        messages = await self.message_repository.get_by_thread_id(thread_id)
        
        if not messages:
            return "New conversation"
            
        # Take up to the first 3 messages for title generation
        recent_messages = messages[:3]
        
        # Format messages for DSPy processing
        formatted_messages = self._format_messages_for_ai(recent_messages)
        
        # Generate title using DSPy
        try:
            result = self.title_generator(messages=formatted_messages)
            title = result.title.strip()
            
            # Ensure title is not too long and remove any quotes
            title = title.replace('"', '').replace("'", '')
            if len(title) > 50:
                title = title[:47] + "..."
                
            # Fallback if title is empty or too generic
            if not title or title.lower() in ["chat", "conversation", "new", "thread"]:
                return self._generate_fallback_title(recent_messages)
                
            return title
            
        except Exception:
            # Fallback to simple title generation if DSPy fails
            return self._generate_fallback_title(recent_messages)
    
    def _format_messages_for_ai(self, messages: List[ChatMessage]) -> str:
        """Format chat messages for AI processing."""
        formatted = []
        for msg in messages:
            role = "User" if msg.role.value == "user" else "AI"
            # Truncate very long messages
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _generate_fallback_title(self, messages: List[ChatMessage]) -> str:
        """Generate a simple fallback title based on message content."""
        if not messages:
            return "New conversation"
            
        first_user_message = next(
            (msg for msg in messages if msg.role.value == "user"), 
            None
        )
        
        if first_user_message:
            # Use first few words of the first user message
            words = first_user_message.content.split()[:6]
            title = " ".join(words)
            if len(title) > 50:
                title = title[:47] + "..."
            return title
            
        return "New conversation"


class StubThreadTitleService:
    """Stub implementation for thread title service - to be replaced when UOW is ready."""
    
    def __init__(self, message_repository: ChatMessageRepository):
        self.message_repository = message_repository
        
    async def generate_title_for_thread(self, thread_id: UUID) -> str:
        """
        Stub implementation that generates simple titles.
        This can be replaced with the full DSPy implementation later.
        """
        messages = await self.message_repository.get_by_thread_id(thread_id)
        
        if not messages:
            return "New conversation"
            
        # Find first user message
        first_user_message = next(
            (msg for msg in messages if msg.role.value == "user"), 
            None
        )
        
        if first_user_message:
            # Use first few words of the first user message
            words = first_user_message.content.split()[:5]
            title = " ".join(words)
            if len(title) > 40:
                title = title[:37] + "..."
            return title if title else "New conversation"
            
        return "New conversation"