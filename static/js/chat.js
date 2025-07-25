// Chat interface JavaScript
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

    if (message && ws && ws.readyState === WebSocket.OPEN && currentThreadId) {
        ws.send(JSON.stringify({
            type: 'message',
            content: message,
            message_type: 'text'
        }));
        input.value = '';
        input.style.height = 'auto';
        updateSendButton();
    } else if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert('WebSocket is not connected');
    } else if (!currentThreadId) {
        alert('No thread selected');
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