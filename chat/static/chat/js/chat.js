class ChatClient {
    constructor(roomName, userId, receiverId) {
        this.roomName = roomName;
        this.userId = userId;
        this.receiverId = receiverId;
        this.socket = null;
        this.typingTimeout = null;
        this.typingIndicatorShown = false;
        this.initialize();
    }

    initialize() {
        // Initialize WebSocket connection
        const wsScheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsPath = `${wsScheme}${window.location.host}/ws/chat/${this.roomName}/`;
        this.socket = new WebSocket(wsPath);

        // Set up event handlers
        this.socket.onopen = this.onSocketOpen.bind(this);
        this.socket.onmessage = this.onSocketMessage.bind(this);
        this.socket.onclose = this.onSocketClose.bind(this);
        this.socket.onerror = this.onSocketError.bind(this);

        // Set up UI event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Message form submission
        const messageForm = document.getElementById('message-form');
        if (messageForm) {
            messageForm.addEventListener('submit', this.onMessageSubmit.bind(this));
        }

        // Typing indicator
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.addEventListener('input', this.onTyping.bind(this));
            messageInput.addEventListener('blur', this.onStopTyping.bind(this));
        }

        // Mark messages as read when chat is visible
        document.addEventListener('visibilitychange', this.onVisibilityChange.bind(this));
        window.addEventListener('focus', this.markMessagesAsRead.bind(this));
    }

    onSocketOpen() {
        console.log('WebSocket connection established');
        this.markMessagesAsRead();
    }

    onSocketMessage(event) {
        const data = JSON.parse(event.data);
        console.log('Message received:', data);

        switch (data.type) {
            case 'chat_message':
                this.handleChatMessage(data);
                break;
            case 'typing_indicator':
                this.handleTypingIndicator(data);
                break;
            case 'notification':
                this.handleNotification(data);
                break;
            case 'message_read':
                this.handleMessageRead(data);
                break;
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    onSocketClose(event) {
        console.log('WebSocket connection closed:', event);
        // Attempt to reconnect after a delay
        setTimeout(() => this.initialize(), 5000);
    }

    onSocketError(error) {
        console.error('WebSocket error:', error);
    }

    onMessageSubmit(event) {
        event.preventDefault();
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();

        if (message && this.socket.readyState === WebSocket.OPEN) {
            this.sendMessage(message);
            messageInput.value = '';
            this.onStopTyping();
        }
    }

    onTyping() {
        if (!this.typingIndicatorShown) {
            this.sendTypingIndicator(true);
            this.typingIndicatorShown = true;
        }

        // Reset the typing indicator after 3 seconds of inactivity
        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.onStopTyping();
        }, 3000);
    }

    onStopTyping() {
        if (this.typingIndicatorShown) {
            this.sendTypingIndicator(false);
            this.typingIndicatorShown = false;
        }
    }

    onVisibilityChange() {
        if (document.visibilityState === 'visible') {
            this.markMessagesAsRead();
        }
    }

    sendMessage(message) {
        const messageData = {
            type: 'chat_message',
            message: message,
            receiver_id: this.receiverId
        };
        this.socket.send(JSON.stringify(messageData));
    }

    sendTypingIndicator(isTyping) {
        const typingData = {
            type: 'typing',
            is_typing: isTyping,
            receiver_id: this.receiverId
        };
        this.socket.send(JSON.stringify(typingData));
    }

    markMessagesAsRead() {
        const unreadMessages = document.querySelectorAll('.message:not(.read)');
        if (unreadMessages.length > 0) {
            const messageIds = Array.from(unreadMessages).map(msg => msg.dataset.messageId);
            
            // Mark messages as read in the UI
            unreadMessages.forEach(msg => msg.classList.add('read'));
            
            // Send read receipt for each message
            messageIds.forEach(messageId => {
                this.socket.send(JSON.stringify({
                    type: 'read_receipt',
                    message_id: messageId
                }));
            });
            
            // Update unread count in the UI
            this.updateUnreadCount();
        }
    }

    handleChatMessage(data) {
        // Add message to the chat UI
        const messagesContainer = document.querySelector('.messages-container');
        if (messagesContainer) {
            const messageElement = this.createMessageElement(data);
            messagesContainer.appendChild(messageElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Update last message in the chat list
        this.updateChatListLastMessage(data);
        
        // Show desktop notification if tab is not active
        if (document.visibilityState !== 'visible') {
            this.showNotification(data);
        }
    }

    handleTypingIndicator(data) {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.textContent = data.is_typing 
                ? `${data.username} is typing...` 
                : '';
        }
    }

    handleNotification(data) {
        // Show desktop notification
        this.showNotification(data);
        
        // Update unread count in the UI
        this.updateUnreadCount();
    }

    handleMessageRead(data) {
        // Update message read status in the UI
        const messageElement = document.querySelector(`.message[data-message-id="${data.message_id}"]`);
        if (messageElement) {
            messageElement.classList.add('read');
            
            const readStatus = messageElement.querySelector('.read-status');
            if (readStatus) {
                readStatus.textContent = 'Read';
            }
        }
    }

    createMessageElement(data) {
        const isCurrentUser = data.sender_id == this.userId;
        const messageClass = isCurrentUser ? 'message sent' : 'message received';
        
        const messageElement = document.createElement('div');
        messageElement.className = messageClass;
        messageElement.dataset.messageId = data.message_id;
        
        const messageContent = `
            <div class="message-content">${data.message}</div>
            <div class="message-time">
                ${new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                <span class="read-status">${data.is_read ? '✓✓' : '✓'}</span>
            </div>
        `;
        
        messageElement.innerHTML = messageContent;
        return messageElement;
    }

    updateChatListLastMessage(data) {
        // Find the chat in the sidebar and update its last message
        const chatElement = document.querySelector(`.chat-list-item[data-user-id="${data.sender_id}"]`);
        if (chatElement) {
            const lastMessageElement = chatElement.querySelector('.last-message');
            const timestampElement = chatElement.querySelector('.timestamp');
            
            if (lastMessageElement) {
                lastMessageElement.textContent = data.message;
            }
            
            if (timestampElement) {
                timestampElement.textContent = new Date(data.timestamp).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
            }
            
            // Move chat to top of the list
            const chatList = chatElement.parentElement;
            if (chatList.firstChild !== chatElement) {
                chatList.insertBefore(chatElement, chatList.firstChild);
            }
        }
    }

    updateUnreadCount() {
        // Update unread count in the chat list and title
        const unreadCount = document.querySelectorAll('.message:not(.read)').length;
        document.title = unreadCount > 0 
            ? `(${unreadCount}) Chat App` 
            : 'Chat App';
            
        // Update unread badge if it exists
        const unreadBadge = document.getElementById('unread-badge');
        if (unreadBadge) {
            unreadBadge.textContent = unreadCount > 0 ? unreadCount : '';
            unreadBadge.style.display = unreadCount > 0 ? 'inline-block' : 'none';
        }
    }

    showNotification(data) {
        if (Notification.permission === 'granted') {
            const notification = new Notification(
                `New message from ${data.sender_username || 'User'}`,
                {
                    body: data.message,
                    icon: data.sender_avatar || '/static/img/default-avatar.png',
                    tag: `chat-${this.roomName}`
                }
            );
            
            // Focus the chat window when notification is clicked
            notification.onclick = () => {
                window.focus();
                this.markMessagesAsRead();
                notification.close();
            };
        }
    }
}

// Initialize chat when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        const roomName = chatContainer.dataset.roomName;
        const userId = chatContainer.dataset.userId;
        const receiverId = chatContainer.dataset.receiverId;
        
        if (roomName && userId && receiverId) {
            window.chatClient = new ChatClient(roomName, userId, receiverId);
        }
    }
    
    // Request notification permission
    if (Notification.permission !== 'denied') {
        Notification.requestPermission();
    }
});
