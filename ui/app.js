// ==================== Configuration ====================
const CONFIG = {
    wsUrl: 'ws://localhost:8001/ws',
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    typingDelay: 50,
};

// ==================== State Management ====================
let ws = null;
let reconnectAttempts = 0;
let isConnected = false;
let messageQueue = [];

// ==================== DOM Elements ====================
const elements = {
    welcomeScreen: document.getElementById('welcomeScreen'),
    messagesArea: document.getElementById('messagesArea'),
    messageInput: document.getElementById('messageInput'),
    sendButton: document.getElementById('sendButton'),
    typingIndicator: document.getElementById('typingIndicator'),
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),
    charCount: document.getElementById('charCount'),
};

// ==================== WebSocket Connection ====================
function connectWebSocket() {
    try {
        ws = new WebSocket(CONFIG.wsUrl);

        ws.onopen = handleWebSocketOpen;
        ws.onmessage = handleWebSocketMessage;
        ws.onerror = handleWebSocketError;
        ws.onclose = handleWebSocketClose;
    } catch (error) {
        console.error('WebSocket connection error:', error);
        updateConnectionStatus('disconnected');
        scheduleReconnect();
    }
}

function handleWebSocketOpen() {
    console.log('WebSocket connected');
    isConnected = true;
    reconnectAttempts = 0;
    updateConnectionStatus('connected');

    // Send queued messages
    while (messageQueue.length > 0) {
        const message = messageQueue.shift();
        sendMessage(message);
    }
}

function handleWebSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);
        console.log('Received message:', data);

        // Transform typing indicator into message
        if (data.type === 'response') {
            transformTypingToMessage(data.message || data.text);
        } else if (data.type === 'error') {
            transformTypingToMessage('Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.');
        }
    } catch (error) {
        console.error('Error parsing message:', error);
        transformTypingToMessage('Xin lỗi, không thể xử lý phản hồi.');
    }
}

function handleWebSocketError(error) {
    console.error('WebSocket error:', error);
    updateConnectionStatus('disconnected');
}

function handleWebSocketClose(event) {
    console.log('WebSocket disconnected:', event.code, event.reason);
    isConnected = false;
    updateConnectionStatus('disconnected');
    hideTypingIndicator();

    // Attempt to reconnect
    if (reconnectAttempts < CONFIG.maxReconnectAttempts) {
        scheduleReconnect();
    }
}

function scheduleReconnect() {
    reconnectAttempts++;
    updateConnectionStatus('connecting');

    setTimeout(() => {
        console.log(`Reconnecting... Attempt ${reconnectAttempts}/${CONFIG.maxReconnectAttempts}`);
        connectWebSocket();
    }, CONFIG.reconnectInterval);
}

function updateConnectionStatus(status) {
    const statusMap = {
        connected: {
            text: 'Đã kết nối',
            class: 'connected',
        },
        connecting: {
            text: 'Đang kết nối...',
            class: 'connecting',
        },
        disconnected: {
            text: 'Mất kết nối',
            class: 'disconnected',
        },
    };

    const statusInfo = statusMap[status] || statusMap.disconnected;
    elements.statusText.textContent = statusInfo.text;
    elements.statusDot.className = `status-dot ${statusInfo.class}`;
}

// ==================== Message Handling ====================
function sendMessageToServer(message) {
    if (!message || !message.trim()) return;

    const payload = {
        type: 'message',
        message: message.trim(),
        timestamp: new Date().toISOString(),
    };

    if (isConnected && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload));
        showTypingIndicator();
    } else {
        // Queue message if not connected
        messageQueue.push(message);
        addMessage('Đang kết nối lại, tin nhắn sẽ được gửi khi kết nối thành công...', 'bot');
    }
}

function sendMessage(message = null) {
    const text = message || elements.messageInput.value.trim();

    if (!text) return;

    // Hide welcome screen on first message
    if (elements.welcomeScreen && !elements.welcomeScreen.classList.contains('hidden')) {
        elements.welcomeScreen.classList.add('hidden');
    }

    // Add user message to UI
    addMessage(text, 'user');

    // Send to server
    sendMessageToServer(text);

    // Clear input
    if (!message) {
        elements.messageInput.value = '';
        updateCharCount();
        updateSendButtonState();
        autoResizeTextarea();
    }
}

function sendSuggestion(text) {
    sendMessage(text);
}

function addMessage(text, sender, animated = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';

    // If animated (bot typing effect), start empty and type out
    if (animated && sender === 'bot') {
        bubbleDiv.textContent = '';
        typeText(bubbleDiv, text);
    } else {
        // Parse and render markdown for bot messages
        if (sender === 'bot') {
            bubbleDiv.innerHTML = parseMarkdown(text);
        } else {
            bubbleDiv.textContent = text;
        }
    }

    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatTime(new Date());

    contentDiv.appendChild(bubbleDiv);
    contentDiv.appendChild(timeDiv);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    elements.messagesArea.appendChild(messageDiv);

    // Add smooth appearance
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(10px)';
    messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

    setTimeout(() => {
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 10);

    scrollToBottom();

    return messageDiv;
}

function parseMarkdown(text) {
    if (!text) return '';

    return text
        // Code blocks with backticks
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        // Inline code with single backticks
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Bold with ** or __
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>')
        // Italic with * or _
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/_(.*?)_/g, '<em>$1</em>')
        // Line breaks
        .replace(/\n/g, '<br>')
        // Lists (basic support)
        .replace(/^\s*[\-\*]\s+(.+)$/gm, '<li>$1</li>')
        // Convert li groups to ul
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
}

