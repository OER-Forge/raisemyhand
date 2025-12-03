// NOTE: Authentication utilities are now in shared.js
// This file uses: getApiKey(), setApiKey(), clearApiKey(), handleAuthError(),
// promptForApiKey(), authenticatedFetch(), escapeHtml(), showNotification()

const instructorCode = new URLSearchParams(window.location.search).get('code');
let sessionData = null;
let ws = null;
let config = null;

// Load configuration
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        config = await response.json();
    } catch (error) {
        console.error('Error loading config:', error);
        // Fallback to window.location if config fails
        config = { base_url: window.location.origin };
    }
}

async function loadSession() {
    try {
        await loadConfig(); // Load config first

        const apiKey = getApiKey();
        if (!apiKey) {
            console.error('No API key found');
            promptForApiKey();
            return;
        }

        const response = await authenticatedFetch(`/api/instructor/sessions/${instructorCode}`);

        if (response.status === 401) {
            console.error('Authentication failed - invalid API key');
            handleAuthError();
            return;
        }

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Failed to load session:', response.status, errorText);
            throw new Error(`Session not found: ${response.status}`);
        }
        sessionData = await response.json();

        // Update UI
        document.getElementById('session-title').textContent = sessionData.title;
        document.getElementById('session-code').textContent = sessionData.session_code;

        // Show password protection status
        const passwordInfo = document.getElementById('password-info');
        if (sessionData.has_password) {
            passwordInfo.style.display = 'block';
        }

        const baseUrl = config.base_url;
        const studentUrl = `${baseUrl}/student?code=${sessionData.session_code}`;
        document.getElementById('student-url').textContent = studentUrl;

        // Update status and buttons
        const statusEl = document.getElementById('session-status');
        const endBtn = document.getElementById('end-session-btn');
        const restartBtn = document.getElementById('restart-session-btn');

        if (sessionData.is_active) {
            statusEl.textContent = 'Active';
            statusEl.className = 'status-indicator active';
            endBtn.style.display = 'inline-block';
            restartBtn.style.display = 'none';
        } else {
            statusEl.textContent = 'Ended';
            statusEl.className = 'status-indicator ended';
            endBtn.style.display = 'none';
            restartBtn.style.display = 'inline-block';
        }

        renderQuestions();
        connectWebSocket();
    } catch (error) {
        console.error('Error loading session:', error);
        alert(`Failed to load session: ${error.message}`);
        // Redirect to home page after error
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionData.session_code}`;

    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        setTimeout(connectWebSocket, 3000);
    };
}

function handleWebSocketMessage(message) {
    if (message.type === 'new_question') {
        // Add new question to session data
        sessionData.questions.push(message.question);
        renderQuestions();
        showNotification('New question received!', 'success');
    } else if (message.type === 'upvote' || message.type === 'vote_update') {
        // Update vote count
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
                <div class="empty-state-text">No questions yet. Share the session URL with your students!</div>
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
        const questionNumber = q.question_number || '?';

        return `
            <div class="question-card ${answeredClass}">
                <div class="question-header">
                    <div class="question-badge">Q${questionNumber}</div>
                    <div class="question-content">
                        <div class="question-text">${escapeHtml(q.text)}</div>
                        <div class="question-meta">Asked at ${createdTime}</div>
                    </div>
                    <div class="question-actions">
                        <div class="upvote-btn">
                            <span class="upvote-icon">⬆️</span>
                            <span class="upvote-count">${q.upvotes}</span>
                        </div>
                        <button class="btn ${q.is_answered ? 'btn-secondary' : 'btn-success'}"
                                onclick="toggleAnswered(${q.id})">
                            ${q.is_answered ? 'Mark Unanswered' : 'Mark Answered'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function toggleAnswered(questionId) {
    try {
        // Get CSRF token for best practice (even though backend doesn't require it for this endpoint)
        const csrfToken = await getCsrfToken();

        const response = await fetch(`/api/questions/${questionId}/answer?instructor_code=${instructorCode}`, {
            method: 'POST',
            headers: {
                'X-CSRF-Token': csrfToken
            }
        });

        if (!response.ok) {
            throw new Error('Failed to update question');
        }

        // WebSocket will handle the UI update
    } catch (error) {
        console.error('Error toggling answer status:', error);
        showNotification('Failed to update question', 'error');
    }
}

function showQRCode() {
    const baseUrl = config.base_url;
    const qrUrl = `/api/sessions/${sessionData.session_code}/qr?url_base=${encodeURIComponent(baseUrl)}`;
    document.getElementById('qr-image').src = qrUrl;
    document.getElementById('qr-modal').classList.add('active');
}

function hideQRCode() {
    document.getElementById('qr-modal').classList.remove('active');
}

function openPublicStats() {
    const baseUrl = config.base_url;
    const statsUrl = `${baseUrl}/stats?code=${sessionData.session_code}`;
    
    // Open in new tab
    window.open(statsUrl, '_blank');
    
    // Also copy to clipboard
    navigator.clipboard.writeText(statsUrl).then(() => {
        alert('📊 Public stats page opened!\n\n✅ URL copied to clipboard:\n' + statsUrl + '\n\nShare this link to display live statistics without revealing question text.');
    }).catch(() => {
        alert('📊 Public stats page opened!\n\n📋 Share this URL:\n' + statsUrl);
    });
}

async function downloadReport(format) {
    try {
        const response = await authenticatedFetch(`/api/sessions/${instructorCode}/report?format=${format}`);
        
        if (response.status === 401) {
            handleAuthError();
            return;
        }
        
        if (!response.ok) {
            throw new Error('Failed to generate report');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `session_${sessionData.session_code}_report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showNotification('Report downloaded successfully', 'success');
    } catch (error) {
        console.error('Error downloading report:', error);
        showNotification('Failed to download report', 'error');
    }
}

async function endSession() {
    if (!confirm('Are you sure you want to end this session? Students will no longer be able to submit questions.')) {
        return;
    }

    try {
        const response = await authenticatedFetch(`/api/sessions/${instructorCode}/end`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }
        
        if (!response.ok) {
            throw new Error('Failed to end session');
        }

        showNotification('Session ended successfully', 'success');

        // Update UI
        sessionData.is_active = false;
        const statusEl = document.getElementById('session-status');
        statusEl.textContent = 'Ended';
        statusEl.className = 'status-indicator ended';

        // Toggle buttons
        document.getElementById('end-session-btn').style.display = 'none';
        document.getElementById('restart-session-btn').style.display = 'inline-block';

        // Close WebSocket
        if (ws) {
            ws.close();
        }
    } catch (error) {
        console.error('Error ending session:', error);
        showNotification('Failed to end session', 'error');
    }
}

async function restartSession() {
    if (!confirm('Are you sure you want to restart this session? Students will be able to submit questions again.')) {
        return;
    }

    try {
        const response = await authenticatedFetch(`/api/sessions/${instructorCode}/restart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }
        
        if (!response.ok) {
            throw new Error('Failed to restart session');
        }

        showNotification('Session restarted successfully', 'success');

        // Update UI
        sessionData.is_active = true;
        const statusEl = document.getElementById('session-status');
        statusEl.textContent = 'Active';
        statusEl.className = 'status-indicator active';

        // Toggle buttons
        document.getElementById('end-session-btn').style.display = 'inline-block';
        document.getElementById('restart-session-btn').style.display = 'none';

        // Reconnect WebSocket
        connectWebSocket();
    } catch (error) {
        console.error('Error restarting session:', error);
        showNotification('Failed to restart session', 'error');
    }
}

// Utility functions (showNotification, escapeHtml) are now in shared.js

// Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        clearApiKey();
        window.location.href = '/';
    }
}

// Initialize
if (!instructorCode) {
    alert('Invalid instructor code');
    window.location.href = '/';
} else if (!getApiKey()) {
    // Prompt for API key if not found
    promptForApiKey();
} else {
    // Load session immediately if we have both code and API key
    loadSession();
}
