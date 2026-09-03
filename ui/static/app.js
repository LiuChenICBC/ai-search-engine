/**
 * www_search - 主页交互逻辑
 * 所有事件通过 addEventListener 绑定，避免 CSP 阻止内联脚本
 */
(function () {
    'use strict';

    const queryEl = document.getElementById('query');
    const messagesEl = document.getElementById('messages');
    const sendBtn = document.getElementById('sendBtn');
    const welcomeEl = document.getElementById('welcome');
    const keyDot = document.getElementById('keyDot');
    const keyStatusText = document.getElementById('keyStatusText');

    // API Key 管理 (localStorage)
    function getApiKey() {
        return localStorage.getItem('www_search_api_key') || '';
    }

    function hasApiKey() {
        return getApiKey().length > 20;
    }

    function updateKeyStatus() {
        if (hasApiKey()) {
            keyDot.className = 'key-dot ok';
            keyStatusText.textContent = 'API Key 已配置';
        } else {
            keyDot.className = 'key-dot missing';
            keyStatusText.textContent = '未配置 API Key';
        }
    }

    // Modal
    function showKeyModal() {
        document.getElementById('keyModal').classList.add('active');
        var input = document.getElementById('apiKeyInput');
        input.value = getApiKey();
        setTimeout(function () { input.focus(); }, 100);
    }

    function hideKeyModal() {
        document.getElementById('keyModal').classList.remove('active');
        document.getElementById('apiKeyInput').value = '';
    }

    function saveApiKey() {
        var val = document.getElementById('apiKeyInput').value.trim();
        if (val) {
            localStorage.setItem('www_search_api_key', val);
        } else {
            localStorage.removeItem('www_search_api_key');
        }
        updateKeyStatus();
        hideKeyModal();
    }

    // Bind events via addEventListener (CSP blocks inline handlers)
    var settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', showKeyModal);
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', sendQuery);
    }

    var cancelKeyBtn = document.getElementById('cancelKeyBtn');
    if (cancelKeyBtn) {
        cancelKeyBtn.addEventListener('click', hideKeyModal);
    }

    var saveKeyBtn = document.getElementById('saveKeyBtn');
    if (saveKeyBtn) {
        saveKeyBtn.addEventListener('click', saveApiKey);
    }

    var apiKeyInput = document.getElementById('apiKeyInput');
    if (apiKeyInput) {
        apiKeyInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') saveApiKey();
        });
    }

    // Init status
    updateKeyStatus();

    // Auto-resize textarea
    if (queryEl) {
        queryEl.addEventListener('input', function () {
            queryEl.style.height = 'auto';
            queryEl.style.height = Math.min(queryEl.scrollHeight, 200) + 'px';
        });
    }

    function handleKey(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuery();
        }
    }

    // Bind keyboard on textarea
    if (queryEl) {
        queryEl.addEventListener('keydown', handleKey);
    }

    async function sendQuery() {
        const query = queryEl.value.trim();
        if (!query) return;

        // 检查 API Key
        if (!hasApiKey()) {
            showKeyModal();
            return;
        }

        // Hide welcome, show user message
        if (welcomeEl) welcomeEl.remove();
        queryEl.value = '';
        queryEl.style.height = 'auto';

        // Add user message
        addMessage('user', query);

        // Disable input
        sendBtn.disabled = true;

        // Add assistant message area
        const msgId = 'msg-' + Date.now();
        const assistantDiv = document.createElement('div');
        assistantDiv.className = 'message assistant';
        assistantDiv.id = msgId;
        assistantDiv.innerHTML =
            '<div class="label">\u26a1 \u7b54\u6848</div>' +
            '<div class="status-area"></div>' +
            '<div class="answer-content"></div>' +
            '<div class="sources"></div>';
        messagesEl.appendChild(assistantDiv);
        scrollToBottom();

        const statusArea = assistantDiv.querySelector('.status-area');
        const answerArea = assistantDiv.querySelector('.answer-content');
        const sourcesArea = assistantDiv.querySelector('.sources');

        let fullAnswer = '';
        let cursor = document.createElement('span');
        cursor.className = 'cursor';

        try {
            const headers = { 'Content-Type': 'application/json' };
            const apiKey = getApiKey();
            if (apiKey) {
                headers['X-API-Key'] = apiKey;
            }
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ query: query, stream: true }),
            });

            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const result = await reader.read();
                if (result.done) break;

                buffer += decoder.decode(result.value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;

                    try {
                        const event = JSON.parse(data);
                        if (event.type === 'status') {
                            statusArea.innerHTML =
                                '<div class="status-msg"><div class="spinner"></div>' + escapeHtml(event.text) + '</div>';
                        } else if (event.type === 'answer_chunk') {
                            fullAnswer += event.text;
                            const oldCursor = answerArea.querySelector('.cursor');
                            if (oldCursor) oldCursor.remove();
                            answerArea.innerHTML = renderMarkdown(fullAnswer);
                            answerArea.appendChild(cursor);
                            scrollToBottom();
                        } else if (event.type === 'sources') {
                            const sourcesDiv = document.createElement('div');
                            sourcesDiv.className = 'sources';
                            sourcesDiv.innerHTML = '<div class="sources-title">\ud83d\udcda \u6765\u6e90</div>';
                            event.sources.forEach(function (src, idx) {
                                var safeUrl = isSafeUrl(src.url) ? src.url : '#';
                                var titleHtml = safeUrl !== '#' 
                                    ? '<a href="' + escapeHtml(src.url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(src.title) + '</a>'
                                    : escapeHtml(src.title);
                                sourcesDiv.innerHTML +=
                                    '<div class="source-item">' +
                                    '  <div class="source-num">' + (idx + 1) + '</div>' +
                                    '  <div class="source-info">' +
                                    '    <div class="source-title">' + titleHtml + '</div>' +
                                    '    <div class="source-url">' + escapeHtml(src.url) + '</div>' +
                                    '    <div class="source-snippet">' + escapeHtml(src.snippet) + '</div>' +
                                    '  </div></div>';
                            });
                            sourcesArea.appendChild(sourcesDiv);
                            scrollToBottom();
                        } else if (event.type === 'done') {
                            statusArea.innerHTML = '';
                            cursor.remove();
                            answerArea.innerHTML = renderMarkdown(fullAnswer);
                            scrollToBottom();
                        }
                    } catch (parseErr) {
                        // Skip parse errors for malformed SSE lines
                    }
                }
            }
        } catch (err) {
            statusArea.innerHTML =
                '<div class="status-msg" style="color: #ef4444;">\u274c \u9519\u8bef: ' + escapeHtml(err.message) + '</div>';
        }

        sendBtn.disabled = false;
        queryEl.focus();
    }

    function addMessage(type, content) {
        const div = document.createElement('div');
        div.className = 'message ' + type;
        var label = type === 'user' ? '\ud83d\udc64 \u4f60' : '\u26a1 \u7b54\u6848';
        div.innerHTML = '<div class="label">' + label + '</div><div>' + escapeHtml(content) + '</div>';
        messagesEl.appendChild(div);
        scrollToBottom();
    }

    function scrollToBottom() {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Validate URL safety (only allow http/https/mailto protocols)
    function isSafeUrl(url) {
        var safeProtocols = ['http:', 'https:', 'mailto:'];
        try {
            var parsed = new URL(url);
            return safeProtocols.indexOf(parsed.protocol) !== -1;
        } catch (e) {
            return false;
        }
    }

    // Simple markdown renderer
    function renderMarkdown(text) {
        var html = escapeHtml(text);

        // Code blocks
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        // Headers
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        // Links [text](url) - only allow safe protocols
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (match, linkText, url) {
            if (isSafeUrl(url)) {
                return '<a href="' + escapeHtml(url) + '" target="_blank" rel="noopener noreferrer">' + linkText + '</a>';
            }
            return linkText + ' (' + url + ')';
        });
        // Unordered lists
        html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');
        html = '<p>' + html + '</p>';

        // Clean up empty paragraphs
        html = html.replace(/<p><\/p>/g, '');
        html = html.replace(/<p>(<h[23]>)/g, '$1');
        html = html.replace(/(<\/h[23]>)<\/p>/g, '$1');
        html = html.replace(/<p>(<pre>)/g, '$1');
        html = html.replace(/(<\/pre>)<\/p>/g, '$1');
        html = html.replace(/<p>(<ul>)/g, '$1');
        html = html.replace(/(<\/ul>)<\/p>/g, '$1');

        return html;
    }

    // Focus on load
    if (queryEl) {
        queryEl.focus();
    }
})();
