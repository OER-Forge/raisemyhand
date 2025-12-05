// Classes Dashboard JavaScript - Manage instructor classes (v2 API)

let allClasses = [];
let currentEditClassId = null;
let showArchived = false;

// Check authentication on load
function checkAuth() {
    console.log('Checking authentication...');
    const jwtToken = getJwtToken();
    const apiKey = getApiKey();
    console.log('JWT token:', jwtToken ? jwtToken.substring(0, 20) + '...' : 'None');
    console.log('API key:', apiKey ? apiKey.substring(0, 10) + '...' : 'None');

    if (!isAuthenticated()) {
        console.error('No authentication found - redirecting to login');
        showNotification('Please log in to view your classes.', 'error');
        setTimeout(() => {
            window.location.href = '/instructor-login';
        }, 1500);
        return;
    }
    console.log('Authentication found, loading classes...');
    loadClasses();
}

// Load all classes for authenticated user (v2 API)
async function loadClasses() {
    try {
        // Always load ALL classes including archived to get accurate stats
        const response = await authenticatedFetch('/api/classes?include_archived=true');

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to load classes');
        }

        allClasses = await response.json();
        updateStats();
        renderClasses();
    } catch (error) {
        console.error('Error loading classes:', error);
        showNotification('Failed to load classes', 'error');
    }
}

// Update statistics
function updateStats() {
    const activeClasses = allClasses.filter(c => !c.is_archived);
    const archivedClasses = allClasses.filter(c => c.is_archived);
    const totalMeetings = allClasses.reduce((sum, c) => sum + (c.meeting_count || 0), 0);

    document.getElementById('total-classes').textContent = allClasses.length;
    document.getElementById('active-classes').textContent = activeClasses.length;
    document.getElementById('total-meetings').textContent = totalMeetings;

    // Update archived count
    const archivedCountEl = document.getElementById('archived-classes');
    if (archivedCountEl) {
        archivedCountEl.textContent = archivedClasses.length;
    }
}

// Toggle archived classes visibility
function toggleArchivedClasses() {
    showArchived = !showArchived;
    const toggleBtn = document.getElementById('toggle-archived-btn');
    if (toggleBtn) {
        toggleBtn.textContent = showArchived ? 'Hide Archived' : 'Show Archived';
    }
    renderClasses();
}

// Render classes
function renderClasses() {
    const container = document.getElementById('classes-list');
    const emptyState = document.getElementById('empty-state');

    const activeClasses = allClasses.filter(c => !c.is_archived);
    const archivedClasses = allClasses.filter(c => c.is_archived);
    const displayClasses = showArchived ? allClasses : activeClasses;

    if (displayClasses.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        emptyState.innerHTML = showArchived
            ? '<p>No classes found (including archived).</p>'
            : '<p>No active classes. <button onclick="toggleArchivedClasses()" class="btn btn-secondary">Show Archived</button></p>';
        return;
    }

    container.style.display = 'grid';
    emptyState.style.display = 'none';

    // Separate archived classes if showing both
    let html = '';

    if (showArchived && activeClasses.length > 0) {
        html += '<div style="grid-column: 1/-1; padding: 20px; background: #e3f2fd; border-radius: 8px; margin-bottom: 20px;">';
        html += '<h2 style="margin: 0; font-size: 1.5rem;">Active Classes</h2>';
        html += '</div>';
        html += renderClassCards(activeClasses, false);
    }

    if (showArchived && archivedClasses.length > 0) {
        html += '<div style="grid-column: 1/-1; padding: 20px; background: #fff3e0; border-radius: 8px; margin: 20px 0;">';
        html += '<h2 style="margin: 0; font-size: 1.5rem;">Archived Classes</h2>';
        html += '<p style="margin: 5px 0 0 0; color: #666;">These classes are hidden by default. Meetings remain accessible.</p>';
        html += '</div>';
        html += renderClassCards(archivedClasses, true);
    }

    if (!showArchived) {
        html = renderClassCards(activeClasses, false);
    }

    container.innerHTML = html;
}

