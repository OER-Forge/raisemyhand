// Sessions Dashboard JavaScript - View all meetings for an API key (v2 API)
// NOTE: Uses shared.js for authentication utilities

let allMeetings = [];

// Check authentication on load
function checkAuth() {
    const apiKey = getApiKey();
    if (!apiKey) {
        const key = prompt('Please enter your API key to view your meetings:');
        if (key) {
            setApiKey(key);
            loadMeetings();
        } else {
            alert('API key is required to view meetings.');
            window.location.href = '/';
        }
    } else {
        loadMeetings();
    }
}

// Load all meetings for this API key (v2 API)
async function loadMeetings() {
    try {
        const apiKey = getApiKey();
        const response = await fetch(`/api/meetings?api_key=${apiKey}&include_ended=true`);
        
        if (response.status === 401) {
            clearApiKey();
            showNotification('Invalid API key. Please log in again.', 'error');
            setTimeout(() => {
                checkAuth();
            }, 2000);
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to load meetings');
        }

        allMeetings = await response.json();
        updateStats();
        renderMeetings();
    } catch (error) {
        console.error('Error loading meetings:', error);
        showNotification('Failed to load meetings', 'error');
    }
}

// Update statistics
function updateStats() {
    const activeMeetings = allMeetings.filter(m => m.is_active);
    const totalQuestions = allMeetings.reduce((sum, m) => sum + (m.question_count || 0), 0);
    const unansweredQuestions = 0; // TODO: Add unanswered count to API response

    document.getElementById('total-sessions').textContent = allMeetings.length;
    document.getElementById('active-sessions').textContent = activeMeetings.length;
    document.getElementById('total-questions').textContent = totalQuestions;
    document.getElementById('unanswered-questions').textContent = unansweredQuestions;
}

// Filter meetings
function filterSessions() {
    const filter = document.querySelector('input[name="status-filter"]:checked').value;
    renderMeetings(filter);
}

// Render meetings (v2 API)
function renderMeetings(filter = 'all') {
    const container = document.getElementById('sessions-list');
    const emptyState = document.getElementById('empty-state');

    let meetingsToShow = allMeetings;

    if (filter === 'active') {
        meetingsToShow = allMeetings.filter(m => m.is_active);
    } else if (filter === 'ended') {
        meetingsToShow = allMeetings.filter(m => !m.is_active);
    }

    if (meetingsToShow.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    container.style.display = 'grid';
    emptyState.style.display = 'none';

    container.innerHTML = meetingsToShow.map(meeting => `
        <div class="session-card">
            <div class="session-header">
                <div>
                    <h3 class="session-title">${escapeHtml(meeting.title)}</h3>
                    <span class="badge ${meeting.is_active ? 'badge-active' : 'badge-ended'}">
                        ${meeting.is_active ? 'Active' : 'Ended'}
                    </span>
                </div>
            </div>

            <div class="session-meta">
                <span>📅 ${formatDate(meeting.created_at)}</span>
                ${meeting.ended_at ? `<span>⏱️ Ended ${formatDate(meeting.ended_at)}</span>` : ''}
            </div>

            <div class="session-stats">
                <div class="session-stat">
                    <span class="session-stat-label">Questions</span>
                    <span class="session-stat-value">${meeting.question_count || 0}</span>
                </div>
                <div class="session-stat">
                    <span class="session-stat-label">Class ID</span>
                    <span class="session-stat-value">${meeting.class_id}</span>
                </div>
                <div class="session-stat">
                    <span class="session-stat-label">Code</span>
                    <span class="session-stat-value">${meeting.meeting_code}</span>
                </div>
            </div>

            <div class="session-actions">
                <a href="/instructor?code=${meeting.instructor_code}" class="btn btn-primary">
                    ${meeting.is_active ? 'Manage' : 'View'}
                </a>
                <a href="/student?code=${meeting.meeting_code}" class="btn btn-secondary" target="_blank">
                    Student View
                </a>
                ${meeting.is_active ? `
                    <button onclick="endMeeting('${meeting.instructor_code}')" class="btn" style="background: #f44336; color: white;">
                        End Meeting
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// End a meeting (v2 API)
async function endMeeting(instructorCode) {
    if (!confirm('Are you sure you want to end this meeting?')) {
        return;
    }

    try {
        const apiKey = getApiKey();
        const response = await fetch(`/api/meetings/${instructorCode}/end?api_key=${apiKey}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to end meeting');
        }

        showNotification('Meeting ended successfully', 'success');
        loadMeetings(); // Reload to update
    } catch (error) {
        console.error('Error ending meeting:', error);
        showNotification('Failed to end meeting', 'error');
    }
}

// Logout
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        clearApiKey();
        window.location.href = '/';
    }
}

// Modal functions
function openCreateSessionModal() {
    console.log('openCreateSessionModal called');
    const modal = document.getElementById('create-session-modal');
    if (!modal) {
        console.error('Modal element not found!');
        alert('Error: Modal element not found. Please refresh the page.');
        return;
    }
    console.log('Modal found, opening...');
    modal.classList.add('active');
    document.getElementById('session-title').value = '';
    document.getElementById('session-password').value = '';
    document.getElementById('session-title').focus();
}

function closeCreateSessionModal() {
    const modal = document.getElementById('create-session-modal');
    modal.classList.remove('active');
}

// Create a new session (v2 API)
async function createSession(event) {
    event.preventDefault();

    const title = document.getElementById('session-title').value.trim();
    const password = document.getElementById('session-password').value;
    const apiKey = getApiKey();

    if (!title) {
        showNotification('Please enter a session name', 'error');
        return;
    }

    try {
        // First, get instructor's classes to find default class
        const classesResponse = await fetch(`/api/classes?api_key=${encodeURIComponent(apiKey)}`);

        if (classesResponse.status === 401) {
            showNotification('Invalid API key', 'error');
            clearApiKey();
            setTimeout(() => window.location.href = '/instructor-login', 2000);
            return;
        }

        if (!classesResponse.ok) {
            showNotification('Failed to verify API key', 'error');
            return;
        }

        const classes = await classesResponse.json();

        // Find or create default class
        let classId;
        const defaultClass = classes.find(c => c.name === "Default Class");

        if (defaultClass) {
            classId = defaultClass.id;
        } else {
            // Create a new default class
            const createClassResponse = await fetch(`/api/classes?api_key=${encodeURIComponent(apiKey)}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: "Default Class", description: "Auto-created default class" })
            });

            if (!createClassResponse.ok) {
                showNotification('Failed to create class', 'error');
                return;
            }

            const newClass = await createClassResponse.json();
            classId = newClass.id;
        }

        // Now create the meeting
        const payload = { title: title };
        if (password) {
            payload.password = password;
        }

        const response = await fetch(`/api/classes/${classId}/meetings?api_key=${encodeURIComponent(apiKey)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            showNotification('Invalid API key', 'error');
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Failed to create meeting', 'error');
            return;
        }

        const meeting = await response.json();

        // Close modal
        closeCreateSessionModal();

        // Show success and redirect to instructor view
        showNotification('Meeting created successfully!', 'success');
        setTimeout(() => {
            window.location.href = `/instructor?code=${meeting.instructor_code}`;
        }, 1000);

    } catch (error) {
        console.error('Error creating meeting:', error);
        showNotification('Failed to create meeting. Please try again.', 'error');
    }
}

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('create-session-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeCreateSessionModal();
            }
        });
    }
});

// Helper functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Utility functions (escapeHtml, showNotification) are in shared.js

// Auto-refresh every 30 seconds
setInterval(loadMeetings, 30000);

// Initialize on page load
checkAuth();
