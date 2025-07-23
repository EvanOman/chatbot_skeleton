import os
import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID
import json
import traceback

import dspy
from dspy import Module, Signature, InputField, OutputField, ChainOfThought

from ...domain.entities.chat_message import ChatMessage
from ...domain.value_objects.message_role import MessageRole
from ..interfaces.bot_service import BotService


class ReactThought(Signature):
    """Analyze the user's message and determine the appropriate response strategy."""
    
    user_message = InputField(desc="The user's input message")
    conversation_history = InputField(desc="Previous messages in the conversation")
    
    reasoning = OutputField(desc="Step-by-step reasoning about how to respond")
    needs_tools = OutputField(desc="Whether tools are needed (true/false)")
    response_type = OutputField(desc="Type of response: 'direct', 'tool_assisted', 'clarification'")


class ToolSelection(Signature):
    """Select and configure the appropriate tool for the task."""
    
    user_message = InputField(desc="The user's input message")
    reasoning = InputField(desc="Previous reasoning about the task")
    
    tool_name = OutputField(desc="Name of the tool to use: 'calculator', 'search', 'weather', 'none'")
    tool_input = OutputField(desc="Input parameters for the selected tool")


class ResponseGeneration(Signature):
    """Generate a helpful and contextual response."""
    
    user_message = InputField(desc="The user's input message")
    conversation_history = InputField(desc="Previous messages in the conversation")
    reasoning = InputField(desc="Reasoning about the response strategy")
    tool_results = InputField(desc="Results from any tools used (if applicable)")
    
    response = OutputField(desc="The final response to the user")


class Calculator:
    @staticmethod
    def calculate(expression: str) -> str:
        """Safely evaluate mathematical expressions."""
        try:
            # Remove any potentially dangerous characters
            safe_chars = set('0123456789+-*/().sqrt()pow()abs()round()sin()cos()tan()log()exp() ')
            if not all(c in safe_chars or c.isalnum() or c in '.,_' for c in expression):
                return "Error: Invalid characters in expression"
            
            # Use eval with restricted builtins for basic math
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "pow": pow,
                "sqrt": lambda x: x ** 0.5,
                "sin": lambda x: __import__('math').sin(x),
                "cos": lambda x: __import__('math').cos(x),
                "tan": lambda x: __import__('math').tan(x),
                "log": lambda x: __import__('math').log(x),
                "exp": lambda x: __import__('math').exp(x),
            }
            
            result = eval(expression, allowed_names)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"


class SearchTool:
    @staticmethod
    def search(query: str) -> str:
        """Simulate web search (placeholder for actual implementation)."""
        # In a real implementation, this would use SerpAPI or similar
        return f"Search results for '{query}': This is a simulated search result. In production, this would return actual web search results."


class WeatherTool:
    @staticmethod
    def get_weather(location: str) -> str:
        """Get weather information (placeholder for actual implementation)."""
        # In a real implementation, this would use a weather API
        return f"Weather in {location}: This is simulated weather data. In production, this would return actual weather information."