// Typing animation effect
function typeText(element, text, speed = 30) {
    let index = 0;
    const interval = setInterval(() => {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            index++;
            scrollToBottom();
        } else {
            clearInterval(interval);
        }
    }, speed);
}

function showTypingIndicator() {
    // Create message structure first (hidden)
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.id = 'typing-message-container';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble typing-bubble';
    bubbleDiv.id = 'typing-bubble-content';

    // Add typing dots
    const dotsContainer = document.createElement('div');
    dotsContainer.className = 'typing-dots';
    dotsContainer.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    bubbleDiv.appendChild(dotsContainer);

    contentDiv.appendChild(bubbleDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    elements.messagesArea.appendChild(messageDiv);

    // Fade in
    setTimeout(() => {
        messageDiv.style.opacity = '1';
    }, 10);

    scrollToBottom();
}

function transformTypingToMessage(text) {
    const typingContainer = document.getElementById('typing-message-container');
    const bubbleContent = document.getElementById('typing-bubble-content');

    if (!typingContainer || !bubbleContent) {
        // Fallback if typing indicator doesn't exist
        addMessage(text, 'bot', false); // Changed to false to show immediately
        return;
    }

    // Clear the typing dots
    bubbleContent.innerHTML = '';

    // Remove typing-bubble class
    bubbleContent.classList.remove('typing-bubble');

    // Parse and render markdown content
    const formattedText = parseMarkdown(text);
    bubbleContent.innerHTML = formattedText;

    // Add timestamp
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatTime(new Date());
    typingContainer.querySelector('.message-content').appendChild(timeDiv);

    // Remove the ID so it won't be reused
    typingContainer.removeAttribute('id');
    bubbleContent.removeAttribute('id');

    // Add smooth fade-in effect
    bubbleContent.style.opacity = '0';
    bubbleContent.style.transition = 'opacity 0.3s ease-in-out';

    setTimeout(() => {
        bubbleContent.style.opacity = '1';
    }, 10);

    scrollToBottom();
}

function scrollToBottom() {
    setTimeout(() => {
        elements.messagesArea.parentElement.scrollTop = elements.messagesArea.parentElement.scrollHeight;
    }, 100);
}

// ==================== Input Handling ====================
function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 120) + 'px';
}

function updateCharCount() {
    const count = elements.messageInput.value.length;
    elements.charCount.textContent = count;

    if (count > 450) {
        elements.charCount.parentElement.style.color = '#e74c3c';
    } else if (count > 400) {
        elements.charCount.parentElement.style.color = '#f39c12';
    } else {
        elements.charCount.parentElement.style.color = 'var(--text-light)';
    }
}

function updateSendButtonState() {
    const hasText = elements.messageInput.value.trim().length > 0;
    elements.sendButton.disabled = !hasText || !isConnected;
}

// ==================== Utility Functions ====================
function formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

// ==================== Event Listeners ====================
function initializeEventListeners() {
    // Send button click
    elements.sendButton.addEventListener('click', () => sendMessage());

    // Enter key to send (Shift+Enter for new line)
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    elements.messageInput.addEventListener('input', () => {
        autoResizeTextarea();
        updateCharCount();
        updateSendButtonState();
    });

    // Focus input on load
    elements.messageInput.focus();

    // Handle page visibility change
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && !isConnected) {
            connectWebSocket();
        }
    });

    // Handle page unload
    window.addEventListener('beforeunload', () => {
        if (ws) {
            ws.close();
        }
    });
}

// ==================== Initialization ====================
function initialize() {
    console.log('Initializing Travel Chatbot...');

    // Initialize event listeners
    initializeEventListeners();

    // Connect to WebSocket
    connectWebSocket();

    // Initial UI state
    updateCharCount();
    updateSendButtonState();

    console.log('Travel Chatbot initialized successfully');
}

// Start the application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}

// ==================== Test Functions ====================
function testTypingIndicator() {
    // Hide welcome screen
    if (elements.welcomeScreen && !elements.welcomeScreen.classList.contains('hidden')) {
        elements.welcomeScreen.classList.add('hidden');
    }

    // Add user message
    addMessage('Xin chào! Tôi muốn biết về các địa điểm du lịch ở Hà Nội.', 'user');

    // Show typing indicator
    showTypingIndicator();

    // Simulate bot response after 3 seconds
    setTimeout(() => {
        transformTypingToMessage('Chào bạn! Hà Nội có rất nhiều địa điểm du lịch tuyệt vời như Hồ Hoàn Kiếm, Văn Miếu Quốc Tử Giám, Phố cổ Hà Nội, và nhiều nơi khác. Bạn muốn tìm hiểu chi tiết về địa điểm nào?');
    }, 3000);
}

// ==================== Global Functions ====================
// Make functions available globally for onclick handlers
window.sendSuggestion = sendSuggestion;
window.testTypingIndicator = testTypingIndicator;
