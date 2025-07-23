import os
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from uuid import UUID
import json
import traceback
import time

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
    
    tool_name = OutputField(desc="Name of the tool to use: 'calculator', 'search', 'weather', 'text_processor', 'code_runner', 'memory_store', 'memory_search', 'memory_list', 'none'")
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
        """Enhanced calculator with support for complex mathematical operations."""
        try:
            import math
            import re
            
            # Clean up the expression
            expression = expression.strip()
            
            # Support natural language math queries
            expression = re.sub(r'\bsquare root of\b', 'sqrt', expression, flags=re.IGNORECASE)
            expression = re.sub(r'\bsin of\b', 'sin', expression, flags=re.IGNORECASE)
            expression = re.sub(r'\bcos of\b', 'cos', expression, flags=re.IGNORECASE)
            expression = re.sub(r'\btan of\b', 'tan', expression, flags=re.IGNORECASE)
            expression = re.sub(r'\blog of\b', 'log', expression, flags=re.IGNORECASE)
            expression = re.sub(r'\be to the power of\b', 'exp', expression, flags=re.IGNORECASE)
            expression = re.sub(r'\bpi\b', str(math.pi), expression, flags=re.IGNORECASE)
            expression = re.sub(r'\be\b', str(math.e), expression, flags=re.IGNORECASE)
            
            # Define safe functions
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sinh": math.sinh,
                "cosh": math.cosh,
                "tanh": math.tanh,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "ceil": math.ceil,
                "floor": math.floor,
                "factorial": math.factorial,
                "degrees": math.degrees,
                "radians": math.radians,
                "pi": math.pi,
                "e": math.e,
            }
            
            # Check for dangerous operations
            dangerous_patterns = ['import', 'exec', 'eval', '__', 'open', 'file']
            if any(pattern in expression.lower() for pattern in dangerous_patterns):
                return "Error: Potentially dangerous operation detected"
            
            # Evaluate the expression
            result = eval(expression, allowed_names)
            
            # Format the result nicely
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 8)
            
            return f"**Calculation Result:** `{result}`\n\n*Expression:* `{expression}`"
        except Exception as e:
            return f"**Calculation Error:** {str(e)}\n\n*Expression:* `{expression}`"


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
        return f"**Weather in {location}:**\n\n🌤️ *This is simulated weather data*\n- Temperature: 72°F (22°C)\n- Conditions: Partly cloudy\n- Humidity: 65%\n- Wind: 8 mph SW\n\n*In production, this would return actual weather information from a weather API.*"


class TextProcessor:
    @staticmethod
    def process_text(text: str, operation: str = "analyze") -> str:
        """Process text with various operations."""
        try:
            import re
            from collections import Counter
            
            text = text.strip()
            if not text:
                return "Error: No text provided"
            
            if operation.lower() in ["analyze", "analysis"]:
                # Text analysis
                words = re.findall(r'\b\w+\b', text.lower())
                sentences = re.split(r'[.!?]+', text)
                paragraphs = text.split('\n\n')
                
                word_count = len(words)
                sentence_count = len([s for s in sentences if s.strip()])
                paragraph_count = len([p for p in paragraphs if p.strip()])
                char_count = len(text)
                char_count_no_spaces = len(text.replace(' ', ''))
                
                # Most common words
                word_freq = Counter(words)
                common_words = word_freq.most_common(5)
                
                # Average lengths
                avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
                avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
                
                result = f"**Text Analysis:**\n\n"
                result += f"📊 **Statistics:**\n"
                result += f"- Words: {word_count}\n"
                result += f"- Sentences: {sentence_count}\n"
                result += f"- Paragraphs: {paragraph_count}\n"
                result += f"- Characters: {char_count} ({char_count_no_spaces} without spaces)\n"
                result += f"- Average word length: {avg_word_length:.1f} characters\n"
                result += f"- Average sentence length: {avg_sentence_length:.1f} words\n\n"
                
                if common_words:
                    result += f"🔤 **Most common words:**\n"
                    for word, count in common_words:
                        result += f"- {word}: {count} time{'s' if count > 1 else ''}\n"
                
                return result
                
            elif operation.lower() in ["summarize", "summary"]:
                # Simple extractive summary (first and last sentences)
                sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
                if len(sentences) <= 2:
                    return f"**Summary:** The text is already quite short.\n\n*Original text:* {text}"
                
                summary_sentences = []
                if sentences:
                    summary_sentences.append(sentences[0])
                    if len(sentences) > 2:
                        summary_sentences.append(sentences[-1])
                
                summary = '. '.join(summary_sentences) + '.'
                return f"**Summary:**\n\n{summary}\n\n*({len(sentences)} sentences reduced to {len(summary_sentences)})*"
                
            elif operation.lower() in ["uppercase", "upper"]:
                return f"**Uppercase text:**\n\n{text.upper()}"
                
            elif operation.lower() in ["lowercase", "lower"]:
                return f"**Lowercase text:**\n\n{text.lower()}"
                
            elif operation.lower() in ["title", "titlecase"]:
                return f"**Title Case:**\n\n{text.title()}"
                
            elif operation.lower() in ["reverse"]:
                return f"**Reversed text:**\n\n{text[::-1]}"
                
            elif operation.lower() in ["word_count", "count"]:
                words = re.findall(r'\b\w+\b', text)
                return f"**Word count:** {len(words)} words"
                
            else:
                return f"**Available operations:** analyze, summarize, uppercase, lowercase, title, reverse, word_count\n\n*You requested:* {operation}"
                
        except Exception as e:
            return f"**Text Processing Error:** {str(e)}"


