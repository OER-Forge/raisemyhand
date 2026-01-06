// Variable declarations
let currentInstructorId = null;

// Tab Switching with Persistence
function switchTab(tabName) {
    // Close any open modals
    const createUserModal = document.getElementById('create-user-modal');
    if (createUserModal) {
        closeCreateUserModal();
    }
    
    // Save active tab to localStorage
    localStorage.setItem('adminActiveTab', tabName);

    // Update URL without page reload using history.replaceState
    window.history.replaceState({ tab: tabName }, '', window.location.pathname);

    // Hide all panels
    document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
        panel.setAttribute('aria-hidden', 'true');
    });

    // Deselect all buttons
    document.querySelectorAll('[role="tab"]').forEach(button => {
        button.setAttribute('aria-selected', 'false');
        button.setAttribute('tabindex', '-1');
    });

    // Show selected panel
    const selectedPanel = document.getElementById(`panel-${tabName}`);
    if (selectedPanel) {
        selectedPanel.setAttribute('aria-hidden', 'false');
    }

    // Select active button
    const selectedButton = document.getElementById(`tab-${tabName}`);
    if (selectedButton) {
        selectedButton.setAttribute('aria-selected', 'true');
        selectedButton.setAttribute('tabindex', '0');
        selectedButton.focus();
    }

    // Load data for the selected tab
    switch(tabName) {
        case 'overview':
            loadStats();
            break;
        case 'api-keys':
            loadApiKeys();
            break;
        case 'sessions':
            loadSessions();
            break;
        case 'users':
            loadInstructorList();
            break;
    }
}

// Tab Hamburger Menu (Mobile)
function initTabHamburgerMenu() {
    const hamburgerBtn = document.getElementById('tab-hamburger-btn');
    const tabList = document.getElementById('tab-menu-list');
    const overlay = document.getElementById('tab-menu-overlay');
    
    if (!hamburgerBtn || !tabList || !overlay) return;
    
    // Toggle menu on hamburger click
    hamburgerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = tabList.classList.contains('open');
        if (isOpen) {
            closeTabMenu();
        } else {
            openTabMenu();
        }
    });
    
    // Close menu on overlay click
    overlay.addEventListener('click', closeTabMenu);
    
    // Close menu on tab button click
    tabList.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', closeTabMenu);
    });
    
    // Close menu on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && tabList.classList.contains('open')) {
            closeTabMenu();
            hamburgerBtn.focus();
        }
    });
    
    // Close menu on window resize (when switching to desktop)
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (window.innerWidth > 768 && tabList.classList.contains('open')) {
                closeTabMenu();
            }
        }, 250);
    });
}

