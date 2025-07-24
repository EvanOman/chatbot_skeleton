import os
from uuid import UUID

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .infrastructure.container.container import Container
from .infrastructure.middleware.logging_middleware import RichLoggingMiddleware
from .presentation.api.chat_routes import router as chat_router
from .presentation.api.export_routes import router as export_router
from .presentation.api.visualization_routes import router as visualization_router
from .presentation.api.webhook_routes import router as webhook_router
from .presentation.websocket.chat_websocket import websocket_endpoint


def create_app() -> FastAPI:
    # Initialize container
    Container()

    app = FastAPI(
        title="🤖 Sample Chat App API",
        description="""
        A modern Python chat application with FastAPI and WebSocket support.

        ## Features

        * **Advanced AI Agent**: DSPy REACT agent with sophisticated reasoning
        * **Tool Integration**: Calculator, web search, weather APIs, file processing
        * **Real-time Chat**: WebSocket support for instant messaging
        * **Memory System**: BM25-based conversation memory and context
        * **Streaming Responses**: Real-time typing effects

        ## Getting Started

        1. **Create a Thread**: Start by creating a new chat thread
        2. **Send Messages**: Use the message endpoint to chat with the AI
        3. **Explore Tools**: Try calculator, weather, or search queries

        ## Example Interactions

        * **Calculator**: "What is 25 * 18 + 42?"
        * **Weather**: "What's the weather like in San Francisco?"
        * **Search**: "Search for the latest AI news"
        * **General**: "Explain how machine learning works"

        ## Try It Out

        Use these example UUIDs in the interactive documentation below:
        * **User ID**: `123e4567-e89b-12d3-a456-426614174000`
        * **Thread ID**: `123e4567-e89b-12d3-a456-426614174000`

        ---

        **💡 Tip**: All endpoints include detailed examples in their "Try it out" sections.
        """,
        version="0.1.0",
        contact={
            "name": "Sample Chat App",
            "url": "https://github.com/EvanOman/chatbot_skeleton",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        tags_metadata=[
            {
                "name": "chat",
                "description": "Chat thread and message operations. Create threads, send messages, and interact with the AI assistant.",
            },
            {
                "name": "visualization",
                "description": "Interactive visualization features. Visualize chat threads as conversation trees and view thread overviews.",
            },
            {
                "name": "export",
                "description": "Conversation export features. Export chat threads in multiple formats (JSON, CSV, Markdown, HTML).",
            },
            {
                "name": "webhooks",
                "description": "Webhook management and external integrations. Configure webhooks to receive notifications about chat events.",
            },
        ],
    )

    # Add rich logging middleware for development
    development_mode = os.getenv("ENVIRONMENT", "development").lower() == "development"
    if development_mode:
        app.add_middleware(RichLoggingMiddleware, enable_logging=True)

    # Include routers
    app.include_router(chat_router)
    app.include_router(export_router)
    app.include_router(visualization_router)
    app.include_router(webhook_router)

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
                * { box-sizing: border-box; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; 
                    margin: 0; 
                    padding: 0; 
                    background-color: #0f0f23; 
                    color: #ececf1;
                    height: 100vh;
                    overflow: hidden;
                }
                
                .app-container {
                    display: flex;
                    height: 100vh;
                }
                
                /* Sidebar Styles */
                .sidebar {
                    width: 260px;
                    background-color: #202123;
                    border-right: 1px solid #32343a;
                    display: flex;
                    flex-direction: column;
                    position: relative;
                }
                
                .sidebar-header {
                    padding: 12px;
                    border-bottom: 1px solid #32343a;
                }
                
                .new-chat-btn {
                    width: 100%;
                    padding: 12px;
                    background: transparent;
                    border: 1px solid #565869;
                    border-radius: 6px;
                    color: #ececf1;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    transition: background-color 0.2s;
                }
                
                .new-chat-btn:hover {
                    background-color: #2a2b32;
                }
                
                .threads-list {
                    flex: 1;
                    overflow-y: auto;
                    padding: 8px 0;
                }
                
                .thread-item {
                    padding: 12px;
                    margin: 2px 8px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    word-break: break-word;
                    position: relative;
                    transition: background-color 0.2s;
                }
                
                .thread-item:hover {
                    background-color: #2a2b32;
                }
                
                .thread-item.active {
                    background-color: #343541;
                }
                
                .thread-title {
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                
                .user-section {
                    padding: 12px;
                    border-top: 1px solid #32343a;
                    font-size: 14px;
                    color: #8e8ea0;
                }
                
                /* Main Chat Area */
                .main-content {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    background-color: #343541;
                }
                
                .chat-header {
                    padding: 12px 20px;
                    border-bottom: 1px solid #32343a;
                    background-color: #343541;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                
                .model-selector-container {
                    padding: 12px 20px;
                    border-bottom: 1px solid #32343a;
                    background-color: #343541;
                }

                .model-selector-container select {
                    width: 100%;
                    padding: 8px;
                    background-color: #40414f;
                    color: #ececf1;
                    border: 1px solid #565869;
                    border-radius: 6px;
                }
                
                .chat-title {
                    font-size: 18px;
                    font-weight: 600;
                    color: #ececf1;
                }
                
                .status {
                    font-size: 12px;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-weight: 500;
                }
                
                .connected { 
                    background-color: #10a37f; 
                    color: white;
                }
                
                .disconnected { 
                    background-color: #ef4444; 
                    color: white;
                }
                
                .chat-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                    background-color: #343541;
                }
                
                .message {
                    margin-bottom: 24px;
                    max-width: 800px;
                    margin-left: auto;
                    margin-right: auto;
                }
                
                .message-wrapper {
                    display: flex;
                    gap: 16px;
                    padding: 20px;
                    border-radius: 8px;
                }
                
                .user-message .message-wrapper {
                    background-color: #444654;
                }
                
                .ai-message .message-wrapper {
                    background-color: #343541;
                    border: 1px solid #32343a;
                }
                
                .message-role {
                    font-weight: 600;
                    font-size: 16px;
                    margin-bottom: 8px;
                    min-width: 60px;
                }
                
                .user-role { color: #19c37d; }
                .ai-role { color: #ff6b6b; }
                
                .message-content {
                    flex: 1;
                    line-height: 1.6;
                }
                
                .chat-input-container {
                    padding: 20px;
                    background-color: #343541;
                    border-top: 1px solid #32343a;
                }
                
                .chat-input {
                    max-width: 800px;
                    margin: 0 auto;
                    display: flex;
                    align-items: end;
                    gap: 12px;
                    background-color: #40414f;
                    border-radius: 12px;
                    padding: 12px;
                    border: 1px solid #565869;
                }
                
                .chat-input textarea {
                    flex: 1;
                    background: transparent;
                    border: none;
                    color: #ececf1;
                    font-size: 16px;
                    font-family: inherit;
                    resize: none;
                    outline: none;
                    min-height: 24px;
                    max-height: 200px;
                    padding: 0;
                }
                
                .chat-input button {
                    background: #19c37d;
                    border: none;
                    border-radius: 6px;
                    color: white;
                    cursor: pointer;
                    padding: 8px 12px;
                    font-size: 14px;
                    transition: background-color 0.2s;
                }
                
                .chat-input button:hover:not(:disabled) {
                    background: #0fa36b;
                }
                
                .chat-input button:disabled {
                    background: #565869;
                    cursor: not-allowed;
                }
                
                .file-button {
                    background: #40414f !important;
                    border: 1px solid #565869 !important;
                    color: #ececf1 !important;
                }
                
                .file-button:hover {
                    background: #525362 !important;
                }
                
                .typing-cursor { 
                    color: #19c37d; 
                    font-weight: bold; 
                    margin-left: 2px; 
                }
                
                @keyframes blink { 
                    0%, 50% { opacity: 1; } 
                    51%, 100% { opacity: 0; } 
                }
                
                .streaming-content { display: inline; }

                /* Markdown styling */
                .message-content h1, .message-content h2, .message-content h3 {
                    margin: 16px 0 8px 0; 
                    color: #ececf1;
                }
                .message-content h1 { font-size: 1.25em; }
                .message-content h2 { font-size: 1.1em; }
                .message-content h3 { font-size: 1.05em; }
                .message-content p { margin: 12px 0; line-height: 1.6; }
                .message-content code {
                    background: #1a1b26; 
                    padding: 2px 6px; 
                    border-radius: 4px;
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace; 
                    font-size: 0.9em;
                    color: #e2e8f0;
                }
                .message-content pre {
                    background: #1a1b26; 
                    padding: 16px; 
                    border-radius: 8px;
                    overflow-x: auto; 
                    margin: 16px 0; 
                    border-left: 4px solid #19c37d;
                }
                .message-content pre code {
                    background: none; 
                    padding: 0;
                }
                .message-content ul, .message-content ol {
                    margin: 12px 0; 
                    padding-left: 24px;
                }
                .message-content li { margin: 6px 0; }
                .message-content blockquote {
                    border-left: 4px solid #565869; 
                    margin: 16px 0; 
                    padding: 8px 16px;
                    background: #2a2b32; 
                    font-style: italic;
                }
                .message-content strong { font-weight: 600; color: #ececf1; }
                .message-content em { font-style: italic; }
                .message-content a { color: #19c37d; text-decoration: none; }
                .message-content a:hover { text-decoration: underline; }
                
                /* Loading state */
                .loading {
                    text-align: center;
                    color: #8e8ea0;
                    padding: 20px;
                    font-style: italic;
                }
                
                /* Empty state */
                .empty-chat {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    text-align: center;
                    color: #8e8ea0;
                }
                
                .empty-chat h2 {
                    margin-bottom: 8px;
                    color: #ececf1;
                }
                
                .empty-chat p {
                    margin-bottom: 24px;
                }
            </style>
        </head>
        <body>
            <div class="app-container">
                <!-- Sidebar -->
                <div class="sidebar">
                    <div class="sidebar-header">
                        <button class="new-chat-btn" onclick="createNewThread()">
                            + New chat
                        </button>
                    </div>
                    
                    <div class="threads-list" id="threadsList">
                        <div class="loading">Loading threads...</div>
                    </div>
                    
                    <div class="user-section">
                        <div>User: <span id="currentUser">user_123</span></div>
                        <div class="status" id="globalStatus">Disconnected</div>
                    </div>
                </div>
                
                <!-- Main Chat Area -->
                <div class="main-content">
                    <div class="chat-header">
                        <div class="chat-title" id="chatTitle">Select a chat to start messaging</div>
                    </div>
                    <div class="model-selector-container">
                        <select id="modelSelector">
                            <option value="echobot">EchoBot</option>
                            <option value="dspy">DSPy Agent</option>
                        </select>
                    </div>
                    
                    <div class="chat-messages" id="messages">
                        <div class="empty-chat">
                            <h2>Welcome to Sample Chat App</h2>
                            <p>Select a chat from the sidebar or create a new one to get started.</p>
                        </div>
                    </div>
                    
                    <div class="chat-input-container" id="inputContainer" style="display: none;">
                        <div class="chat-input">
                            <textarea id="messageInput" placeholder="Type your message..." rows="1" onkeydown="handleKeyDown(event)" oninput="autoResize(this)"></textarea>
                            <input type="file" id="fileInput" accept=".txt,.md,.py,.js,.html,.css,.json,.xml,.yaml,.yml,.jpg,.jpeg,.png,.gif,.bmp,.webp,.pdf,.doc,.docx,.csv,.tsv,.xlsx" style="display: none;" onchange="handleFileUpload(event)">
                            <button class="file-button" onclick="document.getElementById('fileInput').click()">📎</button>
                            <button id="sendButton" onclick="sendMessage()" disabled>Send</button>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                let ws = null;
                let currentUserId = '123e4567-e89b-12d3-a456-426614174000'; // Default user UUID (user_123)
                let currentThreadId = null;
                let userThreads = [];

                function generateUUID() {
                    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                        return v.toString(16);
                    });
                }

                // Initialize the app
                async function initApp() {
                    document.getElementById('currentUser').textContent = 'user_123';
                    await loadUserThreads();
                    updateGlobalStatus('Disconnected', false);
                }

                async function loadUserThreads() {
                    try {
                        const response = await fetch(`/api/threads/user/${currentUserId}`);
                        if (response.ok) {
                            userThreads = await response.json();
                            renderThreadsList();
                        } else {
                            const errorText = await response.text();
                            console.error('Failed to load user threads:', response.status, errorText);
                            renderThreadsList(); // Show empty state
                        }
                    } catch (error) {
                        console.error('Error loading threads:', error);
                        renderThreadsList(); // Show empty state
                    }
                }

                function renderThreadsList() {
                    const threadsList = document.getElementById('threadsList');
                    
                    if (userThreads.length === 0) {
                        threadsList.innerHTML = `
                            <div class="loading">No chat threads yet. Create your first chat!</div>
                        `;
                        return;
                    }

                    threadsList.innerHTML = userThreads.map(thread => `
                        <div class="thread-item ${thread.thread_id === currentThreadId ? 'active' : ''}" 
                             onclick="selectThread('${thread.thread_id}', '${escapeHtml(thread.title || 'New Chat')}')">
                            <div class="thread-title">${escapeHtml(thread.title || 'New Chat')}</div>
                        </div>
                    `).join('');
                }

                function escapeHtml(text) {
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                }

                async function createNewThread() {
                    try {
                        const response = await fetch('/api/threads/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                user_id: currentUserId,
                                title: 'New Chat'
                            })
                        });

                        if (response.ok) {
                            const thread = await response.json();
                            userThreads.unshift(thread); // Add to beginning
                            renderThreadsList();
                            selectThread(thread.thread_id, thread.title || 'New Chat');
                        } else {
                            const errorText = await response.text();
                            console.error('Failed to create thread:', response.status, errorText);
                            alert('Failed to create thread: ' + response.status + ' - ' + errorText);
                        }
                    } catch (error) {
                        console.error('Error creating thread:', error);
                        alert('Error creating thread: ' + error.message);
                    }
                }

                function selectThread(threadId, title) {
                    currentThreadId = threadId;
                    
                    // Update active thread in sidebar
                    document.querySelectorAll('.thread-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    event?.target?.closest('.thread-item')?.classList.add('active');
                    
                    // Update chat title
                    document.getElementById('chatTitle').textContent = title;
                    
                    // Show input container and connect
                    document.getElementById('inputContainer').style.display = 'block';
                    
                    // Clear empty state
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML = '';
                    
                    connectWebSocket();
                    loadMessages();
                }

                function updateGlobalStatus(status, connected) {
                    const statusElement = document.getElementById('globalStatus');
                    statusElement.textContent = status;
                    statusElement.className = `status ${connected ? 'connected' : 'disconnected'}`;
                }

                function connectWebSocket() {
                    if (ws) {
                        ws.close();
                    }

                    if (!currentThreadId) {
                        console.error('No thread selected');
                        return;
                    }

                    const wsUrl = `ws://${window.location.host}/ws/${currentThreadId}/${currentUserId}`;
                    ws = new WebSocket(wsUrl);

                    ws.onopen = function() {
                        updateGlobalStatus('Connected', true);
                        updateSendButton();
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
                        updateGlobalStatus('Disconnected', false);
                        updateSendButton();
                    };

                    ws.onerror = function(error) {
                        console.error('WebSocket error:', error);
                        updateGlobalStatus('Connection Error', false);
                        updateSendButton();
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

                    const messageWrapper = document.createElement('div');
                    messageWrapper.className = 'message-wrapper';

                    const roleDiv = document.createElement('div');
                    roleDiv.className = `message-role ${message.role === 'user' ? 'user-role' : 'ai-role'}`;
                    roleDiv.textContent = message.role === 'user' ? 'You' : 'AI';

                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'message-content';

                    if (message.role === 'assistant') {
                        // Parse markdown for AI messages
                        contentDiv.innerHTML = parseMarkdown(message.content);
                    } else {
                        // Plain text for user messages
                        contentDiv.textContent = message.content;
                    }

                    messageWrapper.appendChild(roleDiv);
                    messageWrapper.appendChild(contentDiv);
                    messageDiv.appendChild(messageWrapper);
                    messagesDiv.appendChild(messageDiv);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                function startStreamingMessage(data) {
                    const messagesDiv = document.getElementById('messages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message ai-message';
                    messageDiv.id = `msg-${data.message_id}`;

                    const messageWrapper = document.createElement('div');
                    messageWrapper.className = 'message-wrapper';

                    const roleDiv = document.createElement('div');
                    roleDiv.className = 'message-role ai-role';
                    roleDiv.textContent = 'AI';

                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'streaming-content message-content';
                    contentDiv.textContent = '';

                    const cursorSpan = document.createElement('span');
                    cursorSpan.className = 'typing-cursor';
                    cursorSpan.textContent = '▋';
                    cursorSpan.style.animation = 'blink 1s infinite';

                    messageWrapper.appendChild(roleDiv);
                    messageWrapper.appendChild(contentDiv);
                    messageWrapper.appendChild(cursorSpan);
                    messageDiv.appendChild(messageWrapper);
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

                function updateSendButton() {
                    const sendButton = document.getElementById('sendButton');
                    const input = document.getElementById('messageInput');
                    const hasText = input.value.trim().length > 0;
                    const isConnected = ws && ws.readyState === WebSocket.OPEN;
                    
                    sendButton.disabled = !hasText || !isConnected;
                }

                function autoResize(textarea) {
                    textarea.style.height = 'auto';
                    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
                    updateSendButton();
                }

                function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    const model = document.getElementById('modelSelector').value;

                    if (message && currentThreadId) {
                        if (model === 'dspy') {
                            // Send message via HTTP to DSPy agent
                            sendHttpMessage(message);
                        } else {
                            // Send message via WebSocket to EchoBot
                            sendWsMessage(message);
                        }
                        input.value = '';
                        input.style.height = 'auto';
                        updateSendButton();
                    } else if (!currentThreadId) {
                        alert('No thread selected');
                    }
                }

                function sendWsMessage(message) {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'message',
                            content: message,
                            message_type: 'text'
                        }));
                    } else {
                        alert('WebSocket is not connected');
                    }
                }

                async function sendHttpMessage(message) {
                    try {
                        const response = await fetch(`/api/threads/${currentThreadId}/messages`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                content: message,
                                message_type: 'text'
                            })
                        });

                        if (response.ok) {
                            const data = await response.json();
                            data.forEach(displayMessage);
                        } else {
                            const errorText = await response.text();
                            console.error('Failed to send message:', response.status, errorText);
                            alert('Failed to send message: ' + response.status + ' - ' + errorText);
                        }
                    } catch (error) {
                        console.error('Error sending message:', error);
                        alert('Error sending message: ' + error.message);
                    }
                }

                function handleKeyDown(event) {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
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

                // Initialize app when page loads
                window.addEventListener('load', initApp);
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
                            <h3><span class="emoji">🌳</span>Visualization</h3>
                            <ul class="card-links">
                                <li><a href="/api/visualization/threads/overview">Threads Overview</a></li>
                                <li><a href="/api/visualization/thread/123e4567-e89b-12d3-a456-426614174000/tree">Sample Tree View</a></li>
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
                            <h3><span class="emoji">📚</span>API Documentation</h3>
                            <ul class="card-links">
                                <li><a href="/docs">Swagger UI</a></li>
                                <li><a href="/redoc">ReDoc Documentation</a></li>
                                <li><a href="/openapi.json">OpenAPI Schema</a></li>
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
