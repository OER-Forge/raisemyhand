// NOTE: Authentication utilities are now in shared.js
// This file uses: getApiKey(), setApiKey(), clearApiKey(), handleAuthError(),
// promptForApiKey(), authenticatedFetch(), escapeHtml(), showNotification()

const instructorCode = new URLSearchParams(window.location.search).get('code');
let meetingData = null; // v2: renamed from sessionData
let ws = null;
let config = null;
let easyMDE = null; // Markdown editor instance

// Markdown rendering helpers (same as student.js but instructors see both)
function renderMarkdownNoImages(text) {
    const rawHtml = marked.parse(text);
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
        FORBID_TAGS: ['img'],
        FORBID_ATTR: ['src', 'srcset']
    });
    return cleanHtml;
}

function renderMarkdownFull(text) {
    const rawHtml = marked.parse(text);
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'img'],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt', 'title', 'class']
    });
    return cleanHtml;
}

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

        // v2 API: GET /api/meetings/{instructor_code}
        const response = await authenticatedFetch(`/api/meetings/${instructorCode}`);

        if (response.status === 401) {
            console.error('Authentication failed');
            handleAuthError();
            return;
        }

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Failed to load meeting:', response.status, errorText);
            throw new Error(`Meeting not found: ${response.status}`);
        }
        meetingData = await response.json();
        console.log('[INSTRUCTOR] Meeting data loaded from API:', meetingData);
        console.log('[INSTRUCTOR] is_active value:', meetingData.is_active);

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
        const studentUrlEl = document.getElementById('student-url');
        studentUrlEl.innerHTML = `<a href="${studentUrl}" target="_blank" rel="noopener noreferrer" style="color: var(--primary-color); text-decoration: none; word-break: break-all;">${studentUrl}</a>`;
        studentUrlEl.setAttribute('aria-label', `Student join URL: ${studentUrl}`);

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

    console.log('[INSTRUCTOR] Connecting to WebSocket:', wsUrl);
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[INSTRUCTOR] WebSocket connected');
    };

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('[INSTRUCTOR] WebSocket message received:', message.type, message);
        handleWebSocketMessage(message);
    };

    ws.onerror = (error) => {
        console.error('[INSTRUCTOR] WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('[INSTRUCTOR] WebSocket closed, reconnecting in 3 seconds...');
        setTimeout(connectWebSocket, 3000);
    };
}

function handleWebSocketMessage(message) {
    console.log('[INSTRUCTOR] Handling message type:', message.type);
    
    if (message.type === 'new_question') {
        console.log('[INSTRUCTOR] Adding new question:', message.question);
        // Add new question to meeting data
        meetingData.questions.push(message.question);
        renderQuestions();

        // Show different notification for flagged vs normal questions
        if (message.question.status === 'flagged') {
            showNotification('⚠️ Question flagged for review!', 'warning');
        } else {
            showNotification('New question received!', 'success');
        }
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
    } else if (message.type === 'question_moderated') {
        // Question was approved or rejected
        const question = meetingData.questions.find(q => q.id === message.question_id);
        if (question) {
            question.status = message.status;
            renderQuestions();

            // Reload flagged questions if we're viewing that tab
            const flaggedTab = document.getElementById('flagged-questions-tab');
            if (flaggedTab && flaggedTab.classList.contains('active')) {
                loadFlaggedQuestions();
            }
        }
    }
}

