// Get meeting code from URL (v2 API uses "meeting_code")
const meetingCode = new URLSearchParams(window.location.search).get('code');
let meetingData = null;
let ws = null;
let upvotedQuestions = new Set();
let studentId = null; // Track student ID for vote tracking

console.log('[STUDENT] Meeting code from URL:', meetingCode);
console.log('[STUDENT] Full URL:', window.location.href);

if (!meetingCode) {
    console.error('[STUDENT] No meeting code found in URL');
    alert('Invalid meeting code');
    window.location.href = '/';
}

// Get or create student ID
function getStudentId() {
    let id = localStorage.getItem('student_id');
    if (!id) {
        id = 'student_' + Math.random().toString(36).substring(2, 15);
        localStorage.setItem('student_id', id);
    }
    return id;
}

studentId = getStudentId();

// Initialize profanity filter if available
let profanityFilter = null;
if (typeof Filter !== 'undefined') {
    profanityFilter = new Filter();
}

// Markdown rendering helpers
function renderMarkdownNoImages(text) {
    // Parse markdown to HTML
    const rawHtml = marked.parse(text);

    // Sanitize HTML and strip images (students can't use images)
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
        FORBID_TAGS: ['img'],
        FORBID_ATTR: ['src', 'srcset']
    });

    return cleanHtml;
}

function renderMarkdownFull(text) {
    // Parse markdown to HTML
    const rawHtml = marked.parse(text);

    // Sanitize HTML but allow images (for instructor answers)
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'img'],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt', 'title', 'class']
    });

    return cleanHtml;
}

