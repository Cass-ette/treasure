// ai-assistant.js — Chat interface with multi-model & conversation management

var chatMessages = document.getElementById('chatMessages');
var chatInput = document.getElementById('chatInput');
var sendBtn = document.getElementById('sendBtn');
var typingIndicator = document.getElementById('typingIndicator');
var modelSelect = document.getElementById('modelSelect');

// 当前会话状态
var chatHistory = [];       // [{role, content}, ...]
var currentConvId = null;   // 正在编辑的对话 ID
var conversations = window.__conversations || [];

// ── 初始化 ───────────────────────────────────────────────

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

renderConvList();

// ── 发送消息 ─────────────────────────────────────────────

function askSuggestion(btn) {
    chatInput.value = btn.textContent;
    sendMessage();
}

function sendMessage() {
    var text = chatInput.value.trim();
    if (!text) return;

    chatHistory.push({ role: 'user', content: text });
    appendMessage(text, 'user');
    chatInput.value = '';
    chatInput.style.height = 'auto';
    setLoading(true);

    fetch('/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, model: modelSelect.value })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        setLoading(false);
        if (data.error) {
            appendMessage('抱歉，出现错误: ' + data.error, 'ai');
        } else {
            chatHistory.push({ role: 'assistant', content: data.reply });
            appendMessage(data.reply, 'ai');
        }
    })
    .catch(function () {
        setLoading(false);
        appendMessage('网络请求失败，请重试。', 'ai');
    });
}

// ── DOM 操作 ─────────────────────────────────────────────

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

// ── 新对话 ───────────────────────────────────────────────

function newConversation() {
    chatHistory = [];
    currentConvId = null;
    // 清除聊天区，保留欢迎消息和 typing indicator
    var welcome = document.getElementById('welcomeMsg');
    while (chatMessages.firstChild) {
        chatMessages.removeChild(chatMessages.firstChild);
    }
    if (welcome) {
        chatMessages.appendChild(welcome);
    }
    chatMessages.appendChild(typingIndicator);
}

// ── 保存对话 ─────────────────────────────────────────────

function saveConversation() {
    if (chatHistory.length === 0) {
        alert('当前没有对话内容可保存');
        return;
    }

    var defaultTitle = chatHistory[0].content.substring(0, 30);
    var title = prompt('对话标题', defaultTitle);
    if (title === null) return;

    fetch('/ai/conversations/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            id: currentConvId,
            title: title || defaultTitle,
            messages: chatHistory,
            model: modelSelect.value
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.error) {
            alert(data.error);
            return;
        }
        currentConvId = data.id;
        refreshConvList();
    });
}

// ── 加载对话 ─────────────────────────────────────────────

function loadConversation(id) {
    fetch('/ai/conversations/' + id)
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.error) {
            alert(data.error);
            return;
        }
        currentConvId = data.id;
        chatHistory = data.messages || [];
        if (data.model) modelSelect.value = data.model;

        // 清空聊天区并渲染历史消息
        while (chatMessages.firstChild) {
            chatMessages.removeChild(chatMessages.firstChild);
        }
        chatMessages.appendChild(typingIndicator);

        chatHistory.forEach(function (msg) {
            var role = msg.role === 'user' ? 'user' : 'ai';
            appendMessage(msg.content, role);
        });

        // 关闭侧栏
        var offcanvas = bootstrap.Offcanvas.getInstance(document.getElementById('historyPanel'));
        if (offcanvas) offcanvas.hide();
    });
}

// ── 删除对话 ─────────────────────────────────────────────

function deleteConversation(id, evt) {
    evt.stopPropagation();
    if (!confirm('确定删除这条对话？')) return;

    fetch('/ai/conversations/' + id, { method: 'DELETE' })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.ok) {
            if (currentConvId === id) {
                newConversation();
            }
            refreshConvList();
        }
    });
}

// ── 对话列表 ─────────────────────────────────────────────

function refreshConvList() {
    fetch('/ai/conversations')
    .then(function (r) { return r.json(); })
    .then(function (data) {
        conversations = data;
        renderConvList();
    });
}

function renderConvList() {
    var container = document.getElementById('convList');
    if (!container) return;

    if (!conversations || conversations.length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-4">暂无保存的对话</div>';
        return;
    }

    var html = '';
    conversations.forEach(function (c) {
        html += '<div class="conv-list-item" onclick="loadConversation(' + c.id + ')">'
            + '<span class="conv-title">' + escapeHtml(c.title) + '</span>'
            + '<span class="conv-meta">' + c.updated_at + '</span>'
            + '<button class="btn-close" onclick="deleteConversation(' + c.id + ', event)"></button>'
            + '</div>';
    });
    container.innerHTML = html;
}

// ── 设置 ─────────────────────────────────────────────────

function saveSettings() {
    var body = {
        deepseek_api_key: document.getElementById('settingDeepseekKey').value.trim(),
        anthropic_api_key: document.getElementById('settingClaudeKey').value.trim(),
        preferred_model: document.getElementById('settingDefaultModel').value
    };

    fetch('/ai/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.ok) {
            location.reload();
        } else {
            alert(data.error || '保存失败');
        }
    });
}

// ── 导出数据 ─────────────────────────────────────────────

function exportContext() {
    window.location.href = '/ai/export-context';
}

// ── 工具函数 ─────────────────────────────────────────────

function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// 暴露全局函数
window.sendMessage = sendMessage;
window.askSuggestion = askSuggestion;
window.newConversation = newConversation;
window.saveConversation = saveConversation;
window.loadConversation = loadConversation;
window.deleteConversation = deleteConversation;
window.saveSettings = saveSettings;
window.exportContext = exportContext;