class CodeRunner:
    @staticmethod
    def run_code(code: str, language: str = "python") -> str:
        """Safely run simple code snippets (placeholder - would need sandboxing in production)."""
        # This is a placeholder for security reasons
        # In production, this would require proper sandboxing
        return f"**Code Execution (Simulation):**\n\n```{language}\n{code}\n```\n\n⚠️ *Code execution is simulated for security. In production, this would run in a secure sandbox.*"


class MemoryTool:
    """Tool for storing and retrieving information using BM25 search."""
    
    def __init__(self):
        self.memories = []
        self.corpus = []
        self.bm25 = None
        self._initialize_bm25()
    
    def _initialize_bm25(self):
        """Initialize BM25 with NLTK tokenization."""
        try:
            import nltk
            from rank_bm25 import BM25Okapi
            
            # Try to download required NLTK data with proper error handling
            try:
                nltk.data.find('tokenizers/punkt')
            except (LookupError, FileNotFoundError):
                try:
                    # Ensure NLTK data directory exists
                    import os
                    os.makedirs(os.path.expanduser('~/nltk_data'), exist_ok=True)
                    nltk.download('punkt', quiet=True, download_dir=os.path.expanduser('~/nltk_data'))
                except Exception:
                    pass  # Continue without punkt if download fails
            
            try:
                nltk.data.find('corpora/stopwords')
            except (LookupError, FileNotFoundError):
                try:
                    import os
                    os.makedirs(os.path.expanduser('~/nltk_data'), exist_ok=True)
                    nltk.download('stopwords', quiet=True, download_dir=os.path.expanduser('~/nltk_data'))
                except Exception:
                    pass  # Continue without stopwords if download fails
            
        except ImportError:
            # BM25 dependencies not available
            pass
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25."""
        import re
        
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        try:
            import nltk
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize
            
            # Try NLTK tokenization
            tokens = word_tokenize(text)
            
            # Remove stopwords if available
            try:
                stop_words = set(stopwords.words('english'))
                tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
            except Exception:
                # If stopwords not available, just filter short words
                tokens = [token for token in tokens if len(token) > 2]
            
            return tokens
        except Exception:
            # Fallback to simple splitting with basic stopword removal
            common_stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
                'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
            }
            words = text.split()
            return [word for word in words if len(word) > 2 and word not in common_stopwords]
    
    def store_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Store a memory and rebuild the BM25 index."""
        try:
            from rank_bm25 import BM25Okapi
            import datetime
            
            memory = {
                'id': len(self.memories),
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.datetime.now().isoformat(),
                'tokens': self._tokenize(content)
            }
            
            self.memories.append(memory)
            self.corpus = [memory['tokens'] for memory in self.memories]
            
            # Rebuild BM25 index
            if self.corpus:
                self.bm25 = BM25Okapi(self.corpus)
            
            return f"**Memory stored** (ID: {memory['id']})\n\n*Content preview:* {content[:100]}{'...' if len(content) > 100 else ''}"
            
        except ImportError:
            return "**Error:** BM25 dependencies not available. Please install rank-bm25 and nltk."
        except Exception as e:
            return f"**Memory storage error:** {str(e)}"
    
    def search_memory(self, query: str, top_k: int = 3) -> str:
        """Search memories using BM25."""
        try:
            if not self.memories:
                return "**No memories stored yet.**\n\nUse the memory tool to store information first."
            
            if not self.bm25:
                return "**Search index not available.** Please store some memories first."
            
            # Tokenize query
            query_tokens = self._tokenize(query)
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top results
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            
            if not top_indices or scores[top_indices[0]] == 0:
                return f"**No relevant memories found for:** '{query}'\n\n*Try different keywords or store more related information.*"
            
            result = f"**Memory search results for:** '{query}'\n\n"
            
            for i, idx in enumerate(top_indices, 1):
                if scores[idx] > 0:
                    memory = self.memories[idx]
                    score = scores[idx]
                    result += f"**{i}. Memory #{memory['id']}** (Score: {score:.2f})\n"
                    result += f"*Stored:* {memory['timestamp'][:19]}\n"
                    result += f"*Content:* {memory['content'][:200]}{'...' if len(memory['content']) > 200 else ''}\n\n"
            
            return result
            
        except Exception as e:
            return f"**Memory search error:** {str(e)}"
    
    def list_memories(self, limit: int = 5) -> str:
        """List recent memories."""
        if not self.memories:
            return "**No memories stored yet.**"
        
        result = f"**Recent memories** (showing last {min(limit, len(self.memories))}):\n\n"
        
        for memory in self.memories[-limit:]:
            result += f"**Memory #{memory['id']}**\n"
            result += f"*Stored:* {memory['timestamp'][:19]}\n"
            result += f"*Content:* {memory['content'][:150]}{'...' if len(memory['content']) > 150 else ''}\n\n"
        
        return result


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
            "text_processor": TextProcessor(),
            "code_runner": CodeRunner(),
        }
        
        # Initialize memory tool (shared across agent instance)
        self.memory_tool = MemoryTool()
        
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
            elif tool_name == "text_processor":
                # Parse operation and text from input
                parts = tool_input.split(":", 1)
                if len(parts) == 2:
                    operation = parts[0].strip()
                    text = parts[1].strip()
                    return self.tools["text_processor"].process_text(text, operation)
                else:
                    return self.tools["text_processor"].process_text(tool_input, "analyze")
            elif tool_name == "code_runner":
                # Parse language and code from input
                parts = tool_input.split(":", 1)
                if len(parts) == 2:
                    language = parts[0].strip()
                    code = parts[1].strip()
                    return self.tools["code_runner"].run_code(code, language)
                else:
                    return self.tools["code_runner"].run_code(tool_input, "python")
            elif tool_name == "memory_store":
                return self.memory_tool.store_memory(tool_input)
            elif tool_name == "memory_search":
                return self.memory_tool.search_memory(tool_input)
            elif tool_name == "memory_list":
                try:
                    limit = int(tool_input) if tool_input.strip().isdigit() else 5
                except:
                    limit = 5
                return self.memory_tool.list_memories(limit)
            else:
                return f"Error: Unknown tool '{tool_name}'. Available tools: calculator, search, weather, text_processor, code_runner, memory_store, memory_search, memory_list"
        except Exception as e:
            return f"Tool error: {str(e)}"
    
    def _fallback_response(self, user_message: ChatMessage) -> str:
        """Generate a fallback response when DSPy is not available."""
        content = user_message.content.lower()
        
        # Math detection
        math_keywords = ['+', '-', '*', '/', 'calculate', 'math', 'sum', 'multiply', 'divide', 'sqrt', 'sin', 'cos', 'factorial']
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
        
        # Text processing detection
        text_keywords = ['analyze', 'summarize', 'count words', 'uppercase', 'lowercase', 'process text']
        if any(keyword in content for keyword in text_keywords):
            return "I can help with text processing! I can analyze text, summarize content, count words, change case, and more. In this demo mode, I would use my text processing tools to help you."
        
        # Memory detection
        memory_keywords = ['remember', 'store', 'recall', 'memory', 'save this', 'what did i say about']
        if any(keyword in content for keyword in memory_keywords):
            return "I have memory capabilities! I can store information and retrieve it later using BM25 search. In full mode, I would help you store and recall information across our conversations."
        
        # Code detection
        code_keywords = ['code', 'python', 'javascript', 'run', 'execute', 'script']
        if any(keyword in content for keyword in code_keywords):
            return "I can help with code! While I can't execute code for security reasons in this demo, I have tools that would let me analyze and run code in a secure sandbox environment."
        
        # Greeting detection
        greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        if any(greeting in content for greeting in greetings):
            return "Hello! I'm an advanced AI assistant with sophisticated reasoning and tool capabilities. I can help with:\n\n- **Math & calculations** (including complex functions)\n- **Text processing** (analysis, summarization, formatting)\n- **Memory & information storage** (with BM25 search)\n- **Weather information** (simulated)\n- **Web search** (simulated)\n- **Code analysis** (secure execution simulation)\n\nWhat would you like to explore?"
        
        # Question detection
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', '?']
        if any(word in content for word in question_words):
            return f"That's an interesting question about '{user_message.content}'. I'm designed to provide thoughtful, step-by-step responses using advanced reasoning. While I don't have access to real-time data in this demo, I can help you think through problems systematically."
        
        # Default response
        return f"I understand you said: '{user_message.content}'. I'm an advanced conversational AI that uses reasoning and tools to provide helpful responses. I can help with math, answer questions, and more. How can I assist you today?"
    
    async def generate_streaming_response(self, user_message: ChatMessage, thread_id: UUID) -> AsyncGenerator[str, None]:
        """Generate a streaming response with real-time typing effect."""
        try:
            # Add user message to memory
            self._add_to_memory(thread_id, "user", user_message.content)
            
            # Get conversation context
            conversation_history = self._get_conversation_context(thread_id)
            
            # Check if DSPy is properly configured
            if not hasattr(dspy.settings, 'lm') or dspy.settings.lm is None:
                response = self._fallback_response(user_message)
                # Stream the fallback response word by word
                words = response.split()
                for i, word in enumerate(words):
                    if i == 0:
                        yield word
                    else:
                        yield " " + word
                    await asyncio.sleep(0.05)  # Small delay for typing effect
                
                self._add_to_memory(thread_id, "assistant", response)
                return

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
                                for keyword in ['calculate', 'search', 'weather', 'math', '+', '-', '*', '/', 
                                              'analyze', 'summarize', 'remember', 'store', 'recall', 'memory',
                                              'code', 'python', 'execute', 'process text', 'uppercase', 'lowercase'])
                response_type = "tool_assisted" if needs_tools else "direct"
            
            tool_results = "No tools used."
            
            # Step 2: Use tools if needed
            if needs_tools:
                yield "🔧 Using tools to help with your request...\n\n"
                await asyncio.sleep(0.3)
                
                try:
                    tool_decision = self.tool_selector(
                        user_message=user_message.content,
                        reasoning=reasoning
                    )
                    
                    tool_name = tool_decision.tool_name
                    tool_input = tool_decision.tool_input
                    
                    if tool_name != "none":
                        yield f"📊 Running {tool_name} tool...\n\n"
                        await asyncio.sleep(0.2)
                        tool_results = self._use_tool(tool_name, tool_input)
                except Exception as e:
                    tool_results = f"Tool selection error: {str(e)}"
            
            # Step 3: Generate and stream final response
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
            
            # Stream the response word by word with typing effect
            words = response.split()
            streamed_response = ""
            for i, word in enumerate(words):
                if i == 0:
                    chunk = word
                    streamed_response += word
                else:
                    chunk = " " + word
                    streamed_response += " " + word
                yield chunk
                await asyncio.sleep(0.08)  # Typing delay
            
            # Add complete response to memory
            self._add_to_memory(thread_id, "assistant", streamed_response)
            
        except Exception as e:
            # Ultimate fallback
            error_msg = f"I encountered an error while processing your request. Let me provide a simpler response:\n\n{self._fallback_response(user_message)}"
            words = error_msg.split()
            streamed_response = ""
            for i, word in enumerate(words):
                if i == 0:
                    chunk = word
                    streamed_response += word
                else:
                    chunk = " " + word
                    streamed_response += " " + word
                yield chunk
                await asyncio.sleep(0.05)
            
            self._add_to_memory(thread_id, "assistant", streamed_response)

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
                                for keyword in ['calculate', 'search', 'weather', 'math', '+', '-', '*', '/', 
                                              'analyze', 'summarize', 'remember', 'store', 'recall', 'memory',
                                              'code', 'python', 'execute', 'process text', 'uppercase', 'lowercase'])
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