function openTabMenu() {
    const hamburgerBtn = document.getElementById('tab-hamburger-btn');
    const tabList = document.getElementById('tab-menu-list');
    const overlay = document.getElementById('tab-menu-overlay');
    
    if (tabList) {
        tabList.classList.add('open');
        hamburgerBtn.setAttribute('aria-expanded', 'true');
        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
}

function closeTabMenu() {
    const hamburgerBtn = document.getElementById('tab-hamburger-btn');
    const tabList = document.getElementById('tab-menu-list');
    const overlay = document.getElementById('tab-menu-overlay');
    
    if (tabList) {
        tabList.classList.remove('open');
        hamburgerBtn.setAttribute('aria-expanded', 'false');
        overlay.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// Initialize tab on page load - restore from localStorage or use default
window.addEventListener('load', function() {
    // First, check if URL has a hash (anchor) - ignore it
    // Instead, use localStorage to remember the last tab
    const savedTab = localStorage.getItem('adminActiveTab') || 'overview';
    
    // Remove any hash from URL to prevent browser jumping
    if (window.location.hash) {
        window.history.replaceState(null, '', window.location.pathname);
    }
    
    // Initialize hamburger menu for mobile
    initTabHamburgerMenu();
    
    switchTab(savedTab);
});

// Handle browser back/forward buttons
window.addEventListener('popstate', function(event) {
    const tabName = event.state?.tab || localStorage.getItem('adminActiveTab') || 'overview';
    switchTab(tabName);
});

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

// Global sessions data for filtering
let allSessions = [];
let currentDateRange = 'all';

async function loadSessions() {
    const grid = document.getElementById('sessions-grid');

    try {
        const response = await fetch(`/api/admin/sessions?limit=500`, {
            headers: getAuthHeaders()
        });
        
        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to load sessions');

        allSessions = await response.json();
        filterSessions();
    } catch (error) {
        console.error('Error loading sessions:', error);
        grid.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #dc3545; grid-column: 1 / -1;">
                Error loading sessions. Please try again.
            </div>
        `;
        showNotification('Failed to load sessions', 'error');
    }
}

function filterSessions() {
    const searchTerm = document.getElementById('sessions-search')?.value.toLowerCase() || '';
    const status = document.querySelector('input[name="sessions-status"]:checked')?.value || 'all';
    const sortBy = document.getElementById('sessions-sort')?.value || 'created-newest';
    const grid = document.getElementById('sessions-grid');

    // Filter sessions
    let filtered = allSessions.filter(session => {
        // Search filter
        if (searchTerm && !session.title.toLowerCase().includes(searchTerm)) {
            return false;
        }

        // Status filter
        if (status === 'active' && !session.is_active) return false;
        if (status === 'ended' && session.is_active) return false;

        // Date range filter
        if (currentDateRange !== 'all') {
            const sessionDate = new Date(session.created_at);
            const now = new Date();
            const diffDays = Math.floor((now - sessionDate) / (1000 * 60 * 60 * 24));

            if (currentDateRange === 'today' && diffDays > 0) return false;
            if (currentDateRange === 'week' && diffDays > 7) return false;
            if (currentDateRange === 'month' && diffDays > 30) return false;
        }

        return true;
    });

    // Sort sessions
    switch(sortBy) {
        case 'created-oldest':
            filtered.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            break;
        case 'questions-most':
            filtered.sort((a, b) => (b.question_count || 0) - (a.question_count || 0));
            break;
        case 'title-az':
            filtered.sort((a, b) => a.title.localeCompare(b.title));
            break;
        case 'created-newest':
        default:
            filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }

    // Render cards
    if (filtered.length === 0) {
        grid.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666; grid-column: 1 / -1;">
                <div style="font-size: 48px; margin-bottom: 10px;">📭</div>
                <p>No sessions found matching your filters</p>
            </div>
        `;
        document.getElementById('sessions-count').textContent = '0 sessions';
        return;
    }

    grid.innerHTML = filtered.map(session => {
        const createdDate = new Date(session.created_at);
        const formattedDate = createdDate.toLocaleDateString();
        const formattedTime = createdDate.toLocaleTimeString();
        const statusBadge = session.is_active
            ? '<span class="badge badge-active">Active</span>'
            : '<span class="badge badge-ended">Ended</span>';

        const instructorUrl = `${window.location.origin}/instructor?code=${session.instructor_code}`;

        return `
            <div class="session-card">
                <div class="session-card-header">
                    <div style="flex: 1;">
                        <h3 class="session-card-title">${escapeHtml(session.title)}</h3>
                    </div>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <input type="checkbox" class="session-checkbox" value="${session.id}" style="width: 20px; height: 20px; cursor: pointer;">
                        ${statusBadge}
                    </div>
                </div>

                <div class="session-card-meta">
                    <span>📅 ${formattedDate}</span>
                    <span>🕐 ${formattedTime}</span>
                </div>

                <div class="session-card-stats">
                    <div class="session-card-stat">
                        <div class="session-card-stat-label">Questions</div>
                        <div class="session-card-stat-value">${session.question_count || 0}</div>
                    </div>
                    <div class="session-card-stat">
                        <div class="session-card-stat-label">Students</div>
                        <div class="session-card-stat-value">${session.students_count || 0}</div>
                    </div>
                </div>

                <div class="session-card-codes">
                    <div>👨‍🏫 Instructor: <strong>${escapeHtml(session.instructor_name)}</strong></div>
                </div>

                <div class="session-card-actions">
                    <button class="btn btn-secondary" onclick="window.open('${instructorUrl}', '_blank')" style="flex: 1; min-height: 40px;">👁️ View</button>
                    ${session.is_active ? `
                    <button class="btn btn-secondary" onclick="endSessionAdmin(${session.id}, '${session.instructor_code}', '${escapeHtml(session.title)}')" style="flex: 1; min-height: 40px;">🛑 End</button>
                    ` : `
                    <button class="btn btn-success" onclick="restartSessionAdmin(${session.id}, '${session.instructor_code}', '${escapeHtml(session.title)}')" style="flex: 1; min-height: 40px;">🔄 Restart</button>
                    `}
                    <button class="btn btn-danger" onclick="deleteSession(${session.id}, '${escapeHtml(session.title)}')" style="flex: 1; min-height: 40px;">🗑️ Delete</button>
                </div>
            </div>
        `;
    }).join('');

    document.getElementById('sessions-count').textContent = `${filtered.length} session${filtered.length !== 1 ? 's' : ''}`;
}

function setSessionDateRange(range) {
    currentDateRange = range;
    
    // Update active button
    document.querySelectorAll('.date-filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.range === range) {
            btn.classList.add('active');
        }
    });

    filterSessions();
}

function clearSessionFilters() {
    document.getElementById('sessions-search').value = '';
    document.querySelector('input[name="sessions-status"][value="all"]').checked = true;
    document.getElementById('sessions-sort').value = 'created-newest';
    currentDateRange = 'all';
    
    document.querySelectorAll('.date-filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.range === 'all') {
            btn.classList.add('active');
        }
    });

    filterSessions();
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

        // Use key_masked (or key_preview) if available, otherwise fall back to key field
        const displayKey = key.key_masked || key.key_preview || key.key;

        // Display instructor info: prefer display_name, fallback to username
        const instructorDisplay = key.instructor_display_name || key.instructor_username || 'Unknown';

        return `
            <tr>
                <td><strong>${escapeHtml(instructorDisplay)}</strong></td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <code class="code-snippet" style="flex: 1; user-select: all;" id="key-${key.id}">
                            ${escapeHtml(displayKey)}
                        </code>
                        <button class="btn-view" style="padding: 4px 8px; min-width: 70px;" id="reveal-btn-${key.id}" onclick="revealApiKey(${key.id}, this)">👁️ Reveal</button>
                    </div>
                </td>
                <td>${createdDate.toLocaleString()}</td>
                <td>${lastUsedDate ? lastUsedDate.toLocaleString() : 'Never'}</td>
                <td>${statusBadge}</td>
                <td>
                    ${key.is_active ? `
                        <button class="btn-warning" style="margin-right: 5px;" onclick="regenerateApiKeyFromDashboard(${key.instructor_id}, '${escapeHtml(instructorDisplay)}')">
                            🔄 Regenerate
                        </button>
                        <button class="btn-delete" onclick="deleteApiKey(${key.id}, '${escapeHtml(instructorDisplay)}')">
                            🔒 Revoke
                        </button>
                    ` : `
                        <span style="color: #999;">Revoked</span>
                    `}
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

async function regenerateApiKeyFromDashboard(instructorId, instructorName) {
    const reason = prompt(`Regenerate API key for ${instructorName}?\n\nThis will revoke all active keys and create a new one.\n\nPlease provide a reason (e.g., "Compromised", "Security update"):`);

    if (!reason || reason.trim() === '') {
        return; // User cancelled or provided empty reason
    }

    try {
        const response = await fetch(`/api/admin/api-keys/${instructorId}/regenerate`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason: reason.trim() })
        });

        if (handleAuthError(response)) return;

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to regenerate API key');
        }

        const result = await response.json();

        // Show the new API key
        const newKey = result.api_key.key;
        const message = `✅ New API key generated successfully!\n\nKey: ${newKey}\n\n⚠️ IMPORTANT: Copy this key now! You won't be able to see it again.\n\nThis key has been copied to your clipboard.`;

        // Copy to clipboard
        if (navigator.clipboard) {
            await navigator.clipboard.writeText(newKey);
        } else {
            // Fallback
            const textArea = document.createElement('textarea');
            textArea.value = newKey;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
        }

        alert(message);

        showNotification('API key regenerated successfully', 'success');
        loadApiKeys(); // Refresh the list
    } catch (error) {
        console.error('Error regenerating API key:', error);
        showNotification(`Failed to regenerate API key: ${error.message}`, 'error');
    }
}