function renderQuestions() {
    const questionsList = document.getElementById('questions-list');
    const questions = meetingData.questions || [];

    // Filter questions by status:
    // - Approved: show in "All Questions" tab
    // - Flagged: show in "Flagged for Review" tab (needs instructor action)
    // - Rejected: show in "Flagged for Review" tab (already moderated)
    const approvedQuestions = questions.filter(q => q.status === 'approved');
    const flaggedQuestions = questions.filter(q => q.status === 'flagged' || q.status === 'rejected');

    // Update counts
    document.getElementById('question-count').textContent =
        `${approvedQuestions.length} question${approvedQuestions.length !== 1 ? 's' : ''}`;
    document.getElementById('all-count').textContent = approvedQuestions.length;
    document.getElementById('flagged-count').textContent = flaggedQuestions.length;

    if (approvedQuestions.length === 0) {
        questionsList.innerHTML = `
            <div class="empty-state" role="status">
                <div class="empty-state-icon" aria-hidden="true">💭</div>
                <div class="empty-state-text">No questions yet. Share the meeting URL with your students!</div>
            </div>
        `;
        return;
    }

    // Sort: unanswered first (by upvotes), then answered at bottom (by upvotes)
    const sortedQuestions = [...approvedQuestions].sort((a, b) => {
        const aAnswered = a.is_answered_in_class || a.is_answered || false;
        const bAnswered = b.is_answered_in_class || b.is_answered || false;
        
        // If one is answered and one isn't, unanswered comes first
        if (aAnswered !== bAnswered) {
            return aAnswered ? 1 : -1;
        }
        
        // Within same answered status, sort by upvotes (descending)
        if (b.upvotes !== a.upvotes) {
            return b.upvotes - a.upvotes;
        }
        
        // Then by creation time (newest first)
        return new Date(b.created_at) - new Date(a.created_at);
    });

    // Separate questions into unanswered and answered
    const unansweredQuestions = sortedQuestions.filter(q => !(q.is_answered_in_class || q.is_answered));
    const answeredQuestions = sortedQuestions.filter(q => q.is_answered_in_class || q.is_answered);
    
    // Build HTML with section headers
    let questionsHtml = '';
    
    // Add unanswered section if there are unanswered questions
    if (unansweredQuestions.length > 0) {
        questionsHtml += `
            <div class="questions-section-header" style="margin: 20px 0 15px 0; padding: 10px 0; border-bottom: 2px solid #e1e8ed;">
                <h3 style="margin: 0; font-size: 1.1rem; color: #3498db; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.3rem;">🔵</span> Unanswered Questions
                </h3>
            </div>
        `;
    }
    
    questionsHtml += unansweredQuestions.map(q => {
        const createdTime = new Date(q.created_at).toLocaleTimeString();
        const isAnswered = q.is_answered_in_class || q.is_answered || false;
        const answeredClass = isAnswered ? 'answered' : '';
        const questionNumber = q.question_number || '?';
        const answerLabel = isAnswered ? 'Mark as unanswered' : 'Mark as answered';

        // Check if question has a written answer (published or draft)
        const hasWrittenAnswer = q.answer && q.answer.answer_text;
        const isPublished = hasWrittenAnswer && q.answer.is_approved;
        const answerText = hasWrittenAnswer ? q.answer.answer_text : '';

        // Render question text with markdown (no images - student submitted)
        const questionHtml = renderMarkdownNoImages(q.text);

        // Render answer text with full markdown (images allowed - instructor created)
        const answerHtml = hasWrittenAnswer ? renderMarkdownFull(answerText) : '';

        // Check if this question is flagged but has been approved and published
        // (indicated by having flagged_reason but also being allowed to appear in main list)
        // The status will be "flagged" if it has profanity, but we show "approved & published" badge if it has written answer or is not rejected
        const isFlaggedAndApproved = q.flagged_reason && q.status === 'flagged' && q.status !== 'rejected';

        return `
            <article class="question-card ${answeredClass} ${isFlaggedAndApproved ? 'previously-flagged' : ''}" role="article">
                <div class="question-header">
                    <div class="question-badge" aria-label="Question number ${questionNumber}">Q${questionNumber}</div>
                    <div class="question-content">
                        <div class="question-text markdown-content">${questionHtml}</div>
                        <div class="question-meta">
                            <time datetime="${q.created_at}">Asked at ${createdTime}</time>
                            ${isFlaggedAndApproved ? '<span class="approved-badge">✅ Approved & Published</span>' : ''}
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
                                onclick="openAnswerDialog(${q.id})"
                                data-question-text="${escapeHtml(q.text)}"
                                data-has-answer="${q.has_written_answer}"
                                aria-label="Write answer for this question">
                            ${q.has_written_answer ? '✏️ Edit Answer' : '📝 Write Answer'}
                        </button>
                        <button class="btn btn-danger"
                                onclick="deleteQuestion(${q.id})"
                                aria-label="Delete this question">
                            🗑️ Delete
                        </button>
                    </div>
                </div>
                ${hasWrittenAnswer ? `
                <div class="written-answer ${isPublished ? 'published' : 'draft'}" role="region" aria-label="${isPublished ? 'Published written answer' : 'Draft answer (not visible to students)'}">
                    <div class="written-answer-header">
                        <strong>📝 ${isPublished ? 'Published Answer' : 'Draft Answer (Not Published)'}</strong>
                    </div>
                    <div class="written-answer-text markdown-content">${answerHtml}</div>
                </div>
                ` : ''}
            </article>
        `;
    }).join('');
    
    // Add answered section if there are answered questions
    if (answeredQuestions.length > 0) {
        questionsHtml += `
            <div class="questions-section-header" style="margin: 30px 0 15px 0; padding: 10px 0; border-bottom: 2px solid #e1e8ed;">
                <h3 style="margin: 0; font-size: 1.1rem; color: #28a745; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.3rem;">✅</span> Answered Questions
                </h3>
            </div>
        `;
        
        questionsHtml += answeredQuestions.map(q => {
            const createdTime = new Date(q.created_at).toLocaleTimeString();
            const isAnswered = q.is_answered_in_class || q.is_answered || false;
            const answeredClass = isAnswered ? 'answered' : '';
            const questionNumber = q.question_number || '?';
            const answerLabel = isAnswered ? 'Mark as unanswered' : 'Mark as answered';

            // Check if question has a written answer (published or draft)
            const hasWrittenAnswer = q.answer && q.answer.answer_text;
            const isPublished = hasWrittenAnswer && q.answer.is_approved;
            const answerText = hasWrittenAnswer ? q.answer.answer_text : '';

            // Render question text with markdown (no images - student submitted)
            const questionHtml = renderMarkdownNoImages(q.text);

            // Render answer text with full markdown (images allowed - instructor created)
            const answerHtml = hasWrittenAnswer ? renderMarkdownFull(answerText) : '';

            // Check if this question is flagged but has been approved and published
            const isFlaggedAndApproved = q.flagged_reason && q.status === 'flagged' && q.status !== 'rejected';

            return `
                <article class="question-card ${answeredClass} ${isFlaggedAndApproved ? 'previously-flagged' : ''}" role="article">
                    <div class="question-header">
                        <div class="question-badge" aria-label="Question number ${questionNumber}">Q${questionNumber}</div>
                        <div class="question-content">
                            <div class="question-text markdown-content">${questionHtml}</div>
                            <div class="question-meta">
                                <time datetime="${q.created_at}">Asked at ${createdTime}</time>
                                ${isFlaggedAndApproved ? '<span class="approved-badge">✅ Approved & Published</span>' : ''}
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
                                    onclick="openAnswerDialog(${q.id})"
                                    data-question-text="${escapeHtml(q.text)}"
                                    data-has-answer="${q.has_written_answer}"
                                    aria-label="Write answer for this question">
                                ${q.has_written_answer ? '✏️ Edit Answer' : '📝 Write Answer'}
                            </button>
                            <button class="btn btn-danger"
                                    onclick="deleteQuestion(${q.id})"
                                    aria-label="Delete this question">
                                🗑️ Delete
                            </button>
                        </div>
                    </div>
                    ${hasWrittenAnswer ? `
                    <div class="written-answer ${isPublished ? 'published' : 'draft'}" role="region" aria-label="${isPublished ? 'Published written answer' : 'Draft answer (not visible to students)'}">
                        <div class="written-answer-header">
                            <strong>📝 ${isPublished ? 'Published Answer' : 'Draft Answer (Not Published)'}</strong>
                        </div>
                        <div class="written-answer-text markdown-content">${answerHtml}</div>
                    </div>
                    ` : ''}
                </article>
            `;
        }).join('');
    }

    questionsList.innerHTML = questionsHtml;

    // Trigger MathJax to process the new content
    if (window.MathJax && window.MathJax.typesetPromise) {
        MathJax.typesetPromise().catch((err) => console.log('MathJax error:', err));
    } else if (window.MathJax && window.MathJax.Hub) {
        // MathJax 2.x fallback
        MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
    }
}

