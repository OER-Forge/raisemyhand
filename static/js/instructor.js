// NOTE: Authentication utilities are now in shared.js
// This file uses: getApiKey(), setApiKey(), clearApiKey(), handleAuthError(),
// promptForApiKey(), authenticatedFetch(), escapeHtml(), showNotification()

const instructorCode = new URLSearchParams(window.location.search).get('code');
let meetingData = null; // v2: renamed from sessionData
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

        // v2 API: GET /api/meetings/{instructor_code}
        const response = await authenticatedFetch(`/api/meetings/${instructorCode}`);

        if (response.status === 401) {
            console.error('Authentication failed - invalid API key');
            handleAuthError();
            return;
        }

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Failed to load meeting:', response.status, errorText);
            throw new Error(`Meeting not found: ${response.status}`);
        }
        meetingData = await response.json();

        // Update UI
        document.getElementById('session-title').textContent = meetingData.title;
        document.getElementById('session-code').textContent = meetingData.meeting_code;

        // Show password protection status
        const passwordInfo = document.getElementById('password-info');
        if (meetingData.has_password) {
            passwordInfo.style.display = 'block';
        }

        const baseUrl = config.base_url;
        const studentUrl = `${baseUrl}/student?code=${meetingData.meeting_code}`;
        document.getElementById('student-url').textContent = studentUrl;
        document.getElementById('student-url').setAttribute('aria-label', `Student join URL: ${studentUrl}`);

        // Update status and buttons
        const statusEl = document.getElementById('session-status');
        const endBtn = document.getElementById('end-session-btn');
        const restartBtn = document.getElementById('restart-session-btn');

        if (meetingData.is_active) {
            statusEl.textContent = 'Active';
            statusEl.className = 'status-indicator active';
            statusEl.setAttribute('aria-label', 'Meeting status: Active');
            endBtn.style.display = 'inline-block';
            endBtn.removeAttribute('aria-hidden');
            restartBtn.style.display = 'none';
            restartBtn.setAttribute('aria-hidden', 'true');
        } else {
            statusEl.textContent = 'Ended';
            statusEl.className = 'status-indicator ended';
            statusEl.setAttribute('aria-label', 'Meeting status: Ended');
            endBtn.style.display = 'none';
            endBtn.setAttribute('aria-hidden', 'true');
            restartBtn.style.display = 'inline-block';
            restartBtn.removeAttribute('aria-hidden');
        }

        renderQuestions();
        connectWebSocket();
    } catch (error) {
        console.error('Error loading meeting:', error);
        alert(`Failed to load meeting: ${error.message}`);
        // Redirect to home page after error
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${meetingData.meeting_code}`;

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
        // Add new question to meeting data
        meetingData.questions.push(message.question);
        renderQuestions();
        showNotification('New question received!', 'success');
    } else if (message.type === 'upvote' || message.type === 'vote_update') {
        // Update vote count
        const question = meetingData.questions.find(q => q.id === message.question_id);
        if (question) {
            question.upvotes = message.upvotes;
            renderQuestions();
        }
    } else if (message.type === 'answer_status') {
        // Update answer status (v2 uses is_answered_in_class)
        const question = meetingData.questions.find(q => q.id === message.question_id);
        if (question) {
            question.is_answered_in_class = message.is_answered_in_class || message.is_answered;
            renderQuestions();
        }
    }
}

function renderQuestions() {
    const questionsList = document.getElementById('questions-list');
    const questions = meetingData.questions || [];

    // Update count
    document.getElementById('question-count').textContent =
        `${questions.length} question${questions.length !== 1 ? 's' : ''}`;

    if (questions.length === 0) {
        questionsList.innerHTML = `
            <div class="empty-state" role="status">
                <div class="empty-state-icon" aria-hidden="true">💭</div>
                <div class="empty-state-text">No questions yet. Share the meeting URL with your students!</div>
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
        const isAnswered = q.is_answered_in_class || q.is_answered || false;
        const answeredClass = isAnswered ? 'answered' : '';
        const questionNumber = q.question_number || '?';
        const answerLabel = isAnswered ? 'Mark as unanswered' : 'Mark as answered';

        return `
            <article class="question-card ${answeredClass}" role="article">
                <div class="question-header">
                    <div class="question-badge" aria-label="Question number ${questionNumber}">Q${questionNumber}</div>
                    <div class="question-content">
                        <div class="question-text">${escapeHtml(q.text)}</div>
                        <div class="question-meta">
                            <time datetime="${q.created_at}">Asked at ${createdTime}</time>
                        </div>
                    </div>
                    <div class="question-actions">
                        <div class="upvote-btn" role="status" aria-label="${q.upvotes} upvotes">
                            <span class="upvote-icon" aria-hidden="true">⬆️</span>
                            <span class="upvote-count">${q.upvotes}</span>
                        </div>
                        <button class="btn ${isAnswered ? 'btn-secondary' : 'btn-success'}"
                                onclick="toggleAnswered(${q.id})"
                                aria-label="${answerLabel}"
                                aria-pressed="${isAnswered}">
                            ${isAnswered ? '✓ Answered in Class' : 'Mark Answered in Class'}
                        </button>
                        <button class="btn btn-primary"
                                onclick="openAnswerDialog(${q.id}, '${escapeHtml(q.text).replace(/'/g, "\\'")}', ${q.has_written_answer})"
                                aria-label="Write answer for this question">
                            ${q.has_written_answer ? '✏️ Edit Answer' : '📝 Write Answer'}
                        </button>
                    </div>
                </div>
            </article>
        `;
    }).join('');
}

