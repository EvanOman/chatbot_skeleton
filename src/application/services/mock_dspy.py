"""
Mock implementations for DSPy components to enable testing without API keys.

This module provides fully functional mock implementations that simulate
the behavior of DSPy components for testing purposes.
"""

import re
from typing import Any, Dict


class MockDSPySignature:
    """Base mock for DSPy signatures."""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockReactThought(MockDSPySignature):
    """Mock implementation of ReactThought signature."""
    
    def __init__(self, user_message: str, conversation_history: str):
        # Simulate reasoning based on user message content
        reasoning = self._generate_reasoning(user_message)
        needs_tools = self._determine_tool_need(user_message)
        response_type = self._determine_response_type(user_message)
        
        super().__init__(
            reasoning=reasoning,
            needs_tools=needs_tools,
            response_type=response_type
        )
    
    def _generate_reasoning(self, message: str) -> str:
        """Generate mock reasoning based on message content."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['calculate', 'math', '+', '-', '*', '/', 'what is']):
            return "The user is asking for a mathematical calculation. I should use the calculator tool to provide an accurate result."
        elif any(word in message_lower for word in ['remember', 'store', 'save']):
            return "The user wants to store information in memory. I should use the memory storage tool."
        elif any(word in message_lower for word in ['recall', 'what do i', 'do you know']):
            return "The user is asking about stored information. I should search memory for relevant information."
        elif any(word in message_lower for word in ['weather', 'temperature', 'forecast']):
            return "The user is asking about weather information. I should use the weather tool."
        elif any(word in message_lower for word in ['search', 'find', 'look up']):
            return "The user wants to search for information. I should use the search tool."
        else:
            return f"The user message '{message}' appears to be a general question that I can answer directly."
    
    def _determine_tool_need(self, message: str) -> str:
        """Determine if tools are needed based on message content."""
        message_lower = message.lower()
        tool_keywords = ['calculate', 'math', 'remember', 'recall', 'weather', 'search', 'find', '+', '-', '*', '/']
        return "true" if any(word in message_lower for word in tool_keywords) else "false"
    
    def _determine_response_type(self, message: str) -> str:
        """Determine response type based on message content."""
        if self._determine_tool_need(message) == "true":
            return "tool_assisted"
        elif "?" in message:
            return "direct"
        else:
            return "clarification"


class MockToolSelection(MockDSPySignature):
    """Mock implementation of ToolSelection signature."""
    
    def __init__(self, user_message: str, reasoning: str):
        tool_name, tool_input = self._select_tool(user_message)
        
        super().__init__(
            tool_name=tool_name,
            tool_input=tool_input
        )
    
    def _select_tool(self, message: str) -> tuple[str, str]:
        """Select appropriate tool based on message content."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['calculate', 'math', '+', '-', '*', '/', 'what is']):
            # Extract calculation from message
            calculation = self._extract_calculation(message)
            return "calculator", calculation
        elif any(word in message_lower for word in ['remember', 'store', 'save']):
            # Extract information to store
            info = message.replace("remember", "").replace("that", "").strip()
            return "memory_store", info
        elif any(word in message_lower for word in ['recall', 'what do i', 'do you know']):
            # Extract query for memory search
            query = message.replace("what do i", "").replace("recall", "").replace("?", "").strip()
            return "memory_search", query
        elif any(word in message_lower for word in ['weather', 'temperature']):
            # Extract location if mentioned
            location = "current location"  # Default
            return "weather", location
        elif any(word in message_lower for word in ['search', 'find', 'look up']):
            query = message.replace("search for", "").replace("find", "").replace("look up", "").strip()
            return "search", query
        else:
            return "none", ""
    
    def _extract_calculation(self, message: str) -> str:
        """Extract mathematical expression from message."""
        # Look for "what is X * Y" patterns first
        what_is_pattern = r'what\s+is\s+([\d\s\+\-\*\/\(\)\.]+)'
        match = re.search(what_is_pattern, message.lower())
        if match:
            return match.group(1).strip()
        
        # Look for direct mathematical expressions with numbers and operators
        math_pattern = r'(\d+(?:\.\d+)?\s*[\+\-\*\/]\s*\d+(?:\.\d+)?(?:\s*[\+\-\*\/]\s*\d+(?:\.\d+)?)*)'
        matches = re.findall(math_pattern, message)
        
        if matches:
            return matches[0].strip()
        
        # Fallback: look for any numbers and operators
        simple_pattern = r'(\d+\s*[\*\/\+\-]\s*\d+)'
        match = re.search(simple_pattern, message)
        if match:
            return match.group(1).strip()
        
        return "2 + 2"  # Default simple calculation


class MockResponseGeneration(MockDSPySignature):
    """Mock implementation of ResponseGeneration signature."""
    
    def __init__(self, user_message: str, conversation_history: str, reasoning: str, tool_results: str):
        response = self._generate_response(user_message, conversation_history, reasoning, tool_results)
        super().__init__(response=response)
    
    def _generate_response(self, user_message: str, conversation_history: str, reasoning: str, tool_results: str) -> str:
        """Generate a response based on inputs."""
        if tool_results and tool_results.strip():
            # Use tool results in response
            if "calculator" in reasoning.lower():
                return f"I calculated that for you. {tool_results}"
            elif "memory" in reasoning.lower() and "store" in reasoning.lower():
                return f"I've stored that information for you. {tool_results}"
            elif "memory" in reasoning.lower() and "search" in reasoning.lower():
                return f"Based on what I remember: {tool_results}"
            elif "weather" in reasoning.lower():
                return f"Here's the weather information: {tool_results}"
            elif "search" in reasoning.lower():
                return f"I found this information: {tool_results}"
            else:
                return f"Here's what I found: {tool_results}"
        else:
            # Generate direct response
            return f"I understand you're saying: {user_message}. Based on my reasoning, this appears to be a general question that I can help answer directly."


class MockChainOfThought:
    """Mock implementation of DSPy ChainOfThought."""
    
    def __init__(self, signature_class):
        self.signature_class = signature_class
    
    def __call__(self, **kwargs):
        """Execute the chain of thought with mock implementations."""
        if self.signature_class.__name__ == "ReactThought":
            return MockReactThought(
                user_message=kwargs.get("user_message", ""),
                conversation_history=kwargs.get("conversation_history", "")
            )
        elif self.signature_class.__name__ == "ToolSelection":
            return MockToolSelection(
                user_message=kwargs.get("user_message", ""),
                reasoning=kwargs.get("reasoning", "")
            )
        elif self.signature_class.__name__ == "ResponseGeneration":
            return MockResponseGeneration(
                user_message=kwargs.get("user_message", ""),
                conversation_history=kwargs.get("conversation_history", ""),
                reasoning=kwargs.get("reasoning", ""),
                tool_results=kwargs.get("tool_results", "")
            )
        else:
            # Generic mock response
            return MockDSPySignature(**kwargs)


class MockDSPySettings:
    """Mock DSPy settings."""
    
    @staticmethod
    def configure(**kwargs):
        """Mock configure method."""
        pass


class MockDSPyLM:
    """Mock language model."""
    
    def __init__(self, **kwargs):
        pass


# Mock dspy module structure
class MockDSPy:
    ChainOfThought = MockChainOfThought
    settings = MockDSPySettings()
    
    class OpenAI(MockDSPyLM):
        pass
    
    # Re-export signature classes for compatibility
    Signature = MockDSPySignature
    InputField = lambda desc: None
    OutputField = lambda desc: None