async function toggleAnswered(questionId) {
    try {
        // v2 API: POST /api/questions/{id}/mark-answered-in-class
        const response = await authenticatedFetch(`/api/questions/${questionId}/mark-answered-in-class`, {
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
    
    // Open QR code in a new window that can be moved to another screen
    const qrWindow = window.open('', 'RaiseMyHandQR', 'width=600,height=700');
    
    if (!qrWindow) {
        showNotification('Please allow pop-ups to display QR code', 'error');
        return;
    }
    
    // Create a simple page with just the QR code
    const qrPageHTML = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RaiseMyHand - Scan to Join</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    background: white;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    padding: 20px;
                }
                .qr-container {
                    text-align: center;
                }
                .qr-title {
                    font-size: 2rem;
                    color: #2c3e50;
                    margin-bottom: 1rem;
                    font-weight: 700;
                }
                .qr-subtitle {
                    font-size: 1.1rem;
                    color: #7f8c8d;
                    margin-bottom: 2rem;
                }
                img {
                    max-width: 100%;
                    width: 400px;
                    height: 400px;
                    border: 4px solid #3498db;
                    border-radius: 12px;
                    padding: 10px;
                    background: white;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                }
                .instruction {
                    margin-top: 2rem;
                    font-size: 1rem;
                    color: #34495e;
                    line-height: 1.6;
                }
            </style>
        </head>
        <body>
            <div class="qr-container">
                <div class="qr-title">✋ RaiseMyHand</div>
                <div class="qr-subtitle">Scan to Join Session</div>
                <img src="${qrUrl}" alt="QR Code - Scan to join session">
                <div class="instruction">
                    Point your phone camera at this QR code to join the session
                </div>
            </div>
        </body>
        </html>
    `;
    
    qrWindow.document.write(qrPageHTML);
    qrWindow.document.close();
}

function hideQRCode() {
    const modal = document.getElementById('qr-modal');
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
}

function openPublicStats() {
    const baseUrl = config.base_url;
    const statsUrl = `${baseUrl}/stats?code=${meetingData.meeting_code}`;
    window.open(statsUrl, '_blank', 'noopener,noreferrer');
    navigator.clipboard.writeText(statsUrl).catch(() => {});
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
        // Use authenticatedFetch which handles both JWT and API key
        const response = await authenticatedFetch(`/api/meetings/${instructorCode}/end`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to end meeting');
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
        showNotification(`Failed to end meeting: ${error.message}`, 'error');
    } finally {
        hideButtonLoading(endBtn);
    }
}

async function restartSession() {
    const restartBtn = document.getElementById('restart-session-btn');
    showButtonLoading(restartBtn);

    try {
        // Use authenticatedFetch which handles both JWT and API key
        const response = await authenticatedFetch(`/api/meetings/${instructorCode}/restart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to restart meeting');
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
        showNotification(`Failed to restart meeting: ${error.message}`, 'error');
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

async function openAnswerDialog(questionId) {
    currentAnswerQuestionId = questionId;
    
    // Get question text and has_answer from data attributes
    const button = event.currentTarget;
    const questionText = button.getAttribute('data-question-text') || '';
    const hasAnswer = button.getAttribute('data-has-answer') === 'true';

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
            const response = await authenticatedFetch(`/api/questions/${questionId}/answer`);

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

    // Initialize EasyMDE markdown editor
    // Destroy existing instance if it exists to avoid conflicts
    if (easyMDE) {
        easyMDE.toTextArea();
        easyMDE = null;
    }

    // Create new instance
    setTimeout(() => {
        easyMDE = new EasyMDE({
            element: document.getElementById('answer-text'),
            spellChecker: false,
            toolbar: [
                'bold', 'italic', 'heading', '|',
                'quote', 'unordered-list', 'ordered-list', '|',
                'link', 'image', '|',
                'preview', 'side-by-side', 'fullscreen', '|',
                'guide'
            ],
            placeholder: 'Write your answer using markdown...',
            previewRender: (plainText) => {
                return marked.parse(plainText);
            },
            autofocus: true,
            status: false
        });

        // Set initial value if loading existing answer
        if (document.getElementById('answer-text').value) {
            easyMDE.value(document.getElementById('answer-text').value);
        }
    }, 100);
}

function closeAnswerDialog() {
    const modal = document.getElementById('answer-modal');
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');

    // Clean up EasyMDE instance
    if (easyMDE) {
        easyMDE.toTextArea();
        easyMDE = null;
    }

    currentAnswerQuestionId = null;
    currentAnswerData = null;
}

async function submitAnswer(event) {
    event.preventDefault();
    console.log('submitAnswer called');

    const questionId = document.getElementById('answer-question-id').value;
    console.log('Question ID:', questionId);

    // Get value from EasyMDE editor
    const answerText = easyMDE ? easyMDE.value() : document.getElementById('answer-text').value;
    console.log('Answer text length:', answerText ? answerText.length : 0);

    if (!answerText || !answerText.trim()) {
        showNotification('Please enter an answer', 'error');
        return;
    }

    try {
        const response = await authenticatedFetch(`/api/questions/${questionId}/answer`, {
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
            question.answer = data;
        }

        // Re-render questions to show "Edit Answer" button instead of "Write Answer"
        renderQuestions();

        // Don't close modal - allow user to publish or continue editing
    } catch (error) {
        console.error('Error saving answer:', error);
        showNotification('Failed to save answer', 'error');
    }
}

async function publishAnswer() {
    if (!currentAnswerQuestionId) return;

    try {
        const response = await authenticatedFetch(`/api/questions/${currentAnswerQuestionId}/answer/publish`, {
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

        // Update question in local data
        const question = meetingData.questions.find(q => q.id == currentAnswerQuestionId);
        if (question && question.answer) {
            question.answer.is_approved = true;
        }

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
        const response = await authenticatedFetch(`/api/questions/${currentAnswerQuestionId}/answer`, {
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

// Open student view in new tab
function openStudentView() {
    if (meetingData && meetingData.meeting_code) {
        const baseUrl = config.base_url;
        const studentUrl = `${baseUrl}/student?code=${meetingData.meeting_code}`;
        window.open(studentUrl, '_blank', 'noopener,noreferrer');
    } else {
        showNotification('Meeting data not loaded yet', 'error');
    }
}

// Tab Switching for Flagged Questions
function switchQuestionTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.tab-btn[data-tab="${tab}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tab}-questions-tab`).classList.add('active');

    // Load flagged questions if switching to that tab
    if (tab === 'flagged') {
        loadFlaggedQuestions();
    }
}

// Load Flagged Questions
async function loadFlaggedQuestions() {
    if (!instructorCode) {
        console.error('No instructorCode available');
        return;
    }

    console.log('[FLAGGED] Loading flagged questions for instructor code:', instructorCode);

    try {
        const url = `/api/meetings/${instructorCode}/flagged-questions`;
        console.log('[FLAGGED] Fetching from URL:', url);

        const response = await authenticatedFetch(url);
        console.log('[FLAGGED] Response status:', response.status);

        const data = await response.json();
        console.log('[FLAGGED] Data received:', data);

        const flaggedList = document.getElementById('flagged-questions-list');
        const flaggedCount = document.getElementById('flagged-count');

        if (data.questions && data.questions.length > 0) {
            console.log('[FLAGGED] Found', data.questions.length, 'flagged questions');
            flaggedCount.textContent = data.questions.length;
            flaggedList.innerHTML = data.questions.map(q => renderFlaggedQuestion(q)).join('');
        } else {
            console.log('[FLAGGED] No flagged questions found');
            flaggedCount.textContent = '0';
            flaggedList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">✅</div>
                    <div class="empty-state-text">No flagged questions. All questions are approved!</div>
                </div>
            `;
        }
    } catch (error) {
        console.error('[FLAGGED] Failed to load flagged questions:', error);
        showNotification('Failed to load flagged questions', 'error');
    }
}

// Render a Flagged Question Card
function renderFlaggedQuestion(q) {
    // Use sanitized text for display (profanity censored)
    const textToShow = q.sanitized_text || q.text;
    const questionHtml = renderMarkdownNoImages(textToShow);
    const reason = q.flagged_reason || 'inappropriate content';
    const isRejected = q.status === 'rejected';
    const isFlagged = q.status === 'flagged';

    // Show original text for comparison if there's a sanitized version
    const showComparison = q.sanitized_text && q.sanitized_text !== q.text;

    // Determine button states based on current status
    const approveButtonClass = isRejected ? 'btn-secondary' : 'btn-success';
    const rejectButtonClass = isRejected ? 'btn-success' : 'btn-secondary';
    const approveButtonLabel = isRejected ? '↩️ Approve' : '✓ Approve & Show';
    const rejectButtonLabel = isRejected ? '✗ Rejected' : '✗ Reject & Hide';

    return `
        <div class="question-card flagged ${isRejected ? 'rejected' : ''}" data-question-id="${q.id}">
            <div class="question-header">
                <span class="question-badge" aria-label="Question number ${q.question_number}">Q${q.question_number}</span>
                <div class="question-content">
                    <div class="question-text markdown-content">${questionHtml}</div>
                    <div class="question-meta">
                        <span class="flagged-badge">🚩 ${reason.charAt(0).toUpperCase() + reason.slice(1)}</span>
                        ${isRejected ? '<span class="status-badge rejected">Rejected</span>' : '<span class="status-badge flagged">Flagged</span>'}
                        <time datetime="${q.created_at}">${new Date(q.created_at).toLocaleString()}</time>
                    </div>
                </div>
            </div>
            ${showComparison ? `
                <div style="margin-top: 8px; padding: 8px; background: #fff3cd; border-left: 3px solid #ff9800; border-radius: 4px; font-size: 0.9em;">
                    <strong>Original text:</strong> ${escapeHtml(q.text)}<br>
                    <strong>Censored as:</strong> ${escapeHtml(q.sanitized_text)}<br>
                    <em>Profanity detected and censored</em>
                </div>
            ` : ''}
            <div class="question-actions moderation-actions">
                <button class="btn ${approveButtonClass}" 
                        onclick="approveQuestion(${q.id})"
                        aria-label="Approve this question"
                        ${isRejected ? '' : 'disabled'}>
                    ${approveButtonLabel}
                </button>
                <button class="btn ${rejectButtonClass}" 
                        onclick="rejectQuestion(${q.id})"
                        aria-label="Reject and hide this question"
                        ${isRejected ? 'disabled' : ''}>
                    ${rejectButtonLabel}
                </button>
                <button class="btn btn-danger"
                        onclick="deleteQuestion(${q.id})"
                        aria-label="Delete this question">
                    🗑️ Delete
                </button>
            </div>
        </div>
    `;
}

// Approve a Flagged Question
async function approveQuestion(questionId) {
    try {
        const response = await authenticatedFetch(`/api/questions/${questionId}/approve`, {
            method: 'POST'
        });

        if (response.ok) {
            showNotification('Question approved!', 'success');
            // Reload both lists
            loadFlaggedQuestions();
            loadSession(); // Reload main questions list
        } else {
            throw new Error('Failed to approve question');
        }
    } catch (error) {
        console.error('Failed to approve question:', error);
        showNotification('Failed to approve question', 'error');
    }
}

// Reject a Flagged Question
async function rejectQuestion(questionId) {
    if (!confirm('Are you sure you want to reject and hide this question?')) {
        return;
    }

    try {
        const response = await authenticatedFetch(`/api/questions/${questionId}/reject`, {
            method: 'POST'
        });

        if (response.ok) {
            showNotification('Question rejected', 'success');
            // Reload both lists
            loadFlaggedQuestions();
            loadSession(); // Reload main questions list
        } else {
            throw new Error('Failed to reject question');
        }
    } catch (error) {
        console.error('Failed to reject question:', error);
        showNotification('Failed to reject question', 'error');
    }
}

// Delete a Question
async function deleteQuestion(questionId) {
    if (!confirm('Are you sure you want to permanently delete this question? This cannot be undone.')) {
        return;
    }

    try {
        const response = await authenticatedFetch(`/api/questions/${questionId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Question deleted successfully', 'success');
            // Reload the questions list
            loadSession();
        } else {
            throw new Error('Failed to delete question');
        }
    } catch (error) {
        console.error('Failed to delete question:', error);
        showNotification('Failed to delete question', 'error');
    }
}

// Initialize
if (!instructorCode) {
    alert('Invalid instructor code');
    window.location.href = '/';
} else {
    console.log('[INSTRUCTOR] Page initialized with code:', instructorCode);
    console.log('[INSTRUCTOR] Starting to load session...');
    // Always try to load - handleAuth errors will redirect if needed
    loadSession();
}