async function toggleAnswered(questionId) {
    try {
        const apiKey = getApiKey();

        // v2 API: POST /api/questions/{id}/mark-answered-in-class
        const response = await fetch(`/api/questions/${questionId}/mark-answered-in-class?api_key=${apiKey}`, {
            method: 'POST'
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to update question');
        }

        const data = await response.json();

        // Update local data
        const question = meetingData.questions.find(q => q.id === questionId);
        if (question) {
            question.is_answered_in_class = data.is_answered_in_class;
            renderQuestions();
            showNotification(
                data.is_answered_in_class ? 'Question marked as answered' : 'Question marked as unanswered',
                'success'
            );
        }
    } catch (error) {
        console.error('Error toggling answer status:', error);
        showNotification('Failed to update question', 'error');
    }
}

function showQRCode() {
    const baseUrl = config.base_url;
    const qrUrl = `/api/meetings/${meetingData.meeting_code}/qr?url_base=${encodeURIComponent(baseUrl)}`;
    const modal = document.getElementById('qr-modal');
    const qrImage = document.getElementById('qr-image');

    qrImage.src = qrUrl;
    qrImage.setAttribute('alt', `QR code for meeting ${meetingData.title}`);
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');

    // Focus management
    const closeBtn = modal.querySelector('[onclick="hideQRCode()"]');
    if (closeBtn) {
        closeBtn.focus();
    }
}

function hideQRCode() {
    const modal = document.getElementById('qr-modal');
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
}

function openPublicStats() {
    const baseUrl = config.base_url;
    const statsUrl = `${baseUrl}/stats?code=${meetingData.meeting_code}`;

    // Open in new tab
    window.open(statsUrl, '_blank', 'noopener,noreferrer');

    // Also copy to clipboard
    navigator.clipboard.writeText(statsUrl).then(() => {
        alert('📊 Public stats page opened!\n\n✅ URL copied to clipboard:\n' + statsUrl + '\n\nShare this link to display live statistics without revealing question text.');
    }).catch(() => {
        alert('📊 Public stats page opened!\n\n📋 Share this URL:\n' + statsUrl);
    });
}

async function downloadReport(format) {
    try {
        // v2 API: GET /api/meetings/{instructor_code}/report
        const response = await authenticatedFetch(`/api/meetings/${instructorCode}/report?format=${format}`);

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
        a.download = `meeting_${meetingData.meeting_code}_report.${format}`;
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
    if (!confirm('Are you sure you want to end this meeting? Students will no longer be able to submit questions.')) {
        return;
    }

    const endBtn = document.getElementById('end-session-btn');
    showButtonLoading(endBtn);

    try {
        const apiKey = getApiKey();

        // v2 API: POST /api/meetings/{instructor_code}/end
        const response = await fetch(`/api/meetings/${instructorCode}/end?api_key=${apiKey}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to end meeting');
        }

        showNotification('Meeting ended successfully', 'success');

        // Update UI
        meetingData.is_active = false;
        const statusEl = document.getElementById('session-status');
        statusEl.textContent = 'Ended';
        statusEl.className = 'status-indicator ended';
        statusEl.setAttribute('aria-label', 'Meeting status: Ended');

        // Toggle buttons
        endBtn.style.display = 'none';
        endBtn.setAttribute('aria-hidden', 'true');
        const restartBtn = document.getElementById('restart-session-btn');
        restartBtn.style.display = 'inline-block';
        restartBtn.removeAttribute('aria-hidden');

        // Close WebSocket
        if (ws) {
            ws.close();
        }
    } catch (error) {
        console.error('Error ending meeting:', error);
        showNotification('Failed to end meeting', 'error');
    } finally {
        hideButtonLoading(endBtn);
    }
}

async function restartSession() {
    if (!confirm('Are you sure you want to restart this meeting? Students will be able to submit questions again.')) {
        return;
    }

    const restartBtn = document.getElementById('restart-session-btn');
    showButtonLoading(restartBtn);

    try {
        const apiKey = getApiKey();

        // v2 API: POST /api/meetings/{instructor_code}/restart
        const response = await fetch(`/api/meetings/${instructorCode}/restart?api_key=${apiKey}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to restart meeting');
        }

        showNotification('Meeting restarted successfully', 'success');

        // Update UI
        meetingData.is_active = true;
        const statusEl = document.getElementById('session-status');
        statusEl.textContent = 'Active';
        statusEl.className = 'status-indicator active';
        statusEl.setAttribute('aria-label', 'Meeting status: Active');

        // Toggle buttons
        const endBtn = document.getElementById('end-session-btn');
        endBtn.style.display = 'inline-block';
        endBtn.removeAttribute('aria-hidden');
        restartBtn.style.display = 'none';
        restartBtn.setAttribute('aria-hidden', 'true');

        // Reconnect WebSocket
        connectWebSocket();
    } catch (error) {
        console.error('Error restarting meeting:', error);
        showNotification('Failed to restart meeting', 'error');
    } finally {
        hideButtonLoading(restartBtn);
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

// Answer Dialog Functions
let currentAnswerQuestionId = null;
let currentAnswerData = null;

async function openAnswerDialog(questionId, questionText, hasAnswer) {
    currentAnswerQuestionId = questionId;

    // Set modal title and question text
    document.getElementById('answer-modal-title').textContent = hasAnswer ? 'Edit Answer' : 'Write Answer';
    document.getElementById('answer-modal-question').textContent = `Question: ${questionText}`;
    document.getElementById('answer-question-id').value = questionId;

    // Clear form
    document.getElementById('answer-text').value = '';

    // Hide publish/delete buttons initially
    document.getElementById('publish-answer-btn').style.display = 'none';
    document.getElementById('delete-answer-btn').style.display = 'none';

    // If answer exists, load it
    if (hasAnswer) {
        try {
            const apiKey = getApiKey();
            const response = await fetch(`/api/questions/${questionId}/answer?api_key=${apiKey}`);

            if (response.ok) {
                currentAnswerData = await response.json();
                document.getElementById('answer-text').value = currentAnswerData.answer_text;

                // Show publish button if not already published
                if (!currentAnswerData.is_approved) {
                    document.getElementById('publish-answer-btn').style.display = 'inline-block';
                }

                // Show delete button
                document.getElementById('delete-answer-btn').style.display = 'inline-block';
            }
        } catch (error) {
            console.error('Error loading answer:', error);
            showNotification('Failed to load existing answer', 'error');
        }
    }

    // Show modal
    const modal = document.getElementById('answer-modal');
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');

    // Focus textarea
    setTimeout(() => {
        document.getElementById('answer-text').focus();
    }, 100);
}

function closeAnswerDialog() {
    const modal = document.getElementById('answer-modal');
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    currentAnswerQuestionId = null;
    currentAnswerData = null;
}

async function submitAnswer(event) {
    event.preventDefault();

    const questionId = document.getElementById('answer-question-id').value;
    const answerText = document.getElementById('answer-text').value;

    if (!answerText.trim()) {
        showNotification('Please enter an answer', 'error');
        return;
    }

    try {
        const apiKey = getApiKey();
        const response = await fetch(`/api/questions/${questionId}/answer?api_key=${apiKey}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                answer_text: answerText,
                is_approved: false
            })
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to save answer');
        }

        const data = await response.json();
        currentAnswerData = data;

        showNotification('Answer saved successfully', 'success');

        // Show publish button
        document.getElementById('publish-answer-btn').style.display = 'inline-block';
        document.getElementById('delete-answer-btn').style.display = 'inline-block';

        // Update question in local data
        const question = meetingData.questions.find(q => q.id == questionId);
        if (question) {
            question.has_written_answer = true;
        }

        // Don't close modal - allow user to publish or continue editing
    } catch (error) {
        console.error('Error saving answer:', error);
        showNotification('Failed to save answer', 'error');
    }
}

async function publishAnswer() {
    if (!currentAnswerQuestionId) return;

    if (!confirm('Publish this answer to students? Once published, students will be able to see it.')) {
        return;
    }

    try {
        const apiKey = getApiKey();
        const response = await fetch(`/api/questions/${currentAnswerQuestionId}/answer/publish?api_key=${apiKey}`, {
            method: 'POST'
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to publish answer');
        }

        showNotification('Answer published to students!', 'success');

        // Hide publish button
        document.getElementById('publish-answer-btn').style.display = 'none';

        // Close modal
        closeAnswerDialog();

        // Refresh questions to update UI
        renderQuestions();
    } catch (error) {
        console.error('Error publishing answer:', error);
        showNotification('Failed to publish answer', 'error');
    }
}

async function deleteAnswer() {
    if (!currentAnswerQuestionId) return;

    if (!confirm('Delete this answer? This action cannot be undone.')) {
        return;
    }

    try {
        const apiKey = getApiKey();
        const response = await fetch(`/api/questions/${currentAnswerQuestionId}/answer?api_key=${apiKey}`, {
            method: 'DELETE'
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to delete answer');
        }

        showNotification('Answer deleted successfully', 'success');

        // Update question in local data
        const question = meetingData.questions.find(q => q.id == currentAnswerQuestionId);
        if (question) {
            question.has_written_answer = false;
        }

        // Close modal
        closeAnswerDialog();

        // Refresh questions to update UI
        renderQuestions();
    } catch (error) {
        console.error('Error deleting answer:', error);
        showNotification('Failed to delete answer', 'error');
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
