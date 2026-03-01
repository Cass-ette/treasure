// ai-assistant.js — Chat interface for AI analysis assistant

var chatMessages = document.getElementById('chatMessages');
var chatInput = document.getElementById('chatInput');
var sendBtn = document.getElementById('sendBtn');
var typingIndicator = document.getElementById('typingIndicator');

// Auto-resize textarea
if (chatInput) {
    chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    chatInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

function askSuggestion(btn) {
    chatInput.value = btn.textContent;
    sendMessage();
}

function sendMessage() {
    var text = chatInput.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    chatInput.value = '';
    chatInput.style.height = 'auto';
    setLoading(true);

    fetch('/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        setLoading(false);
        if (data.error) {
            appendMessage('抱歉，出现错误: ' + data.error, 'ai');
        } else {
            appendMessage(data.reply, 'ai');
        }
    })
    .catch(function (err) {
        setLoading(false);
        appendMessage('网络请求失败，请重试。', 'ai');
    });
}

function appendMessage(text, role) {
    var msgDiv = document.createElement('div');
    msgDiv.className = 'msg msg-' + role;

    var icon = document.createElement('div');
    icon.className = 'msg-icon';
    icon.innerHTML = role === 'user'
        ? '<i class="bi bi-person"></i>'
        : '<i class="bi bi-robot"></i>';

    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text;

    msgDiv.appendChild(icon);
    msgDiv.appendChild(bubble);

    // Insert before typing indicator
    chatMessages.insertBefore(msgDiv, typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setLoading(loading) {
    typingIndicator.style.display = loading ? 'block' : 'none';
    sendBtn.disabled = loading;
    chatInput.disabled = loading;
    if (loading) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

window.sendMessage = sendMessage;
window.askSuggestion = askSuggestion;
