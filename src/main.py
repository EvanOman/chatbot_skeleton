from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from uuid import UUID

from .presentation.api.chat_routes import router as chat_router
from .presentation.websocket.chat_websocket import websocket_endpoint
from .infrastructure.container.container import Container


def create_app() -> FastAPI:
    # Initialize container
    container = Container()
    
    app = FastAPI(
        title="Sample Chat App",
        description="A modern Python chat application with FastAPI and WebSocket support",
        version="0.1.0",
    )
    
    # Include routers
    app.include_router(chat_router)
    
    # WebSocket endpoint
    @app.websocket("/ws/{thread_id}/{user_id}")
    async def websocket_route(websocket: WebSocket, thread_id: UUID, user_id: UUID):
        await websocket_endpoint(websocket, thread_id, user_id)
    
    # Serve static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Root endpoint with HTML chat interface
    @app.get("/", response_class=HTMLResponse)
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
            </script>
        </body>
        </html>
        """
    
    return app


app = create_app()