class DSPyReactAgent(BotService):
    """Advanced conversational agent using DSPy REACT pattern."""
    
    def __init__(self):
        # Initialize DSPy with a language model
        # In production, you'd configure with actual API keys
        try:
            # Try to use OpenAI if API key is available
            if os.getenv("OPENAI_API_KEY"):
                lm = dspy.OpenAI(
                    model="gpt-3.5-turbo",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    max_tokens=1000
                )
            else:
                # Fallback to a simple dummy model for demonstration
                lm = dspy.OpenAI(
                    model="gpt-3.5-turbo",
                    api_key="dummy-key",
                    max_tokens=1000
                )
        except Exception:
            # If DSPy initialization fails, use a fallback
            lm = None
        
        if lm:
            dspy.settings.configure(lm=lm)
        
        # Initialize reasoning modules
        self.thought_generator = ChainOfThought(ReactThought)
        self.tool_selector = ChainOfThought(ToolSelection)
        self.response_generator = ChainOfThought(ResponseGeneration)
        
        # Initialize tools
        self.tools = {
            "calculator": Calculator(),
            "search": SearchTool(),
            "weather": WeatherTool(),
        }
        
        # Conversation memory
        self.conversation_memory: Dict[UUID, List[Dict[str, Any]]] = {}
    
    def _get_conversation_context(self, thread_id: UUID, limit: int = 10) -> str:
        """Get recent conversation history for context."""
        if thread_id not in self.conversation_memory:
            return "No previous conversation."
        
        history = self.conversation_memory[thread_id][-limit:]
        context_lines = []
        
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def _add_to_memory(self, thread_id: UUID, role: str, content: str):
        """Add message to conversation memory."""
        if thread_id not in self.conversation_memory:
            self.conversation_memory[thread_id] = []
        
        self.conversation_memory[thread_id].append({
            "role": role,
            "content": content,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        # Keep only last 50 messages to prevent memory bloat
        if len(self.conversation_memory[thread_id]) > 50:
            self.conversation_memory[thread_id] = self.conversation_memory[thread_id][-50:]
    
    def _use_tool(self, tool_name: str, tool_input: str) -> str:
        """Execute a tool and return results."""
        try:
            if tool_name == "calculator":
                return self.tools["calculator"].calculate(tool_input)
            elif tool_name == "search":
                return self.tools["search"].search(tool_input)
            elif tool_name == "weather":
                return self.tools["weather"].get_weather(tool_input)
            else:
                return "Error: Unknown tool"
        except Exception as e:
            return f"Tool error: {str(e)}"
    
    def _fallback_response(self, user_message: ChatMessage) -> str:
        """Generate a fallback response when DSPy is not available."""
        content = user_message.content.lower()
        
        # Math detection
        math_keywords = ['+', '-', '*', '/', 'calculate', 'math', 'sum', 'multiply', 'divide']
        if any(keyword in content for keyword in math_keywords):
            # Try to extract and calculate
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', content)
            operators = re.findall(r'[+\-*/]', content)
            
            if len(numbers) >= 2 and len(operators) >= 1:
                try:
                    if operators[0] == '+':
                        result = float(numbers[0]) + float(numbers[1])
                    elif operators[0] == '-':
                        result = float(numbers[0]) - float(numbers[1])
                    elif operators[0] == '*':
                        result = float(numbers[0]) * float(numbers[1])
                    elif operators[0] == '/':
                        result = float(numbers[0]) / float(numbers[1])
                    else:
                        result = "Could not compute"
                    
                    return f"I calculated: {numbers[0]} {operators[0]} {numbers[1]} = {result}"
                except:
                    pass
        
        # Weather detection
        weather_keywords = ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloudy']
        if any(keyword in content for keyword in weather_keywords):
            return "I'd be happy to help with weather information! However, I need access to a weather API to provide current conditions. This is a demonstration of how the agent would handle weather queries."
        
        # Search detection
        search_keywords = ['search', 'find', 'look up', 'what is', 'who is', 'when', 'where']
        if any(keyword in content for keyword in search_keywords):
            return f"I understand you want to search for information about: '{user_message.content}'. In a full implementation, I would use web search APIs to find current information for you."
        
        # Greeting detection
        greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        if any(greeting in content for greeting in greetings):
            return "Hello! I'm an advanced AI assistant powered by DSPy REACT architecture. I can help you with calculations, answer questions, search for information, and much more. What would you like to know?"
        
        # Question detection
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', '?']
        if any(word in content for word in question_words):
            return f"That's an interesting question about '{user_message.content}'. I'm designed to provide thoughtful, step-by-step responses using advanced reasoning. While I don't have access to real-time data in this demo, I can help you think through problems systematically."
        
        # Default response
        return f"I understand you said: '{user_message.content}'. I'm an advanced conversational AI that uses reasoning and tools to provide helpful responses. I can help with math, answer questions, and more. How can I assist you today?"
    
    async def generate_response(self, user_message: ChatMessage, thread_id: UUID) -> str:
        """Generate an intelligent response using REACT pattern."""
        try:
            # Add user message to memory
            self._add_to_memory(thread_id, "user", user_message.content)
            
            # Get conversation context
            conversation_history = self._get_conversation_context(thread_id)
            
            # Check if DSPy is properly configured
            if not hasattr(dspy.settings, 'lm') or dspy.settings.lm is None:
                response = self._fallback_response(user_message)
                self._add_to_memory(thread_id, "assistant", response)
                return response
            
            # Step 1: Generate reasoning and determine if tools are needed
            try:
                thought = self.thought_generator(
                    user_message=user_message.content,
                    conversation_history=conversation_history
                )
                
                reasoning = thought.reasoning
                needs_tools = thought.needs_tools.lower() == "true"
                response_type = thought.response_type
            except Exception as e:
                # Fallback if thought generation fails
                reasoning = f"Analyzing user request: {user_message.content}"
                needs_tools = any(keyword in user_message.content.lower() 
                                for keyword in ['calculate', 'search', 'weather', 'math', '+', '-', '*', '/'])
                response_type = "tool_assisted" if needs_tools else "direct"
            
            tool_results = "No tools used."
            
            # Step 2: Use tools if needed
            if needs_tools:
                try:
                    tool_decision = self.tool_selector(
                        user_message=user_message.content,
                        reasoning=reasoning
                    )
                    
                    tool_name = tool_decision.tool_name
                    tool_input = tool_decision.tool_input
                    
                    if tool_name != "none":
                        tool_results = self._use_tool(tool_name, tool_input)
                except Exception as e:
                    tool_results = f"Tool selection error: {str(e)}"
            
            # Step 3: Generate final response
            try:
                final_response = self.response_generator(
                    user_message=user_message.content,
                    conversation_history=conversation_history,
                    reasoning=reasoning,
                    tool_results=tool_results
                )
                
                response = final_response.response
            except Exception as e:
                # Fallback response generation
                if tool_results != "No tools used.":
                    response = f"Based on my analysis: {reasoning}\n\nTool results: {tool_results}\n\nI hope this helps! Let me know if you need any clarification."
                else:
                    response = f"I've thought about your request: {reasoning}\n\n{self._fallback_response(user_message)}"
            
            # Add assistant response to memory
            self._add_to_memory(thread_id, "assistant", response)
            
            return response
            
        except Exception as e:
            # Ultimate fallback
            error_msg = f"I encountered an error while processing your request. Let me provide a simpler response:\n\n{self._fallback_response(user_message)}"
            self._add_to_memory(thread_id, "assistant", error_msg)
            return error_msg