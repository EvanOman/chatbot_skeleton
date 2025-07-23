import os
from uuid import UUID

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .infrastructure.container.container import Container
from .infrastructure.middleware.logging_middleware import RichLoggingMiddleware
from .presentation.api.chat_routes import router as chat_router
from .presentation.websocket.chat_websocket import websocket_endpoint


def create_app() -> FastAPI:
    # Initialize container
    Container()

    app = FastAPI(
        title="Sample Chat App",
        description="A modern Python chat application with FastAPI and WebSocket support",
        version="0.1.0",
    )

    # Add rich logging middleware for development
    development_mode = os.getenv("ENVIRONMENT", "development").lower() == "development"
    if development_mode:
        app.add_middleware(RichLoggingMiddleware, enable_logging=True)

    # Include routers
    app.include_router(chat_router)

    # WebSocket endpoint
    @app.websocket("/ws/{thread_id}/{user_id}")
    async def websocket_route(websocket: WebSocket, thread_id: UUID, user_id: UUID):
        await websocket_endpoint(websocket, thread_id, user_id)

    # Serve static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Root endpoint - Developer Dashboard in dev mode, Chat interface in production
    @app.get("/", response_class=HTMLResponse)
    async def get_root_interface():
        if development_mode:
            return await get_developer_dashboard()
        else:
            return await get_chat_interface()

    # Chat interface endpoint
    @app.get("/chat", response_class=HTMLResponse)
    async def get_chat_interface():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sample Chat App</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .chat-container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .chat-header { background: #007bff; color: white; padding: 20px; border-radius: 10px 10px 0 0; }
                .chat-messages { height: 400px; overflow-y: auto; padding: 20px; border-bottom: 1px solid #eee; }
                .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
                .user-message { background: #e3f2fd; margin-left: 20%; }
                .ai-message { background: #f1f8e9; margin-right: 20%; }
                .message-role { font-weight: bold; margin-bottom: 5px; }
                .user-role { color: #1976d2; }
                .ai-role { color: #388e3c; }
                .chat-input { display: flex; padding: 20px; }
                .chat-input input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-right: 10px; }
                .chat-input button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
                .chat-input button:hover { background: #0056b3; }
                .setup { margin-bottom: 20px; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .setup input, .setup button { margin: 5px; padding: 8px; }
                .setup button { background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }
                .status { padding: 10px; text-align: center; font-weight: bold; }
                .connected { color: #28a745; }
                .disconnected { color: #dc3545; }
                .typing-cursor { color: #007bff; font-weight: bold; margin-left: 2px; }
                @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
                .streaming-content { display: inline; }

                /* Markdown styling */
                .message-content h1, .message-content h2, .message-content h3 {
                    margin: 10px 0 5px 0; color: #333;
                }
                .message-content h1 { font-size: 1.2em; border-bottom: 1px solid #ddd; }
                .message-content h2 { font-size: 1.1em; }
                .message-content h3 { font-size: 1.05em; }
                .message-content p { margin: 8px 0; line-height: 1.4; }
                .message-content code {
                    background: #f8f9fa; padding: 2px 4px; border-radius: 3px;
                    font-family: 'Courier New', monospace; font-size: 0.9em;
                }
                .message-content pre {
                    background: #f8f9fa; padding: 10px; border-radius: 5px;
                    overflow-x: auto; margin: 10px 0; border-left: 4px solid #007bff;
                }
                .message-content pre code {
                    background: none; padding: 0;
                }
                .message-content ul, .message-content ol {
                    margin: 8px 0; padding-left: 20px;
                }
                .message-content li { margin: 3px 0; }
                .message-content blockquote {
                    border-left: 4px solid #ddd; margin: 10px 0; padding: 5px 15px;
                    background: #f9f9f9; font-style: italic;
                }
                .message-content strong { font-weight: bold; color: #333; }
                .message-content em { font-style: italic; }
                .message-content a { color: #007bff; text-decoration: none; }
                .message-content a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="setup">
                <h3>Chat Setup</h3>
                <label>User ID:</label>
                <input type="text" id="userId" placeholder="Enter your user ID">
                <label>Thread ID:</label>
                <input type="text" id="threadId" placeholder="Enter thread ID (or leave empty to create new)">
                <button onclick="setupChat()">Connect</button>
                <button onclick="createNewThread()">Create New Thread</button>
            </div>

            <div class="chat-container" id="chatContainer" style="display: none;">
                <div class="chat-header">
                    <h2>Sample Chat App</h2>
                    <div class="status" id="status">Disconnected</div>
                </div>
                <div class="chat-messages" id="messages"></div>
                <div class="chat-input">
                    <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                    <input type="file" id="fileInput" accept=".txt,.md,.py,.js,.html,.css,.json,.xml,.yaml,.yml,.jpg,.jpeg,.png,.gif,.bmp,.webp,.pdf,.doc,.docx,.csv,.tsv,.xlsx" style="display: none;" onchange="handleFileUpload(event)">
                    <button onclick="document.getElementById('fileInput').click()">📁</button>
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>

            <script>
                let ws = null;
                let currentUserId = null;
                let currentThreadId = null;

                function generateUUID() {
                    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                        return v.toString(16);
                    });
                }

                async function createNewThread() {
                    const userId = document.getElementById('userId').value || generateUUID();
                    document.getElementById('userId').value = userId;

                    try {
                        const response = await fetch('/api/threads/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                user_id: userId,
                                title: 'New Chat Thread'
                            })
                        });

                        if (response.ok) {
                            const thread = await response.json();
                            document.getElementById('threadId').value = thread.thread_id;
                            setupChat();
                        } else {
                            alert('Failed to create thread');
                        }
                    } catch (error) {
                        alert('Error creating thread: ' + error.message);
                    }
                }

                function setupChat() {
                    const userId = document.getElementById('userId').value || generateUUID();
                    const threadId = document.getElementById('threadId').value || generateUUID();

                    if (!userId || !threadId) {
                        alert('Please provide both User ID and Thread ID');
                        return;
                    }

                    currentUserId = userId;
                    currentThreadId = threadId;

                    document.getElementById('userId').value = userId;
                    document.getElementById('threadId').value = threadId;
                    document.getElementById('chatContainer').style.display = 'block';

                    connectWebSocket();
                    loadMessages();
                }

                function connectWebSocket() {
                    if (ws) {
                        ws.close();
                    }

                    const wsUrl = `ws://localhost:8000/ws/${currentThreadId}/${currentUserId}`;
                    ws = new WebSocket(wsUrl);

                    ws.onopen = function() {
                        document.getElementById('status').textContent = 'Connected';
                        document.getElementById('status').className = 'status connected';
                    };

                    let currentStreamingMessage = null;

                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);

                        if (data.type === 'message') {
                            displayMessage(data);
                        } else if (data.type === 'stream_start') {
                            currentStreamingMessage = startStreamingMessage(data);
                        } else if (data.type === 'stream_chunk') {
                            if (currentStreamingMessage) {
                                appendToStreamingMessage(currentStreamingMessage, data.content);
                            }
                        } else if (data.type === 'stream_end') {
                            if (currentStreamingMessage) {
                                finishStreamingMessage(currentStreamingMessage);
                                currentStreamingMessage = null;
                            }
                        } else if (data.type === 'error') {
                            alert('Error: ' + data.error);
                        }
                    };

                    ws.onclose = function() {
                        document.getElementById('status').textContent = 'Disconnected';
                        document.getElementById('status').className = 'status disconnected';
                    };

                    ws.onerror = function(error) {
                        console.error('WebSocket error:', error);
                        document.getElementById('status').textContent = 'Connection Error';
                        document.getElementById('status').className = 'status disconnected';
                    };
                }

                async function loadMessages() {
                    try {
                        const response = await fetch(`/api/threads/${currentThreadId}/messages`);
                        if (response.ok) {
                            const messages = await response.json();
                            const messagesDiv = document.getElementById('messages');
                            messagesDiv.innerHTML = '';
                            messages.forEach(displayMessage);
                        }
                    } catch (error) {
                        console.error('Error loading messages:', error);
                    }
                }

                function parseMarkdown(text) {
                    // Simple markdown parser
                    let html = text;

                    // Escape HTML first
                    html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

                    // Headers
                    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
                    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
                    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

                    // Code blocks (before other formatting)
                    html = html.replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>');

                    // Inline code
                    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

                    // Bold (simple approach)
                    while (html.indexOf('**') !== -1) {
                        let start = html.indexOf('**');
                        let end = html.indexOf('**', start + 2);
                        if (end !== -1) {
                            let before = html.substring(0, start);
                            let content = html.substring(start + 2, end);
                            let after = html.substring(end + 2);
                            html = before + '<strong>' + content + '</strong>' + after;
                        } else {
                            break;
                        }
                    }

                    // Line breaks
                    html = html.replace(/\\n\\n/g, '</p><p>');
                    html = html.replace(/\\n/g, '<br>');

                    // Wrap in paragraph if doesn't start with a block element
                    if (!html.match(/^<(h[1-6]|pre|ul|ol)/)) {
                        html = '<p>' + html + '</p>';
                    }

                    return html;
                }

                function displayMessage(message) {
                    const messagesDiv = document.getElementById('messages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${message.role === 'user' ? 'user-message' : 'ai-message'}`;

                    const roleDiv = document.createElement('div');
                    roleDiv.className = `message-role ${message.role === 'user' ? 'user-role' : 'ai-role'}`;
                    roleDiv.textContent = message.role === 'user' ? 'You' : 'AI Assistant';

                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'message-content';

                    if (message.role === 'assistant') {
                        // Parse markdown for AI messages
                        contentDiv.innerHTML = parseMarkdown(message.content);
                    } else {
                        // Plain text for user messages
                        contentDiv.textContent = message.content;
                    }

                    messageDiv.appendChild(roleDiv);
                    messageDiv.appendChild(contentDiv);
                    messagesDiv.appendChild(messageDiv);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                function startStreamingMessage(data) {
                    const messagesDiv = document.getElementById('messages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message ai-message';
                    messageDiv.id = `msg-${data.message_id}`;

                    const roleDiv = document.createElement('div');
                    roleDiv.className = 'message-role ai-role';
                    roleDiv.textContent = 'AI Assistant';

                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'streaming-content message-content';
                    contentDiv.textContent = '';

                    const cursorSpan = document.createElement('span');
                    cursorSpan.className = 'typing-cursor';
                    cursorSpan.textContent = '▋';
                    cursorSpan.style.animation = 'blink 1s infinite';

                    messageDiv.appendChild(roleDiv);
                    messageDiv.appendChild(contentDiv);
                    messageDiv.appendChild(cursorSpan);
                    messagesDiv.appendChild(messageDiv);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;

                    return {
                        messageDiv: messageDiv,
                        contentDiv: contentDiv,
                        cursorSpan: cursorSpan,
                        rawContent: ''
                    };
                }

                function appendToStreamingMessage(streamingMessage, chunk) {
                    streamingMessage.rawContent += chunk;
                    // For streaming, show raw text until complete
                    streamingMessage.contentDiv.textContent = streamingMessage.rawContent;
                    streamingMessage.messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }

                function finishStreamingMessage(streamingMessage) {
                    streamingMessage.cursorSpan.remove();
                    // Convert to markdown when streaming is complete
                    streamingMessage.contentDiv.innerHTML = parseMarkdown(streamingMessage.rawContent);
                }

                function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();

                    if (message && ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'message',
                            content: message,
                            message_type: 'text'
                        }));
                        input.value = '';
                    } else if (!ws || ws.readyState !== WebSocket.OPEN) {
                        alert('WebSocket is not connected');
                    }
                }

                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }

                function handleFileUpload(event) {
                    const file = event.target.files[0];
                    if (file && ws && ws.readyState === WebSocket.OPEN) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const base64Data = e.target.result.split(',')[1]; // Remove data:mime;base64, prefix
                            
                            const fileMessage = {
                                type: 'file',
                                filename: file.name,
                                file_data: base64Data
                            };
                            
                            ws.send(JSON.stringify(fileMessage));
                        };
                        reader.readAsDataURL(file);
                    } else if (!ws || ws.readyState !== WebSocket.OPEN) {
                        alert('WebSocket is not connected');
                    }
                    
                    // Clear the file input
                    event.target.value = '';
                }
            </script>
        </body>
        </html>
        """

    async def get_developer_dashboard():
        """Developer dashboard with links to all development tools."""
        # TODO: Get database stats from the database
        # For now, using placeholder values
        thread_count = "N/A"
        message_count = "N/A"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🛠️ Developer Dashboard - Sample Chat App</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white; 
                    border-radius: 15px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #6B73FF 0%, #000DFF 100%);
                    color: white; 
                    padding: 30px; 
                    text-align: center; 
                }}
                .header h1 {{ 
                    margin: 0; 
                    font-size: 2.5em; 
                    font-weight: 300; 
                }}
                .header p {{ 
                    margin: 10px 0 0 0; 
                    opacity: 0.9; 
                    font-size: 1.1em; 
                }}
                .content {{ 
                    padding: 40px; 
                }}
                .grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 30px; 
                    margin-top: 30px; 
                }}
                .card {{ 
                    background: #f8f9fa; 
                    border-radius: 10px; 
                    padding: 25px; 
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
                    transition: transform 0.3s ease, box-shadow 0.3s ease; 
                }}
                .card:hover {{ 
                    transform: translateY(-5px); 
                    box-shadow: 0 10px 25px rgba(0,0,0,0.15); 
                }}
                .card h3 {{ 
                    margin: 0 0 15px 0; 
                    color: #6B73FF; 
                    font-size: 1.3em; 
                }}
                .card-links {{ 
                    list-style: none; 
                    padding: 0; 
                    margin: 0; 
                }}
                .card-links li {{ 
                    margin: 10px 0; 
                }}
                .card-links a {{ 
                    color: #333; 
                    text-decoration: none; 
                    padding: 8px 15px; 
                    background: white; 
                    border-radius: 5px; 
                    display: inline-block; 
                    transition: all 0.3s ease; 
                    border: 2px solid transparent; 
                }}
                .card-links a:hover {{ 
                    background: #6B73FF; 
                    color: white; 
                    border-color: #6B73FF; 
                }}
                .stats {{ 
                    display: flex; 
                    justify-content: space-around; 
                    margin: 30px 0; 
                }}
                .stat {{ 
                    text-align: center; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #ff7eb3 0%, #ff758c 100%); 
                    color: white; 
                    border-radius: 10px; 
                    flex: 1; 
                    margin: 0 10px; 
                }}
                .stat-number {{ 
                    font-size: 2em; 
                    font-weight: bold; 
                    display: block; 
                }}
                .stat-label {{ 
                    font-size: 0.9em; 
                    opacity: 0.9; 
                }}
                .alert {{ 
                    background: #e3f2fd; 
                    border: 2px solid #2196f3; 
                    color: #1976d2; 
                    padding: 15px; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                }}
                .emoji {{ 
                    font-size: 1.5em; 
                    margin-right: 10px; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛠️ Developer Dashboard</h1>
                    <p>Sample Chat App Development Environment</p>
                </div>
                
                <div class="content">
                    <div class="alert">
                        <strong>🚀 Development Mode Active</strong> - 
                        Rich logging enabled, live reloading active
                    </div>
                    
                    <div class="stats">
                        <div class="stat">
                            <span class="stat-number">{thread_count}</span>
                            <span class="stat-label">Chat Threads</span>
                        </div>
                        <div class="stat">
                            <span class="stat-number">{message_count}</span>
                            <span class="stat-label">Messages</span>
                        </div>
                    </div>
                    
                    <div class="grid">
                        <div class="card">
                            <h3><span class="emoji">💬</span>Chat Interface</h3>
                            <ul class="card-links">
                                <li><a href="/chat">Interactive Chat UI</a></li>
                                <li><a href="/api/threads/">Thread Management API</a></li>
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3><span class="emoji">📚</span>API Documentation</h3>
                            <ul class="card-links">
                                <li><a href="/docs">Swagger UI</a></li>
                                <li><a href="/redoc">ReDoc Documentation</a></li>
                                <li><a href="/openapi.json">OpenAPI Schema</a></li>
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3><span class="emoji">🗄️</span>Database Tools</h3>
                            <ul class="card-links">
                                <li><a href="http://localhost:8080" target="_blank">Adminer Database GUI</a></li>
                                <li><a href="#" onclick="alert('Run: uv run alembic upgrade head')">Migration Commands</a></li>
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3><span class="emoji">🔬</span>Development Tools</h3>
                            <ul class="card-links">
                                <li><a href="#" onclick="alert('Run: uv run pytest')">Run Tests</a></li>
                                <li><a href="#" onclick="alert('Run: uv run black src/')">Format Code</a></li>
                                <li><a href="#" onclick="alert('Run: uv run ruff check src/')">Lint Code</a></li>
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3><span class="emoji">🚀</span>Quick Actions</h3>
                            <ul class="card-links">
                                <li><a href="javascript:location.reload()">Reload Dashboard</a></li>
                                <li><a href="#" onclick="alert('Server restart: Ctrl+C then uv run dev')">Restart Server</a></li>
                                <li><a href="https://github.com/EvanOman/chatbot_skeleton" target="_blank">GitHub Repository</a></li>
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3><span class="emoji">📊</span>Monitoring</h3>
                            <ul class="card-links">
                                <li><a href="#" onclick="alert('Check console for rich logs')">View Rich Logs</a></li>
                                <li><a href="#" onclick="alert('Environment: Development Mode')">Environment Info</a></li>
                            </ul>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 40px; padding-top: 30px; border-top: 2px solid #eee;">
                        <p style="color: #666;">
                            🔥 <strong>Live Reloading Active</strong> - Changes will automatically restart the server<br>
                            💡 <strong>Rich Logging Enabled</strong> - Check your console for colorized request/response logs
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    return app


app = create_app()
