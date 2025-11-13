// ==================== Configuration ====================
const CONFIG = {
    wsUrl: 'ws://localhost:8000/ws',
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
    settingsModal: document.getElementById('settingsModal'),
    modalCloseButton: document.getElementById('modalCloseButton'),
    modalCancelButton: document.getElementById('modalCancelButton'),
    currentModel: document.getElementById('currentModel'),
    modelList: document.getElementById('modelList'),
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
            transformTypingToMessage(data.message || data.text, data.sources);
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
        disableInput();
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
        .replace(/\n\s*\n+/g, '\n')
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>')
        .replace(/(<li>.*?<\/li>)(\s*<li>.*?<\/li>)*/gs, (match) => {
            return '<ul>' + match + '</ul>';
        })
        .replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
        .replace(/(?<!_)_(?!_)(.*?)(?<!_)_(?!_)/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
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

function transformTypingToMessage(text, sources = []) {
    const typingContainer = document.getElementById('typing-message-container');
    const bubbleContent = document.getElementById('typing-bubble-content');

    if (!typingContainer || !bubbleContent) {
        // Fallback if typing indicator doesn't exist
        addMessage(text, 'bot', false); // Changed to false to show immediately
        enableInput();
        return;
    }

    // Clear the typing dots
    bubbleContent.innerHTML = '';

    // Remove typing-bubble class
    bubbleContent.classList.remove('typing-bubble');

    // Parse and render markdown content
    const formattedText = parseMarkdown(text);
    bubbleContent.innerHTML = formattedText;

    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesContainer = document.createElement('div');
        sourcesContainer.className = 'message-sources';

        // Get unique sources (deduplicate by source_file)
        const uniqueSources = [];
        const seenFiles = new Set();

        for (const source of sources) {
            if (source.source_file && !seenFiles.has(source.source_file)) {
                uniqueSources.push(source);
                seenFiles.add(source.source_file);
            }
        }

        console.log('Unique sources:', uniqueSources);
        // Show first source as main reference
        if (uniqueSources.length > 0) {
            const firstSource = uniqueSources[0];
            const sourceDiv = document.createElement('div');
            sourceDiv.className = 'source-item';

            const sourceLabel = document.createElement('span');
            sourceLabel.className = 'source-label';
            sourceLabel.textContent = '📚: ';

            const sourceWrapper = document.createElement('div');
            sourceWrapper.className = 'source-wrapper';

            const sourceLink = document.createElement('a');
            sourceLink.href = firstSource.source_file;
            sourceLink.target = '_blank';
            sourceLink.className = 'source-link';
            sourceLink.textContent = 'Tài liệu tham khảo';
            sourceLink.rel = 'noopener noreferrer';

            // Create tooltip with all topics from this source
            const tooltip = document.createElement('div');
            tooltip.className = 'source-tooltip';

            const tooltipTitle = document.createElement('div');
            tooltipTitle.className = 'tooltip-title';
            tooltipTitle.textContent = 'Topic:';
            tooltip.appendChild(tooltipTitle);

            const tooltipTopics = document.createElement('div');
            tooltipTopics.className = 'tooltip-topics';

            // Add all topics from all sources with same source_file (deduplicate)
            const seenTopics = new Set();
            for (const source of sources) {
                if (source.source_file === firstSource.source_file && source.topic) {
                    if (!seenTopics.has(source.topic)) {
                        seenTopics.add(source.topic);
                        const topicItem = document.createElement('div');
                        topicItem.className = 'tooltip-topic-item';
                        topicItem.textContent = '• ' + source.topic;
                        tooltipTopics.appendChild(topicItem);
                    }
                }
            }

            tooltip.appendChild(tooltipTopics);
            sourceWrapper.appendChild(sourceLink);
            sourceWrapper.appendChild(tooltip);

            sourceDiv.appendChild(sourceLabel);
            sourceDiv.appendChild(sourceWrapper);
            sourcesContainer.appendChild(sourceDiv);
        }

        // Show additional topics if available
        if (uniqueSources.length > 1) {
            const topicsDiv = document.createElement('div');
            topicsDiv.className = 'related-topics';

            const topicsLabel = document.createElement('div');
            topicsLabel.className = 'topics-label';
            topicsLabel.textContent = 'Các chủ đề liên quan:';
            topicsDiv.appendChild(topicsLabel);

            const topicsList = document.createElement('div');
            topicsList.className = 'topics-list';

            for (let i = 1; i < uniqueSources.length && i < 4; i++) {
                if (!uniqueSources[i].topic) continue;
                const topic = uniqueSources[i];
                const topicLink = document.createElement('a');
                topicLink.href = topic.source_file;
                topicLink.target = '_blank';
                topicLink.className = 'topic-tag';
                topicLink.textContent = topic.topic;
                topicLink.rel = 'noopener noreferrer';
                topicsList.appendChild(topicLink);
            }

            topicsDiv.appendChild(topicsList);
            sourcesContainer.appendChild(topicsDiv);
        }

        bubbleContent.appendChild(sourcesContainer);
    }

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
    enableInput();
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

// ==================== Input State Management ====================
function disableInput() {
    elements.messageInput.disabled = true;
    elements.sendButton.disabled = true;
    elements.messageInput.style.opacity = '0.6';
    elements.messageInput.style.cursor = 'not-allowed';
}

function enableInput() {
    elements.messageInput.disabled = false;
    elements.messageInput.style.opacity = '1';
    elements.messageInput.style.cursor = 'text';
    updateSendButtonState();
}

// ==================== Settings Handler ====================
function handleSettingsClick() {
    console.log('Settings clicked - LLM Model Configuration');
    openSettingsModal();
}

function openSettingsModal() {
    if (elements.settingsModal) {
        elements.settingsModal.classList.add('active');
        loadModelConfiguration();
    }
}

function closeSettingsModal() {
    if (elements.settingsModal) {
        elements.settingsModal.classList.remove('active');
    }
}

async function loadModelConfiguration() {
    try {
        // Fetch current model and available models from backend
        const response = await fetch('/api/models');
        const data = await response.json();

        await loadAvailableModels(data.models, data.current);
    } catch (error) {
        console.error('Error loading model configuration:', error);
        elements.modelList.innerHTML = '<div style="color: #e74c3c; padding: 1rem;">Lỗi tải danh sách model</div>';
    }
}

async function loadAvailableModels(models = null, currentModel = null) {
    if (!elements.modelList) return;

    try {
        // Use provided models or mock data
        const modelList = models || [
            { name: 'llama3.1', type: 'Ollama', status: 'available' },
            { name: 'qwen3:7b', type: 'Ollama', status: 'available' },
            { name: 'qwen3:0.6b', type: 'Ollama', status: 'available' },
        ];

        elements.modelList.innerHTML = '';

        // Get current model if not provided
        if (!currentModel) {
            const response = await fetch('/api/models');
            const data = await response.json();
            currentModel = data.current;
        }

        modelList.forEach(model => {
            const isActive = model.name === currentModel;
            const modelElement = document.createElement('div');
            modelElement.className = `model-item ${isActive ? 'active' : ''}`;
            modelElement.innerHTML = `
                <div class="model-item-name">
                    ${model.name}
                    <small style="display: block; color: var(--text-secondary); font-weight: 400; margin-top: 0.25rem;">${model.type}</small>
                </div>
                <div class="model-item-status">
                    ${isActive ? '✓' : ''}
                </div>
            `;

            // Disable click nếu là model hiện tại
            if (!isActive) {
                modelElement.style.cursor = 'pointer';
                modelElement.addEventListener('click', () => selectModel(model.name, modelElement));
            } else {
                modelElement.style.cursor = 'default';
                modelElement.style.opacity = '0.7';
            }

            elements.modelList.appendChild(modelElement);
        });
    } catch (error) {
        console.error('Error loading models:', error);
        elements.modelList.innerHTML = '<div style="color: #e74c3c; padding: 1rem;">Không thể tải danh sách model</div>';
    }
}

async function selectModel(modelName, element) {
    try {
        console.log('Selecting model:', modelName);

        // Show loading overlay
        const modelSwitchingOverlay = document.getElementById('modelSwitchingOverlay');
        if (modelSwitchingOverlay) {
            modelSwitchingOverlay.classList.add('active');
        }

        // Disable all model items and input
        const allModelItems = document.querySelectorAll('.model-item');
        allModelItems.forEach(item => {
            item.style.pointerEvents = 'none';
            item.style.opacity = '0.5';
        });
        disableInput();

        // Send request to backend to switch model
        const response = await fetch(`/api/model/switch?model_name=${modelName}`, {
            method: 'POST'
        });
        const result = await response.json();

        if (result.status === 'success') {
            console.log('Model switched successfully:', modelName);

            // Wait a bit to ensure backend is ready
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Update active state in UI
            allModelItems.forEach(item => {
                item.classList.remove('active');
                item.style.opacity = '1';
                item.style.pointerEvents = 'auto';
                item.style.cursor = 'pointer';
                // Update checkbox: remove ✓
                const statusDiv = item.querySelector('.model-item-status');
                if (statusDiv) {
                    statusDiv.textContent = '';
                }
            });

            element.classList.add('active');
            element.style.cursor = 'default';
            element.style.opacity = '0.7';
            element.style.pointerEvents = 'none';

            // Update checkbox for selected model: add ✓
            const statusDiv = element.querySelector('.model-item-status');
            if (statusDiv) {
                statusDiv.textContent = '✓';
            }

            // Hide loading overlay
            if (modelSwitchingOverlay) {
                modelSwitchingOverlay.classList.remove('active');
            }

            // Re-enable input
            enableInput();
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('Error selecting model:', error);

        // Hide loading overlay on error
        const modelSwitchingOverlay = document.getElementById('modelSwitchingOverlay');
        if (modelSwitchingOverlay) {
            modelSwitchingOverlay.classList.remove('active');
        }

        // Re-enable items on error
        const allModelItems = document.querySelectorAll('.model-item');
        allModelItems.forEach(item => {
            item.style.pointerEvents = 'auto';
            item.style.opacity = '1';
        });
        enableInput();

        // Show error message
        addMessage(`❌ Lỗi chuyển model: ${error.message}`, 'bot');
    }
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

    // Settings button click
    const settingsButton = document.getElementById('settingsButton');
    if (settingsButton) {
        settingsButton.addEventListener('click', handleSettingsClick);
    }

    // Modal close buttons
    if (elements.modalCloseButton) {
        elements.modalCloseButton.addEventListener('click', closeSettingsModal);
    }
    if (elements.modalCancelButton) {
        elements.modalCancelButton.addEventListener('click', closeSettingsModal);
    }

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

// ==================== Global Functions ====================
// Make functions available globally for onclick handlers
window.sendSuggestion = sendSuggestion;
