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
