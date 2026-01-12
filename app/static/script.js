/**
 * Frontend JavaScript for RAG AI Agent
 * Handles API communication, message rendering, and user interactions
 */

// Global state
let sessionId = null;
let isProcessing = false;

// DOM Elements
const messagesWrapper = document.getElementById('messagesWrapper');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const sessionIdDisplay = document.getElementById('sessionId');
const charCount = document.getElementById('charCount');
const providerName = document.getElementById('providerName');
const vectorStore = document.getElementById('vectorStore');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setupEventListeners();
    autoResizeTextarea();
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Send button click
    sendButton.addEventListener('click', sendMessage);

    // Enter key to send (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Character counter
    userInput.addEventListener('input', () => {
        charCount.textContent = userInput.value.length;
        autoResizeTextarea();
    });
}

/**
 * Auto-resize textarea based on content
 */
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = userInput.scrollHeight + 'px';
}

/**
 * Check API health and update status
 */
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();

        if (data.status === 'healthy') {
            updateStatus('connected', 'Connected');
            providerName.textContent = data.llm_provider.toUpperCase();
            vectorStore.textContent = data.vector_store.toUpperCase();
        } else {
            updateStatus('error', 'Error');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatus('error', 'Disconnected');
    }
}

/**
 * Update connection status indicator
 */
function updateStatus(status, text) {
    statusDot.className = 'status-dot ' + status;
    statusText.textContent = text;
}

/**
 * Send a message to the API
 */
async function sendMessage() {
    const query = userInput.value.trim();

    if (!query || isProcessing) {
        return;
    }

    // Clear input and disable button
    userInput.value = '';
    charCount.textContent = '0';
    autoResizeTextarea();
    isProcessing = true;
    sendButton.disabled = true;

    // Remove welcome message if present
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Add user message to UI
    addMessage('user', query);

    // Add loading indicator
    const loadingId = addLoadingIndicator();

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Update session ID
        if (data.session_id) {
            sessionId = data.session_id;
            sessionIdDisplay.textContent = sessionId.substring(0, 8) + '...';
        }

        // Remove loading indicator
        removeLoadingIndicator(loadingId);

        // Add assistant response
        addMessage('assistant', data.answer, data.sources, data.used_rag);

    } catch (error) {
        console.error('Error sending message:', error);
        removeLoadingIndicator(loadingId);
        addMessage('assistant', 'Sorry, I encountered an error processing your request. Please try again.', [], false);
    } finally {
        isProcessing = false;
        sendButton.disabled = false;
        userInput.focus();
    }
}

/**
 * Add a message to the chat
 */
function addMessage(role, content, sources = [], usedRag = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = role === 'user' ? 'You' : 'AI Assistant';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    // Format content with line breaks
    const formattedContent = content.replace(/\n/g, '<br>');
    messageContent.innerHTML = formattedContent;

    messageDiv.appendChild(label);
    messageDiv.appendChild(messageContent);

    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';

        const sourcesLabel = document.createElement('div');
        sourcesLabel.className = 'sources-label';
        sourcesLabel.textContent = '📚 Sources:';
        sourcesDiv.appendChild(sourcesLabel);

        sources.forEach(source => {
            const sourceTag = document.createElement('span');
            sourceTag.className = 'source-tag';
            sourceTag.textContent = source;
            sourcesDiv.appendChild(sourceTag);
        });

        messageContent.appendChild(sourcesDiv);
    }

    messagesWrapper.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Add loading indicator
 */
function addLoadingIndicator() {
    const loadingId = 'loading-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = loadingId;

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = 'AI Assistant';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = `
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
    `;

    messageContent.appendChild(loadingIndicator);
    messageDiv.appendChild(label);
    messageDiv.appendChild(messageContent);
    messagesWrapper.appendChild(messageDiv);

    scrollToBottom();
    return loadingId;
}

/**
 * Remove loading indicator
 */
function removeLoadingIndicator(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        loadingElement.remove();
    }
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    messagesWrapper.scrollTop = messagesWrapper.scrollHeight;
}

/**
 * Ask an example question (called from HTML)
 */
function askExample(question) {
    userInput.value = question;
    charCount.textContent = question.length;
    autoResizeTextarea();
    userInput.focus();
    sendMessage();
}

/**
 * Format timestamp
 */
function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Periodically check health
setInterval(checkHealth, 30000); // Every 30 seconds