async function deleteApiKey(keyId, keyName) {
    // First confirm the revocation
    if (!confirm(`Are you sure you want to revoke the API key for "${keyName}"?\n\nThis will prevent anyone using this key from accessing the system.`)) {
        return;
    }

    // Prompt for revocation reason
    const reason = prompt('Please provide a reason for revoking this API key:', 'Security policy');
    if (!reason) {
        showNotification('Revocation cancelled - no reason provided', 'info');
        return;
    }

    try {
        const response = await fetch(`/api/admin/api-keys/${keyId}`, {
            method: 'DELETE',
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason: reason })
        });

        if (handleAuthError(response)) return;
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to revoke API key');
        }

        showNotification('API key revoked successfully', 'success');
        loadApiKeys(); // Refresh the list
    } catch (error) {
        console.error('Error revoking API key:', error);
        showNotification(`Failed to revoke API key: ${error.message}`, 'error');
    }
}

async function revealApiKey(keyId, button) {
    try {
        const response = await fetch(`/api/admin/api-keys/${keyId}`, {
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to reveal API key');

        const apiKey = await response.json();
        const codeElement = document.getElementById(`key-${keyId}`);

        // Check if already revealed
        if (codeElement.textContent.includes(apiKey.key)) {
            // Already revealed, now hide it
            hideApiKey(keyId, button);
            return;
        }

        // Reveal the key
        codeElement.textContent = apiKey.key;
        button.textContent = '🙈 Hide';
        button.style.background = '#f39c12';

        // Add copy button functionality
        codeElement.style.userSelect = 'all';
        showNotification('API key revealed! Be careful with this key.', 'warning');

    } catch (error) {
        console.error('Error revealing API key:', error);
        showNotification('Failed to reveal API key', 'error');
    }
}

function hideApiKey(keyId, button) {
    const codeElement = document.getElementById(`key-${keyId}`);
    // Restore masked version - need to get it from somewhere
    // For now, use a fallback pattern
    const masked = codeElement.textContent.substring(0, 7) + '...' + codeElement.textContent.slice(-4);
    codeElement.textContent = masked;
    button.textContent = '👁️ Reveal';
    button.style.background = '';
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
    const grid = document.getElementById('instructors-grid');

    if (!grid) return; // Tab might not be loaded yet

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
        renderInstructorsCards(instructors);
    } catch (error) {
        console.error('Error loading instructors:', error);
        grid.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #dc3545; grid-column: 1 / -1;">
                Error loading instructors. Please try again.
            </div>
        `;
        showNotification('Failed to load instructors', 'error');
    }
}

function renderInstructorsCards(instructors) {
    const grid = document.getElementById('instructors-grid');
    const countEl = document.getElementById('instructor-count');

    if (instructors.length === 0) {
        grid.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666; grid-column: 1 / -1;">
                <div style="font-size: 48px; margin-bottom: 10px;">👥</div>
                <p>No instructors found</p>
            </div>
        `;
        countEl.textContent = '0 instructors';
        return;
    }

    grid.innerHTML = instructors.map(instructor => {
        const lastLogin = instructor.last_login ? new Date(instructor.last_login) : null;
        const displayName = instructor.display_name || instructor.username;

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

        // Role styling
        let roleColor = '#4a90e2';
        if (instructor.role === 'ADMIN') roleColor = '#f39c12';
        else if (instructor.role === 'SUPER_ADMIN') roleColor = '#e74c3c';
        else if (instructor.role === 'INACTIVE') roleColor = '#95a5a6';

        return `
            <div class="instructor-card" data-instructor-id="${instructor.id}">
                <div class="instructor-card-header">
                    <div style="flex: 1;">
                        <h3 class="instructor-card-name">${escapeHtml(displayName)}</h3>
                        <div style="font-size: 13px; color: var(--text-secondary);">@${escapeHtml(instructor.username)}</div>
                    </div>
                    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                        <span style="font-size: 11px; padding: 4px 8px; border-radius: 4px; background-color: ${roleColor}20; color: ${roleColor}; font-weight: 600;">${instructor.role}</span>
                        <input type="checkbox" class="instructor-checkbox" value="${instructor.id}" style="width: 20px; height: 20px; cursor: pointer;">
                        <span class="badge ${badgeClass}">${badgeText}</span>
                    </div>
                </div>

                ${instructor.email ? `<div class="instructor-card-email">${escapeHtml(instructor.email)}</div>` : ''}

                <div class="instructor-card-stats">
                    <div class="instructor-card-stat">
                        <div class="instructor-card-stat-label">Classes</div>
                        <div class="instructor-card-stat-value">${instructor.classes_count}</div>
                    </div>
                    <div class="instructor-card-stat">
                        <div class="instructor-card-stat-label">Sessions</div>
                        <div class="instructor-card-stat-value">${instructor.sessions_count}</div>
                    </div>
                    ${instructor.active_sessions_count > 0 ? `
                    <div class="instructor-card-stat">
                        <div class="instructor-card-stat-label">Active</div>
                        <div class="instructor-card-stat-value" style="color: #28a745;">${instructor.active_sessions_count}</div>
                    </div>
                    ` : ''}
                </div>

                <div class="instructor-card-meta">
                    ${lastLogin ? `Last login: ${lastLogin.toLocaleDateString()}` : 'Last login: Never'}
                </div>

                <div class="instructor-card-actions">
                    <button class="btn btn-secondary instructor-view-btn" style="flex: 1; min-height: 40px;">👁️ View</button>
                    ${instructor.is_active ? `
                    <button class="btn btn-secondary instructor-deactivate-btn" style="flex: 1; min-height: 40px;">🚫 Deactivate</button>
                    ` : `
                    <button class="btn btn-success instructor-activate-btn" style="flex: 1; min-height: 40px;">✅ Activate</button>
                    `}
                </div>
            </div>
        `;
    }).join('');

    // Add event listeners using event delegation
    grid.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.instructor-view-btn');
        const deactivateBtn = e.target.closest('.instructor-deactivate-btn');
        const activateBtn = e.target.closest('.instructor-activate-btn');
        
        const card = e.target.closest('.instructor-card');
        const instructorId = parseInt(card.getAttribute('data-instructor-id'));
        const instructor = instructors.find(i => i.id === instructorId);
        
        if (viewBtn) {
            viewInstructorDetail(instructorId);
        } else if (deactivateBtn) {
            deactivateInstructor(instructorId, instructor.display_name || instructor.username);
        } else if (activateBtn) {
            activateInstructor(instructorId, instructor.display_name || instructor.username);
        }
    });

    countEl.textContent = `${instructors.length} instructor${instructors.length !== 1 ? 's' : ''}`;
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

    // Classes list
    const classesContainer = document.getElementById('modal-classes-list');
    if (instructor.classes.length === 0) {
        classesContainer.innerHTML = `
            <div style="text-align: center; padding: 20px; color: #666;">
                No classes found
            </div>
        `;
    } else {
        classesContainer.innerHTML = instructor.classes.map(cls => {
            const classDate = new Date(cls.created_at);
            const archivedBadge = cls.is_archived
                ? '<span class="badge badge-ended" style="font-size: 0.75rem;">Archived</span>'
                : '<span class="badge badge-active" style="font-size: 0.75rem;">Active</span>';

            return `
                <div style="padding: 10px; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <div style="font-weight: 600;">${escapeHtml(cls.name)}</div>
                        <div>
                            ${archivedBadge}
                        </div>
                    </div>
                    <div style="font-size: 0.85rem; color: #666;">
                        Created: ${classDate.toLocaleDateString()} • ${cls.meeting_count} sessions
                    </div>
                </div>
            `;
        }).join('');
    }

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
