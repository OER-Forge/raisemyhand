// Load stats on page load
async function loadStats() {
    try {
        const response = await fetch('/api/admin/stats');
        if (!response.ok) throw new Error('Failed to load stats');

        const stats = await response.json();

        document.getElementById('total-sessions').textContent = stats.total_sessions;
        document.getElementById('active-sessions').textContent = stats.active_sessions;
        document.getElementById('total-questions').textContent = stats.total_questions;
        document.getElementById('total-upvotes').textContent = stats.total_upvotes;
        document.getElementById('sessions-24h').textContent = stats.sessions_last_24h;
        document.getElementById('ended-sessions').textContent = stats.ended_sessions;
    } catch (error) {
        console.error('Error loading stats:', error);
        showNotification('Failed to load statistics', 'error');
    }
}

async function loadSessions() {
    const activeOnly = document.getElementById('active-only').checked;
    const tbody = document.getElementById('sessions-tbody');

    try {
        const response = await fetch(`/api/admin/sessions?active_only=${activeOnly}&limit=100`);
        if (!response.ok) throw new Error('Failed to load sessions');

        const sessions = await response.json();

        if (sessions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px; color: #666;">
                        No sessions found
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = sessions.map(session => {
            const createdDate = new Date(session.created_at);
            const formattedDate = createdDate.toLocaleString();
            const statusBadge = session.is_active
                ? '<span class="badge badge-active">Active</span>'
                : '<span class="badge badge-ended">Ended</span>';

            const instructorUrl = `${window.location.origin}/instructor?code=${session.instructor_code}`;
            const studentUrl = `${window.location.origin}/student?code=${session.session_code}`;

            return `
                <tr>
                    <td><input type="checkbox" class="session-checkbox" value="${session.id}"></td>
                    <td><strong>${escapeHtml(session.title)}</strong></td>
                    <td>${formattedDate}</td>
                    <td>${statusBadge}</td>
                    <td>${session.question_count}</td>
                    <td>
                        <div style="font-size: 0.85rem;">
                            <div>Student: <span class="code-snippet">${session.session_code}</span></div>
                            <div>Instructor: <span class="code-snippet">${session.instructor_code}</span></div>
                        </div>
                    </td>
                    <td>
                        <button class="btn-view" onclick="window.open('${instructorUrl}', '_blank')">
                            👁️ View
                        </button>
                        ${session.is_active ? `
                        <button class="btn-view" onclick="endSessionAdmin(${session.id}, '${session.instructor_code}', '${escapeHtml(session.title)}')">
                            🛑 End
                        </button>
                        ` : `
                        <button class="btn-success" onclick="restartSessionAdmin(${session.id}, '${session.instructor_code}', '${escapeHtml(session.title)}')">
                            🔄 Restart
                        </button>
                        `}
                        <button class="btn-delete" onclick="deleteSession(${session.id}, '${escapeHtml(session.title)}')">
                            🗑️ Delete
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading sessions:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px; color: #dc3545;">
                    Error loading sessions. Please try again.
                </td>
            </tr>
        `;
        showNotification('Failed to load sessions', 'error');
    }
}

async function deleteSession(sessionId, sessionTitle) {
    if (!confirm(`Are you sure you want to delete the session "${sessionTitle}"?\n\nThis will permanently delete all questions and cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/sessions/${sessionId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete session');

        showNotification('Session deleted successfully', 'success');
        await loadStats();
        await loadSessions();
    } catch (error) {
        console.error('Error deleting session:', error);
        showNotification('Failed to delete session', 'error');
    }
}

function refreshSessions() {
    loadStats();
    loadSessions();
    showNotification('Data refreshed', 'success');
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        background: ${type === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

async function endSessionAdmin(sessionId, instructorCode, sessionTitle) {
    if (!confirm(`Are you sure you want to end the session "${sessionTitle}"?\n\nStudents will no longer be able to submit questions.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/sessions/${instructorCode}/end`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to end session');

        showNotification('Session ended successfully', 'success');
        await loadStats();
        await loadSessions();
    } catch (error) {
        console.error('Error ending session:', error);
        showNotification('Failed to end session', 'error');
    }
}

async function restartSessionAdmin(sessionId, instructorCode, sessionTitle) {
    if (!confirm(`Are you sure you want to restart the session "${sessionTitle}"?\n\nStudents will be able to submit questions again.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/sessions/${instructorCode}/restart`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to restart session');

        showNotification('Session restarted successfully', 'success');
        await loadStats();
        await loadSessions();
    } catch (error) {
        console.error('Error restarting session:', error);
        showNotification('Failed to restart session', 'error');
    }
}

function getSelectedSessionIds() {
    const checkboxes = document.querySelectorAll('.session-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

async function bulkEndSessions() {
    const sessionIds = getSelectedSessionIds();
    if (sessionIds.length === 0) {
        showNotification('Please select at least one session', 'error');
        return;
    }

    if (!confirm(`Are you sure you want to end ${sessionIds.length} session(s)?`)) {
        return;
    }

    try {
        const response = await fetch('/api/admin/sessions/bulk/end', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sessionIds)
        });

        if (!response.ok) throw new Error('Failed to end sessions');

        const result = await response.json();
        showNotification(result.message, 'success');
        await loadStats();
        await loadSessions();
    } catch (error) {
        console.error('Error ending sessions:', error);
        showNotification('Failed to end sessions', 'error');
    }
}

async function bulkRestartSessions() {
    const sessionIds = getSelectedSessionIds();
    if (sessionIds.length === 0) {
        showNotification('Please select at least one session', 'error');
        return;
    }

    if (!confirm(`Are you sure you want to restart ${sessionIds.length} session(s)?`)) {
        return;
    }

    try {
        const response = await fetch('/api/admin/sessions/bulk/restart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sessionIds)
        });

        if (!response.ok) throw new Error('Failed to restart sessions');

        const result = await response.json();
        showNotification(result.message, 'success');
        await loadStats();
        await loadSessions();
    } catch (error) {
        console.error('Error restarting sessions:', error);
        showNotification('Failed to restart sessions', 'error');
    }
}

async function bulkDeleteSessions() {
    const sessionIds = getSelectedSessionIds();
    if (sessionIds.length === 0) {
        showNotification('Please select at least one session', 'error');
        return;
    }

    if (!confirm(`Are you sure you want to DELETE ${sessionIds.length} session(s)?\n\nThis will permanently delete all questions and cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch('/api/admin/sessions/bulk/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sessionIds)
        });

        if (!response.ok) throw new Error('Failed to delete sessions');

        const result = await response.json();
        showNotification(result.message, 'success');
        await loadStats();
        await loadSessions();
    } catch (error) {
        console.error('Error deleting sessions:', error);
        showNotification('Failed to delete sessions', 'error');
    }
}

function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.session-checkbox');
    checkboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event listeners
document.getElementById('active-only').addEventListener('change', loadSessions);

// Auto-refresh every 30 seconds
setInterval(() => {
    loadStats();
    loadSessions();
}, 30000);

// Initialize
loadStats();
loadSessions();
