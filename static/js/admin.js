// Admin-specific authentication helper functions
// Note: Admin uses admin_token (JWT), different from instructor API keys
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
            const studentUrl = `${window.location.origin}/student?code=${session.meeting_code}`;

            return `
                <tr>
                    <td><input type="checkbox" class="session-checkbox" value="${session.id}"></td>
                    <td><strong>${escapeHtml(session.title)}</strong></td>
                    <td>${formattedDate}</td>
                    <td>${statusBadge}</td>
                    <td>${session.question_count}</td>
                    <td>
                        <div style="font-size: 0.85rem;">
                            <div>Student: <span class="code-snippet">${session.meeting_code}</span></div>
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

// showNotification() is provided by shared.js

async function endSessionAdmin(sessionId, instructorCode, sessionTitle) {
    if (!confirm(`Are you sure you want to end the session "${sessionTitle}"?\n\nStudents will no longer be able to submit questions.`)) {
        return;
    }

    try {
        // Get CSRF token
        const csrfToken = await getCsrfToken();

        // Use v2 endpoint - requires API key, but we can't use admin JWT
        // This won't work without proper admin API endpoints
        // For now, rely on bulk operations which use admin JWT
        const response = await fetch(`/api/meetings/${instructorCode}/end`, {
            method: 'POST',
            headers: {
                'X-CSRF-Token': csrfToken
            }
        });

        if (response.status === 401) {
            showNotification('Admin cannot end sessions - use bulk operations instead', 'error');
            return;
        }

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
        // Get CSRF token
        const csrfToken = await getCsrfToken();

        // Use v2 endpoint - requires API key, but we can't use admin JWT
        // This won't work without proper admin API endpoints
        // For now, rely on bulk operations which use admin JWT
        const response = await fetch(`/api/meetings/${instructorCode}/restart`, {
            method: 'POST',
            headers: {
                'X-CSRF-Token': csrfToken
            }
        });

        if (response.status === 401) {
            showNotification('Admin cannot restart sessions - use bulk operations instead', 'error');
            return;
        }

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

// escapeHtml() is provided by shared.js

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
loadInstructors();

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

// ============================================================================
// Instructor Management Functions
// ============================================================================

let searchDebounceTimer = null;

async function loadInstructors() {
    const searchTerm = document.getElementById('instructor-search')?.value || '';
    const statusFilter = document.getElementById('instructor-status-filter')?.value || '';
    const loginFilter = document.getElementById('instructor-login-filter')?.value || '';

    const tbody = document.getElementById('instructors-tbody');
    if (!tbody) return; // Tab might not be loaded yet

    try {
        // Build query parameters
        const params = new URLSearchParams();
        if (searchTerm) params.append('search', searchTerm);
        if (statusFilter) params.append('status', statusFilter);

        // Handle login filter
        if (loginFilter === 'never') {
            params.append('has_login', 'false');
        } else if (loginFilter) {
            params.append('last_login_days', loginFilter);
        }

        const response = await fetch(`/api/admin/instructors?${params.toString()}`, {
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to load instructors');

        const instructors = await response.json();
        renderInstructorsTable(instructors);
    } catch (error) {
        console.error('Error loading instructors:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #dc3545;">
                    Error loading instructors. Please try again.
                </td>
            </tr>
        `;
        showNotification('Failed to load instructors', 'error');
    }
}

