// Sessions Dashboard JavaScript - View all sessions for an API key

let allSessions = [];
let apiKey = null;

// Get API key from storage
function getApiKey() {
    return localStorage.getItem('instructor_api_key') || getCookie('instructor_api_key');
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function clearApiKey() {
    localStorage.removeItem('instructor_api_key');
    document.cookie = 'instructor_api_key=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
}

// Check authentication on load
function checkAuth() {
    apiKey = getApiKey();
    if (!apiKey) {
        const key = prompt('Please enter your API key to view your sessions:');
        if (key) {
            localStorage.setItem('instructor_api_key', key);
            apiKey = key;
            loadSessions();
        } else {
            alert('API key is required to view sessions.');
            window.location.href = '/';
        }
    } else {
        loadSessions();
    }
}

// Load all sessions for this API key
async function loadSessions() {
    try {
        const response = await fetch(`/api/sessions/my-sessions?api_key=${encodeURIComponent(apiKey)}`);
        
        if (response.status === 401) {
            clearApiKey();
            showNotification('Invalid API key. Please log in again.', 'error');
            setTimeout(() => {
                checkAuth();
            }, 2000);
            return;
        }
        
        if (!response.ok) {
            throw new Error('Failed to load sessions');
        }
        
        allSessions = await response.json();
        updateStats();
        renderSessions();
    } catch (error) {
        console.error('Error loading sessions:', error);
        showNotification('Failed to load sessions', 'error');
    }
}

// Update statistics
function updateStats() {
    const activeSessions = allSessions.filter(s => s.is_active);
    const totalQuestions = allSessions.reduce((sum, s) => sum + s.question_count, 0);
    const unansweredQuestions = allSessions.reduce((sum, s) => sum + s.unanswered_count, 0);
    
    document.getElementById('total-sessions').textContent = allSessions.length;
    document.getElementById('active-sessions').textContent = activeSessions.length;
    document.getElementById('total-questions').textContent = totalQuestions;
    document.getElementById('unanswered-questions').textContent = unansweredQuestions;
}

// Filter sessions
function filterSessions() {
    const filter = document.querySelector('input[name="status-filter"]:checked').value;
    renderSessions(filter);
}

// Render sessions
function renderSessions(filter = 'all') {
    const container = document.getElementById('sessions-list');
    const emptyState = document.getElementById('empty-state');
    
    let sessionsToShow = allSessions;
    
    if (filter === 'active') {
        sessionsToShow = allSessions.filter(s => s.is_active);
    } else if (filter === 'ended') {
        sessionsToShow = allSessions.filter(s => !s.is_active);
    }
    
    if (sessionsToShow.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    container.style.display = 'grid';
    emptyState.style.display = 'none';
    
    container.innerHTML = sessionsToShow.map(session => `
        <div class="session-card">
            <div class="session-header">
                <div>
                    <h3 class="session-title">${escapeHtml(session.title)}</h3>
                    <span class="badge ${session.is_active ? 'badge-active' : 'badge-ended'}">
                        ${session.is_active ? 'Active' : 'Ended'}
                    </span>
                </div>
            </div>
            
            <div class="session-meta">
                <span>📅 ${formatDate(session.created_at)}</span>
                ${session.ended_at ? `<span>⏱️ Ended ${formatDate(session.ended_at)}</span>` : ''}
            </div>
            
            <div class="session-stats">
                <div class="session-stat">
                    <span class="session-stat-label">Questions</span>
                    <span class="session-stat-value">${session.question_count}</span>
                </div>
                <div class="session-stat">
                    <span class="session-stat-label">Unanswered</span>
                    <span class="session-stat-value">${session.unanswered_count}</span>
                </div>
                <div class="session-stat">
                    <span class="session-stat-label">Total Upvotes</span>
                    <span class="session-stat-value">${session.total_upvotes}</span>
                </div>
            </div>
            
            <div class="session-actions">
                <a href="/instructor?code=${session.instructor_code}" class="btn btn-primary">
                    ${session.is_active ? 'Manage' : 'View'}
                </a>
                <a href="/student?code=${session.session_code}" class="btn btn-secondary" target="_blank">
                    Student View
                </a>
                ${session.is_active ? `
                    <button onclick="endSession('${session.instructor_code}')" class="btn" style="background: #f44336; color: white;">
                        End Session
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// End a session
async function endSession(instructorCode) {
    if (!confirm('Are you sure you want to end this session?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sessions/${instructorCode}/end?api_key=${encodeURIComponent(apiKey)}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to end session');
        }
        
        showNotification('Session ended successfully', 'success');
        loadSessions(); // Reload to update
    } catch (error) {
        console.error('Error ending session:', error);
        showNotification('Failed to end session', 'error');
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

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Auto-refresh every 30 seconds
setInterval(loadSessions, 30000);

// Initialize on page load
checkAuth();
