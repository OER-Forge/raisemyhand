// Authentication helper functions
function getAuthHeaders() {
    const token = localStorage.getItem('admin_token');
    if (token) {
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    return {
        'Content-Type': 'application/json'
    };
}

function handleAuthError(response) {
    if (response.status === 401) {
        localStorage.removeItem('admin_token');
        window.location.href = '/admin-login';
        return true;
    }
    return false;
}

// Load stats on page load
async function loadStats() {
    try {
        const response = await fetch('/api/admin/stats', {
            headers: getAuthHeaders()
        });
        
        if (handleAuthError(response)) return;
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
        const response = await fetch(`/api/admin/sessions?active_only=${activeOnly}&limit=100`, {
            headers: getAuthHeaders()
        });
        
        if (handleAuthError(response)) return;
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
            method: 'DELETE',
            headers: getAuthHeaders()
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
            headers: getAuthHeaders(),
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
            headers: getAuthHeaders(),
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
            headers: getAuthHeaders(),
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

// Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('admin_token');
        window.location.href = '/admin-login';
    }
}

// Initialize
loadStats();
loadSessions();
loadApiKeys();

// API Key Management Functions
async function loadApiKeys() {
    try {
        const response = await fetch('/api/admin/api-keys', {
            headers: getAuthHeaders()
        });
        
        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to load API keys');

        const apiKeys = await response.json();
        renderApiKeys(apiKeys);
    } catch (error) {
        console.error('Error loading API keys:', error);
        showNotification('Failed to load API keys', 'error');
    }
}

function renderApiKeys(apiKeys) {
    const tbody = document.getElementById('api-keys-tbody');
    
    if (apiKeys.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px; color: #666;">
                    No API keys found. Create one to allow instructors to create sessions.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = apiKeys.map(key => {
        const createdDate = new Date(key.created_at);
        const lastUsedDate = key.last_used ? new Date(key.last_used) : null;
        const statusBadge = key.is_active
            ? '<span class="badge badge-active">Active</span>'
            : '<span class="badge badge-ended">Inactive</span>';

        return `
            <tr>
                <td><strong>${escapeHtml(key.name)}</strong></td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <code class="code-snippet" style="flex: 1; user-select: all;" id="key-${key.id}">
                            ${escapeHtml(key.key)}
                        </code>
                        <button class="btn-view" style="padding: 4px 8px; min-width: 70px;" onclick="copyApiKeyById(${key.id}, '${key.key}', this)">📋 Copy</button>
                    </div>
                </td>
                <td>${createdDate.toLocaleString()}</td>
                <td>${lastUsedDate ? lastUsedDate.toLocaleString() : 'Never'}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn-delete" onclick="deleteApiKey(${key.id}, '${escapeHtml(key.name)}')">🗑️ Delete</button>
                </td>
            </tr>
        `;
    }).join('');
}

function showCreateApiKeyModal() {
    document.getElementById('create-api-key-modal').classList.add('active');
    document.getElementById('api-key-name').value = '';
    // Focus the input after a short delay to ensure modal is visible
    setTimeout(() => {
        document.getElementById('api-key-name').focus();
    }, 100);
}

function hideCreateApiKeyModal() {
    document.getElementById('create-api-key-modal').classList.remove('active');
    document.getElementById('api-key-name').value = '';
}

function hideApiKeySuccessModal() {
    document.getElementById('api-key-success-modal').classList.remove('active');
    document.getElementById('new-api-key-value').value = '';
}

function copyNewApiKey() {
    const keyInput = document.getElementById('new-api-key-value');
    const copyBtn = document.getElementById('copy-new-key-btn');
    
    navigator.clipboard.writeText(keyInput.value).then(() => {
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '✓ Copied!';
        copyBtn.style.background = '#27ae60';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        // Fallback: select the text
        keyInput.select();
        showNotification('Please copy the key manually', 'warning');
    });
}

async function handleCreateApiKey(event) {
    event.preventDefault();
    
    const form = event.target;
    const name = form.name.value.trim();
    
    if (!name) {
        showNotification('Please enter a name for the API key', 'error');
        return;
    }

    try {
        const response = await fetch('/api/admin/api-keys', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ name: name })
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to create API key');

        const newKey = await response.json();
        
        // Hide create modal
        hideCreateApiKeyModal();
        
        // Show success modal with the key
        document.getElementById('new-api-key-value').value = newKey.key;
        document.getElementById('api-key-success-modal').classList.add('active');
        
        // Auto-copy to clipboard
        await copyToClipboard(newKey.key);
        
        // Refresh the list
        loadApiKeys();
    } catch (error) {
        console.error('Error creating API key:', error);
        showNotification('Failed to create API key', 'error');
    }
}

async function deleteApiKey(keyId, keyName) {
    if (!confirm(`Are you sure you want to delete the API key "${keyName}"?\n\nThis will prevent anyone using this key from creating new sessions.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/api-keys/${keyId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to delete API key');

        showNotification('API key deleted successfully', 'success');
        loadApiKeys(); // Refresh the list
    } catch (error) {
        console.error('Error deleting API key:', error);
        showNotification('Failed to delete API key', 'error');
    }
}

function copyApiKeyById(keyId, keyText, button) {
    navigator.clipboard.writeText(keyText).then(() => {
        const originalText = button.textContent;
        button.textContent = '✓ Copied!';
        button.style.background = '#28a745';
        showNotification('API key copied to clipboard', 'success');
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    }).catch(err => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = keyText;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('API key copied to clipboard', 'success');
            button.textContent = '✓ Copied!';
            setTimeout(() => {
                button.textContent = '📋 Copy';
            }, 2000);
        } catch (err) {
            showNotification('Failed to copy. Please select and copy manually.', 'error');
        }
        document.body.removeChild(textArea);
    });
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return true;
        } catch (err) {
            document.body.removeChild(textArea);
            return false;
        }
    }
}