function renderInstructorsTable(instructors) {
    const tbody = document.getElementById('instructors-tbody');

    if (instructors.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #666;">
                    No instructors found
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = instructors.map(instructor => {
        const createdDate = new Date(instructor.created_at);
        const lastLogin = instructor.last_login ? new Date(instructor.last_login) : null;

        // Badge styling
        let badgeClass = '';
        let badgeText = '';
        if (instructor.badge === 'active') {
            badgeClass = 'badge-active';
            badgeText = 'Active';
        } else if (instructor.badge === 'inactive') {
            badgeClass = 'badge-ended';
            badgeText = 'Inactive';
        } else if (instructor.badge === 'placeholder') {
            badgeClass = 'badge-placeholder';
            badgeText = 'Placeholder';
        }

        // Display name
        const displayName = instructor.display_name || instructor.username;
        const subtitle = instructor.email ? `<div style="font-size: 0.85rem; color: #666;">${escapeHtml(instructor.email)}</div>` : '';

        return `
            <tr data-instructor-id="${instructor.id}">
                <td><input type="checkbox" class="instructor-checkbox" value="${instructor.id}"></td>
                <td>
                    <div><strong>${escapeHtml(displayName)}</strong></div>
                    <div style="font-size: 0.85rem; color: #666;">@${escapeHtml(instructor.username)}</div>
                    ${subtitle}
                </td>
                <td><span class="badge ${badgeClass}">${badgeText}</span></td>
                <td>${instructor.classes_count}</td>
                <td>
                    ${instructor.sessions_count}
                    ${instructor.active_sessions_count > 0 ? `<span class="badge badge-active" style="font-size: 0.75rem; margin-left: 4px;">${instructor.active_sessions_count} active</span>` : ''}
                </td>
                <td>${lastLogin ? lastLogin.toLocaleString() : 'Never'}</td>
                <td>
                    <button class="btn-view instructor-view-btn">
                        👁️ View
                    </button>
                    ${instructor.is_active ? `
                    <button class="btn-delete instructor-deactivate-btn" style="background: #ffc107; color: #000;">
                        🚫 Deactivate
                    </button>
                    ` : `
                    <button class="btn-success instructor-activate-btn">
                        ✅ Activate
                    </button>
                    `}
                </td>
            </tr>
        `;
    }).join('');
    
    // Add event listeners using event delegation
    tbody.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.instructor-view-btn');
        const deactivateBtn = e.target.closest('.instructor-deactivate-btn');
        const activateBtn = e.target.closest('.instructor-activate-btn');
        
        const row = e.target.closest('tr');
        const instructorId = parseInt(row.getAttribute('data-instructor-id'));
        
        if (viewBtn) {
            viewInstructorDetail(instructorId);
        } else if (deactivateBtn) {
            const username = row.querySelector('strong').textContent;
            deactivateInstructor(instructorId, username);
        } else if (activateBtn) {
            const username = row.querySelector('strong').textContent;
            activateInstructor(instructorId, username);
        }
    });
}

function debouncedSearchInstructors() {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        loadInstructors();
    }, 500);
}

function filterInstructors() {
    loadInstructors();
}

function clearInstructorFilters() {
    document.getElementById('instructor-search').value = '';
    document.getElementById('instructor-status-filter').value = '';
    document.getElementById('instructor-login-filter').value = '';
    loadInstructors();
}

function toggleSelectAllInstructors() {
    const selectAllCheckbox = document.getElementById('select-all-instructors');
    const checkboxes = document.querySelectorAll('.instructor-checkbox');
    checkboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
}

