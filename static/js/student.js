const sessionCode = new URLSearchParams(window.location.search).get('code');
let sessionData = null;
let ws = null;
let upvotedQuestions = new Set();

if (!sessionCode) {
    alert('Invalid session code');
    window.location.href = '/';
}

async function loadSession() {
    try {
        const response = await fetch(`/api/sessions/${sessionCode}`);
        if (!response.ok) {
            throw new Error('Session not found');
        }
        sessionData = await response.json();

        // Update UI
        document.getElementById('session-title').textContent = sessionData.title;
        document.getElementById('session-code').textContent = sessionData.session_code;

        if (!sessionData.is_active) {
            // Disable question submission
            const form = document.getElementById('question-form');
            const textarea = document.getElementById('question-text');
            const submitBtn = form.querySelector('button[type="submit"]');

            textarea.disabled = true;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Session Ended';
            submitBtn.style.cursor = 'not-allowed';

            // Show prominent message
            const formContainer = document.querySelector('.question-form');
            const endedMessage = document.createElement('div');
            endedMessage.style.cssText = `
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
                font-weight: bold;
                border: 2px solid #f5c6cb;
            `;
            endedMessage.innerHTML = '⚠️ This session has ended. No new questions can be submitted.';
            formContainer.insertBefore(endedMessage, form);
        }

        renderQuestions();
        connectWebSocket();

        // Load upvoted questions from localStorage
        const stored = localStorage.getItem(`upvoted_${sessionCode}`);
        if (stored) {
            upvotedQuestions = new Set(JSON.parse(stored));
        }
    } catch (error) {
        console.error('Error loading session:', error);
        alert('Failed to load session');
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionCode}`;

    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket closed, reconnecting...');
        setTimeout(connectWebSocket, 3000);
    };
}

function handleWebSocketMessage(message) {
    if (message.type === 'new_question') {
        // Add new question to session data
        sessionData.questions.push(message.question);
        renderQuestions();
    } else if (message.type === 'upvote') {
        // Update upvote count
        const question = sessionData.questions.find(q => q.id === message.question_id);
        if (question) {
            question.upvotes = message.upvotes;
            renderQuestions();
        }
    } else if (message.type === 'answer_status') {
        // Update answer status
        const question = sessionData.questions.find(q => q.id === message.question_id);
        if (question) {
            question.is_answered = message.is_answered;
            renderQuestions();
        }
    }
}

function renderQuestions() {
    const questionsList = document.getElementById('questions-list');
    const questions = sessionData.questions || [];

    // Update count
    document.getElementById('question-count').textContent =
        `${questions.length} question${questions.length !== 1 ? 's' : ''}`;

    if (questions.length === 0) {
        questionsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💭</div>
                <div class="empty-state-text">No questions yet. Be the first to ask!</div>
            </div>
        `;
        return;
    }

    // Sort by upvotes (descending), then by creation time
    const sortedQuestions = [...questions].sort((a, b) => {
        if (b.upvotes !== a.upvotes) {
            return b.upvotes - a.upvotes;
        }
        return new Date(b.created_at) - new Date(a.created_at);
    });

    questionsList.innerHTML = sortedQuestions.map(q => {
        const createdTime = new Date(q.created_at).toLocaleTimeString();
        const answeredClass = q.is_answered ? 'answered' : '';
        const hasUpvoted = upvotedQuestions.has(q.id);
        const upvotedClass = hasUpvoted ? 'upvoted' : '';

        return `
            <div class="question-card ${answeredClass}">
                <div class="question-header">
                    <div class="question-content">
                        <div class="question-text">${escapeHtml(q.text)}</div>
                        <div class="question-meta">
                            Asked at ${createdTime}
                            ${q.is_answered ? '• <strong style="color: var(--success-color);">Answered ✓</strong>' : ''}
                        </div>
                    </div>
                    <div class="question-actions">
                        <button class="upvote-btn ${upvotedClass}"
                                onclick="upvoteQuestion(${q.id})"
                                ${!sessionData.is_active || hasUpvoted ? 'disabled' : ''}>
                            <span class="upvote-icon">⬆️</span>
                            <span class="upvote-count">${q.upvotes}</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function upvoteQuestion(questionId) {
    if (upvotedQuestions.has(questionId)) {
        showNotification('You have already upvoted this question', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/questions/${questionId}/upvote`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to upvote question');
        }

        // Mark as upvoted locally
        upvotedQuestions.add(questionId);
        localStorage.setItem(`upvoted_${sessionCode}`, JSON.stringify([...upvotedQuestions]));

        showNotification('Question upvoted!', 'success');

        // WebSocket will handle the UI update
    } catch (error) {
        console.error('Error upvoting question:', error);
        showNotification('Failed to upvote question', 'error');
    }
}

document.getElementById('question-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!sessionData.is_active) {
        showNotification('This session has ended', 'error');
        return;
    }

    const formData = new FormData(e.target);
    const text = formData.get('text').trim();

    if (!text) {
        showNotification('Please enter a question', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/sessions/${sessionCode}/questions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error('Failed to submit question');
        }

        showNotification('Question submitted successfully!', 'success');
        e.target.reset();

        // WebSocket will handle adding the question to the UI
    } catch (error) {
        console.error('Error submitting question:', error);
        showNotification('Failed to submit question', 'error');
    }
});

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
loadSession();