// Render class cards helper
function renderClassCards(classes, isArchived) {
    return classes.map(cls => `
        <div class="class-card" style="${cls.is_archived ? 'opacity: 0.7; border: 2px solid #ff9800;' : ''}">
            <div class="class-header">
                <div>
                    <h3 class="class-title">${escapeHtml(cls.name)}</h3>
                    <span class="badge ${cls.is_archived ? 'badge-archived' : 'badge-active'}">
                        ${cls.is_archived ? '📦 Archived' : '✅ Active'}
                    </span>
                </div>
            </div>

            ${cls.description ? `<div class="class-description">${escapeHtml(cls.description)}</div>` : ''}

            <div class="class-meta">
                <span>📅 Created ${formatDate(cls.created_at)}</span>
                ${cls.is_archived ? '<br><span style="color: #ff9800;">⚠️ This class is archived but meetings are still accessible</span>' : ''}
            </div>

            <div class="class-stats">
                <div class="class-stat">
                    <span class="class-stat-label">Meetings</span>
                    <span class="class-stat-value">${cls.meeting_count || 0}</span>
                </div>
                <div class="class-stat">
                    <span class="class-stat-label">Class ID</span>
                    <span class="class-stat-value">${cls.id}</span>
                </div>
            </div>

            <div class="class-actions">
                <button onclick="viewClassMeetings(${cls.id})" class="btn btn-primary">
                    View Meetings
                </button>
                ${!cls.is_archived ? `
                    <button onclick="openEditClassModal(${cls.id})" class="btn btn-secondary">
                        Edit
                    </button>
                    <button onclick="archiveClass(${cls.id})" class="btn" style="background: #ff9800; color: white;">
                        Archive
                    </button>
                ` : `
                    <button onclick="unarchiveClass(${cls.id})" class="btn" style="background: #4caf50; color: white;">
                        Unarchive
                    </button>
                `}
            </div>
        </div>
    `).join('');
}

// Modal functions
function openCreateClassModal() {
    currentEditClassId = null;
    document.getElementById('class-modal-title').textContent = 'Create New Class';
    document.getElementById('class-id').value = '';
    document.getElementById('class-name').value = '';
    document.getElementById('class-description').value = '';

    const modal = document.getElementById('class-modal');
    modal.classList.add('active');
    document.getElementById('class-name').focus();
}

function openEditClassModal(classId) {
    const cls = allClasses.find(c => c.id === classId);
    if (!cls) return;

    currentEditClassId = classId;
    document.getElementById('class-modal-title').textContent = 'Edit Class';
    document.getElementById('class-id').value = classId;
    document.getElementById('class-name').value = cls.name;
    document.getElementById('class-description').value = cls.description || '';

    const modal = document.getElementById('class-modal');
    modal.classList.add('active');
    document.getElementById('class-name').focus();
}

function closeClassModal() {
    const modal = document.getElementById('class-modal');
    modal.classList.remove('active');
    currentEditClassId = null;
}

// Save class (create or update)
async function saveClass(event) {
    event.preventDefault();

    const classId = document.getElementById('class-id').value;
    const name = document.getElementById('class-name').value.trim();
    const description = document.getElementById('class-description').value.trim();

    if (!name) {
        showNotification('Please enter a class name', 'error');
        return;
    }

    try {
        const payload = { name, description };
        let response;

        if (classId) {
            // Update existing class
            response = await authenticatedFetch(`/api/classes/${classId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            // Create new class
            response = await authenticatedFetch('/api/classes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Failed to save class', 'error');
            return;
        }

        showNotification(classId ? 'Class updated successfully' : 'Class created successfully', 'success');
        closeClassModal();
        loadClasses(); // Reload to update

    } catch (error) {
        console.error('Error saving class:', error);
        showNotification('Failed to save class. Please try again.', 'error');
    }
}

// Archive a class
async function archiveClass(classId) {
    if (!confirm('Are you sure you want to archive this class? The class will be hidden but meetings will remain accessible. You can unarchive it later.')) {
        return;
    }

    try {
        const response = await authenticatedFetch(`/api/classes/${classId}`, {
            method: 'DELETE'
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to archive class');
        }

        showNotification('Class archived successfully. Use "Show Archived" to restore it.', 'success');
        loadClasses(); // Reload to update
    } catch (error) {
        console.error('Error archiving class:', error);
        showNotification('Failed to archive class', 'error');
    }
}

// Unarchive a class
async function unarchiveClass(classId) {
    if (!confirm('Restore this class from the archive?')) {
        return;
    }

    try {
        const response = await authenticatedFetch(`/api/classes/${classId}/unarchive`, {
            method: 'POST'
        });

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to unarchive class');
        }

        showNotification('Class restored successfully!', 'success');
        loadClasses(); // Reload to update
    } catch (error) {
        console.error('Error unarchiving class:', error);
        showNotification(error.message || 'Failed to unarchive class', 'error');
    }
}

// View meetings for a specific class
function viewClassMeetings(classId) {
    // Redirect to sessions page with class filter
    window.location.href = `/sessions?class_id=${classId}`;
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

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('class-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeClassModal();
            }
        });
    }
});

// Auto-refresh every 30 seconds
setInterval(loadClasses, 30000);

// Initialize on page load
checkAuth();