function getSelectedInstructorIds() {
    const checkboxes = document.querySelectorAll('.instructor-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

async function activateInstructor(instructorId, username) {
    if (!confirm(`Activate instructor "${username}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/instructors/${instructorId}/activate`, {
            method: 'PATCH',
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to activate instructor');

        const result = await response.json();
        showNotification(result.message || 'Instructor activated successfully', 'success');
        loadInstructors();
    } catch (error) {
        console.error('Error activating instructor:', error);
        showNotification('Failed to activate instructor', 'error');
    }
}

async function deactivateInstructor(instructorId, username) {
    if (!confirm(`Deactivate instructor "${username}"?\n\nThey will not be able to login or access their sessions.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/instructors/${instructorId}/deactivate`, {
            method: 'PATCH',
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to deactivate instructor');

        const result = await response.json();
        showNotification(result.message || 'Instructor deactivated successfully', 'success');
        loadInstructors();
    } catch (error) {
        console.error('Error deactivating instructor:', error);
        showNotification('Failed to deactivate instructor', 'error');
    }
}

async function bulkActivateInstructors() {
    const instructorIds = getSelectedInstructorIds();
    if (instructorIds.length === 0) {
        showNotification('Please select at least one instructor', 'error');
        return;
    }

    if (!confirm(`Activate ${instructorIds.length} instructor(s)?`)) {
        return;
    }

    try {
        const response = await fetch('/api/admin/instructors/bulk/activate', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ instructor_ids: instructorIds })
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to activate instructors');

        const result = await response.json();
        showNotification(result.message, 'success');
        loadInstructors();

        // Uncheck select all
        document.getElementById('select-all-instructors').checked = false;
    } catch (error) {
        console.error('Error activating instructors:', error);
        showNotification('Failed to activate instructors', 'error');
    }
}

async function bulkDeactivateInstructors() {
    const instructorIds = getSelectedInstructorIds();
    if (instructorIds.length === 0) {
        showNotification('Please select at least one instructor', 'error');
        return;
    }

    if (!confirm(`Deactivate ${instructorIds.length} instructor(s)?\n\nThey will not be able to login or access their sessions.`)) {
        return;
    }

    try {
        const response = await fetch('/api/admin/instructors/bulk/deactivate', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ instructor_ids: instructorIds })
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to deactivate instructors');

        const result = await response.json();
        showNotification(result.message, 'success');
        loadInstructors();

        // Uncheck select all
        document.getElementById('select-all-instructors').checked = false;
    } catch (error) {
        console.error('Error deactivating instructors:', error);
        showNotification('Failed to deactivate instructors', 'error');
    }
}

async function bulkDeleteInstructors() {
    const instructorIds = getSelectedInstructorIds();
    if (instructorIds.length === 0) {
        showNotification('Please select at least one instructor', 'error');
        return;
    }

    if (!confirm(`⚠️ DELETE ${instructorIds.length} instructor(s)?\n\nThis will permanently delete:\n- All their classes\n- All their sessions\n- All questions in their sessions\n\nThis cannot be undone!`)) {
        return;
    }

    // Double confirmation
    if (!confirm('This is your last chance. Are you absolutely sure?')) {
        return;
    }

    try {
        const response = await fetch('/api/admin/instructors/bulk/delete', {
            method: 'DELETE',
            headers: getAuthHeaders(),
            body: JSON.stringify({ instructor_ids: instructorIds })
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to delete instructors');

        const result = await response.json();
        showNotification(result.message, 'success');
        loadInstructors();

        // Uncheck select all
        document.getElementById('select-all-instructors').checked = false;
    } catch (error) {
        console.error('Error deleting instructors:', error);
        showNotification('Failed to delete instructors', 'error');
    }
}

// ============================================================================
// Quick View Modal Functions
// ============================================================================

let currentInstructorId = null;

async function viewInstructorDetail(instructorId) {
    if (!instructorId || instructorId === 'null' || isNaN(instructorId)) {
        console.error('Invalid instructor ID:', instructorId);
        showNotification('Error: Invalid instructor ID', 'error');
        return;
    }
    
    currentInstructorId = instructorId;

    // Show modal
    const modal = document.getElementById('instructor-detail-modal');
    if (!modal) {
        console.error('Modal element not found!');
        return;
    }
    
    modal.setAttribute('aria-modal', 'true');

    try {
        const response = await fetch(`/api/admin/instructors/${instructorId}`, {
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to load instructor details');

        const instructor = await response.json();
        populateInstructorModal(instructor);
    } catch (error) {
        console.error('Error loading instructor details:', error);
        showNotification('Failed to load instructor details', 'error');
        hideInstructorDetailModal();
    }
}

function populateInstructorModal(instructor) {
    // Header info
    const displayName = instructor.display_name || instructor.username;
    document.getElementById('modal-instructor-name').textContent = displayName;
    document.getElementById('modal-instructor-username').textContent = `@${instructor.username}`;
    document.getElementById('modal-instructor-email').textContent = instructor.email || 'No email';

    // Badge
    let badgeClass = '';
    let badgeText = '';
    if (instructor.last_login === null) {
        badgeClass = 'badge-placeholder';
        badgeText = 'Placeholder';
    } else if (instructor.is_active) {
        badgeClass = 'badge-active';
        badgeText = 'Active';
    } else {
        badgeClass = 'badge-ended';
        badgeText = 'Inactive';
    }
    document.getElementById('modal-instructor-badge').innerHTML = `<span class="badge ${badgeClass}">${badgeText}</span>`;

    // Statistics
    document.getElementById('modal-classes-count').textContent = instructor.stats.classes_count;
    document.getElementById('modal-sessions-count').textContent = instructor.stats.sessions_count;
    document.getElementById('modal-active-sessions').textContent = instructor.stats.active_sessions_count;
    document.getElementById('modal-questions-count').textContent = instructor.stats.questions_count;
    document.getElementById('modal-upvotes-count').textContent = instructor.stats.upvotes_count;
    document.getElementById('modal-students-count').textContent = instructor.stats.unique_students_count;

    // Account info
    const createdDate = new Date(instructor.created_at);
    const lastLogin = instructor.last_login ? new Date(instructor.last_login) : null;
    document.getElementById('modal-created-at').textContent = createdDate.toLocaleString();
    document.getElementById('modal-last-login').textContent = lastLogin ? lastLogin.toLocaleString() : 'Never';
    document.getElementById('modal-api-keys-count').textContent = `${instructor.api_keys.length} key(s)`;

    // Recent sessions
    const sessionsContainer = document.getElementById('modal-recent-sessions');
    if (instructor.recent_sessions.length === 0) {
        sessionsContainer.innerHTML = `
            <div style="text-align: center; padding: 20px; color: #666;">
                No sessions found
            </div>
        `;
    } else {
        sessionsContainer.innerHTML = instructor.recent_sessions.map(session => {
            const sessionDate = new Date(session.created_at);
            const statusBadge = session.is_active
                ? '<span class="badge badge-active" style="font-size: 0.75rem;">Active</span>'
                : '<span class="badge badge-ended" style="font-size: 0.75rem;">Ended</span>';

            return `
                <div style="padding: 10px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600;">${escapeHtml(session.title)}</div>
                        <div style="font-size: 0.85rem; color: #666;">
                            ${sessionDate.toLocaleDateString()} • ${session.question_count} questions
                        </div>
                    </div>
                    <div>
                        ${statusBadge}
                    </div>
                </div>
            `;
        }).join('');
    }

    // Quick action buttons
    const activateBtn = document.getElementById('modal-activate-btn');
    const deactivateBtn = document.getElementById('modal-deactivate-btn');

    if (instructor.is_active) {
        activateBtn.style.display = 'none';
        deactivateBtn.style.display = 'inline-block';
    } else {
        activateBtn.style.display = 'inline-block';
        deactivateBtn.style.display = 'none';
    }
}

function hideInstructorDetailModal() {
    const modal = document.getElementById('instructor-detail-modal');
    if (modal) {
        modal.setAttribute('aria-modal', 'false');
    }
    // Don't reset currentInstructorId here - we might need it for viewFullDetails()
    // It will be reset when opening a new instructor or explicitly
}

async function activateFromModal() {
    if (!currentInstructorId) return;

    const username = document.getElementById('modal-instructor-username').textContent.replace('@', '');

    if (!confirm(`Activate instructor "${username}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/instructors/${currentInstructorId}/activate`, {
            method: 'PATCH',
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to activate instructor');

        showNotification('Instructor activated successfully', 'success');

        // Reload modal data
        await viewInstructorDetail(currentInstructorId);

        // Refresh list in background
        loadInstructors();
    } catch (error) {
        console.error('Error activating instructor:', error);
        showNotification('Failed to activate instructor', 'error');
    }
}

async function deactivateFromModal() {
    if (!currentInstructorId) return;

    const username = document.getElementById('modal-instructor-username').textContent.replace('@', '');

    if (!confirm(`Deactivate instructor "${username}"?\n\nThey will not be able to login or access their sessions.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/instructors/${currentInstructorId}/deactivate`, {
            method: 'PATCH',
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to deactivate instructor');

        showNotification('Instructor deactivated successfully', 'success');

        // Reload modal data
        await viewInstructorDetail(currentInstructorId);

        // Refresh list in background
        loadInstructors();
    } catch (error) {
        console.error('Error deactivating instructor:', error);
        showNotification('Failed to deactivate instructor', 'error');
    }
}

async function resetPasswordFromModal() {
    if (!currentInstructorId) return;

    const username = document.getElementById('modal-instructor-username').textContent.replace('@', '');

    if (!confirm(`Reset password for instructor "${username}"?\n\nA temporary password will be generated.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/instructors/${currentInstructorId}/reset-password`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to reset password');

        const result = await response.json();

        // Show password reset modal
        document.getElementById('reset-instructor-username').textContent = username;
        document.getElementById('temp-password-display').value = result.temporary_password;
        document.getElementById('password-reset-modal').setAttribute('aria-modal', 'true');

        // Auto-copy to clipboard
        await copyToClipboard(result.temporary_password);
        showNotification('Temporary password copied to clipboard', 'success');
    } catch (error) {
        console.error('Error resetting password:', error);
        showNotification('Failed to reset password', 'error');
    }
}

function hidePasswordResetModal() {
    document.getElementById('password-reset-modal').setAttribute('aria-modal', 'false');
    document.getElementById('temp-password-display').value = '';
}

function copyTempPassword() {
    const passwordInput = document.getElementById('temp-password-display');
    const copyBtn = document.getElementById('copy-temp-password-btn');

    navigator.clipboard.writeText(passwordInput.value).then(() => {
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '✓ Copied!';
        copyBtn.style.background = '#27ae60';

        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
        }, 2000);

        showNotification('Password copied to clipboard', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        passwordInput.select();
        showNotification('Please copy the password manually', 'warning');
    });
}

function viewFullDetails() {
    // Use currentInstructorId if available, otherwise log error
    if (!currentInstructorId || currentInstructorId === null || currentInstructorId === 'null') {
        console.error('No instructor ID available. currentInstructorId:', currentInstructorId);
        showNotification('Error: No instructor selected. Please view an instructor first.', 'error');
        return;
    }

    console.log('Opening full details for instructor ID:', currentInstructorId);

    // Hide modal
    hideInstructorDetailModal();

    // Navigate to full details page
    const url = `/admin/instructor-details?id=${currentInstructorId}`;
    window.location.href = url;
}

function refreshInstructors() {
    loadInstructors();
    showNotification('Instructors refreshed', 'success');
}