async function loadSession() {
    try {
        const response = await fetch(`/api/meetings/${meetingCode}`);
        if (!response.ok) {
            throw new Error('Meeting not found');
        }
        meetingData = await response.json();

        // Check if meeting requires password
        if (meetingData.has_password) {
            const password = prompt('This meeting is password protected. Please enter the password:');
            if (!password) {
                alert('Password required to access this meeting');
                window.location.href = '/';
                return;
            }

            // Verify password
            const verifyResponse = await fetch(`/api/meetings/${meetingCode}/verify-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ password })
            });

            if (!verifyResponse.ok) {
                alert('Incorrect password');
                window.location.href = '/';
                return;
            }
        }

        // Update UI
        document.getElementById('session-title').textContent = meetingData.title;
        document.getElementById('session-code').textContent = meetingData.meeting_code;

        if (!meetingData.is_active) {
            // Hide the question submission form entirely when meeting has ended
            const form = document.getElementById('question-form');
            const formContainer = document.querySelector('.question-form');

            // Hide the form
            form.style.display = 'none';
            form.setAttribute('aria-hidden', 'true');

            // Show prominent message
            const endedMessage = document.createElement('div');
            endedMessage.className = 'session-ended-warning';
            endedMessage.setAttribute('role', 'alert');
            endedMessage.innerHTML = '⚠️ This meeting has ended. No new questions can be submitted.';
            formContainer.insertBefore(endedMessage, form);
        }

        renderQuestions();
        connectWebSocket();

        // Load upvoted questions from localStorage
        const stored = localStorage.getItem(`upvoted_${meetingCode}`);
        if (stored) {
            upvotedQuestions = new Set(JSON.parse(stored));
        }
    } catch (error) {
        alert('Failed to load meeting');
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${meetingCode}`;

    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    ws.onerror = (error) => {
        // WebSocket error - will attempt reconnection on close
    };

    ws.onclose = () => {
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };
}

function handleWebSocketMessage(message) {
    if (message.type === 'new_question') {
        // Add new question to meeting data
        meetingData.questions.push(message.question);
        renderQuestions();
    } else if (message.type === 'upvote' || message.type === 'vote_update') {
        // Update vote count
        const question = meetingData.questions.find(q => q.id === message.question_id);
        if (question) {
            question.upvotes = message.upvotes;
            renderQuestions();
        }
    } else if (message.type === 'answer') {
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

    // NOTE: Server-side filtering now handles removing flagged/rejected questions for students
    // All questions in this array are already approved for student viewing
    const visibleQuestions = questions;

    // Update count
    document.getElementById('question-count').textContent =
        `${visibleQuestions.length} question${visibleQuestions.length !== 1 ? 's' : ''}`;

    if (visibleQuestions.length === 0) {
        questionsList.innerHTML = `
            <div class="empty-state" role="status">
                <div class="empty-state-icon" aria-hidden="true">💭</div>
                <div class="empty-state-text">No questions yet. Be the first to ask!</div>
            </div>
        `;
        return;
    }

    // Sort by upvotes (descending), then by creation time
    const sortedQuestions = [...visibleQuestions].sort((a, b) => {
        if (b.upvotes !== a.upvotes) {
            return b.upvotes - a.upvotes;
        }
        return new Date(b.created_at) - new Date(a.created_at);
    });

    questionsList.innerHTML = sortedQuestions.map(q => {
        const createdTime = new Date(q.created_at).toLocaleTimeString();
        const isAnswered = q.is_answered_in_class || q.is_answered || false;
        const answeredClass = isAnswered ? 'answered' : '';
        const hasUpvoted = upvotedQuestions.has(q.id);
        const upvotedClass = hasUpvoted ? 'upvoted' : '';
        const questionNumber = q.question_number || '?';
        const voteLabel = hasUpvoted ? 'Remove upvote' : 'Upvote question';

        // Check if question has a published written answer
        const hasWrittenAnswer = q.answer && q.answer.is_approved;
        const answerText = hasWrittenAnswer ? q.answer.answer_text : '';

        // Render question text with markdown (no images allowed for students)
        const questionHtml = renderMarkdownNoImages(q.text);

        // Render answer text with full markdown (images allowed for instructors)
        const answerHtml = hasWrittenAnswer ? renderMarkdownFull(answerText) : '';

        return `
            <article class="question-card ${answeredClass}" role="article">
                <div class="question-header">
                    <div class="question-badge" aria-label="Question number ${questionNumber}">Q${questionNumber}</div>
                    <div class="question-content">
                        <div class="question-text markdown-content">${questionHtml}</div>
                        <div class="question-meta">
                            <time datetime="${q.created_at}">Asked at ${createdTime}</time>
                        </div>
                    </div>
                    <div class="question-actions">
                        ${isAnswered ? '<span class="answer-badge answered" title="This question was answered in class">✓ Answered</span>' : ''}
                        <button class="upvote-btn ${upvotedClass}"
                                onclick="toggleVote(${q.id})"
                                aria-label="${voteLabel}"
                                aria-pressed="${hasUpvoted}"
                                ${!meetingData.is_active ? 'disabled aria-disabled="true"' : ''}>
                            <span class="upvote-icon" aria-hidden="true">⬆️</span>
                            <span class="upvote-count" aria-label="${q.upvotes} upvotes">${q.upvotes}</span>
                        </button>
                    </div>
                </div>
                ${hasWrittenAnswer ? `
                <div class="written-answer" role="region" aria-label="Instructor's written answer">
                    <div class="written-answer-header">
                        <strong>📝 Instructor's Answer:</strong>
                    </div>
                    <div class="written-answer-text markdown-content">${answerHtml}</div>
                </div>
                ` : ''}
            </article>
        `;
    }).join('');
}

async function toggleVote(questionId) {
    const hasVoted = upvotedQuestions.has(questionId);

    try {
        // v2 API: toggle vote with student_id query param
        const response = await fetch(`/api/questions/${questionId}/vote?student_id=${studentId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to update vote');
        }

        const data = await response.json();

        // Update local storage based on server response
        if (data.action === 'removed') {
            upvotedQuestions.delete(questionId);
            showNotification('Vote removed', 'success');
        } else {
            upvotedQuestions.add(questionId);
            showNotification('Question upvoted!', 'success');
        }
        localStorage.setItem(`upvoted_${meetingCode}`, JSON.stringify([...upvotedQuestions]));

        // Update UI with new count from server
        const question = meetingData.questions.find(q => q.id === questionId);
        if (question) {
            question.upvotes = data.upvotes;
            renderQuestions();
        }
    } catch (error) {
        showNotification('Failed to update vote', 'error');
    }
}

// NOTE: Profanity filtering is now handled server-side
// Questions are checked and censored before being sent to students

document.getElementById('question-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!meetingData.is_active) {
        showNotification('This meeting has ended', 'error');
        return;
    }

    const formData = new FormData(e.target);
    const text = formData.get('text').trim();

    if (!text) {
        showNotification('Please enter a question', 'error');
        return;
    }

    // Client-side profanity check (warning only, not blocking)
    if (profanityFilter && profanityFilter.isProfane(text)) {
        const proceed = confirm(
            '⚠️ Your question may contain inappropriate language.\n\n' +
            'It will be flagged for instructor review before being visible to others.\n\n' +
            'Do you want to submit it anyway?'
        );
        if (!proceed) {
            return;
        }
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    showButtonLoading(submitBtn);

    try {
        // v2 API: POST to /api/meetings/{code}/questions
        const response = await fetch(`/api/meetings/${meetingCode}/questions`, {
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
        showNotification('Failed to submit question', 'error');
    } finally {
        hideButtonLoading(submitBtn);
    }
});

// showNotification() and escapeHtml() are provided by shared.js

// Initialize
loadSession();
