// Classes Dashboard JavaScript - Manage instructor classes (v2 API)

let allClasses = [];
let currentEditClassId = null;

// Check authentication on load
function checkAuth() {
    const apiKey = getApiKey();
    if (!apiKey) {
        const key = prompt('Please enter your API key to view your classes:');
        if (key) {
            setApiKey(key);
            loadClasses();
        } else {
            alert('API key is required to view classes.');
            window.location.href = '/';
        }
    } else {
        loadClasses();
    }
}

// Load all classes for this API key (v2 API)
async function loadClasses() {
    try {
        const apiKey = getApiKey();
        const response = await fetch(`/api/classes?api_key=${apiKey}`);

        if (response.status === 401) {
            clearApiKey();
            showNotification('Invalid API key. Please log in again.', 'error');
            setTimeout(() => {
                checkAuth();
            }, 2000);
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
    const totalMeetings = allClasses.reduce((sum, c) => sum + (c.meeting_count || 0), 0);

    document.getElementById('total-classes').textContent = allClasses.length;
    document.getElementById('active-classes').textContent = activeClasses.length;
    document.getElementById('total-meetings').textContent = totalMeetings;
}

// Render classes
function renderClasses() {
    const container = document.getElementById('classes-list');
    const emptyState = document.getElementById('empty-state');

    const activeClasses = allClasses.filter(c => !c.is_archived);

    if (activeClasses.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    container.style.display = 'grid';
    emptyState.style.display = 'none';

    container.innerHTML = activeClasses.map(cls => `
        <div class="class-card">
            <div class="class-header">
                <div>
                    <h3 class="class-title">${escapeHtml(cls.name)}</h3>
                    <span class="badge ${cls.is_archived ? 'badge-archived' : 'badge-active'}">
                        ${cls.is_archived ? 'Archived' : 'Active'}
                    </span>
                </div>
            </div>

            ${cls.description ? `<div class="class-description">${escapeHtml(cls.description)}</div>` : ''}

            <div class="class-meta">
                <span>📅 Created ${formatDate(cls.created_at)}</span>
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
                <button onclick="openEditClassModal(${cls.id})" class="btn btn-secondary">
                    Edit
                </button>
                <button onclick="archiveClass(${cls.id})" class="btn" style="background: #f44336; color: white;">
                    Archive
                </button>
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
    const apiKey = getApiKey();

    if (!name) {
        showNotification('Please enter a class name', 'error');
        return;
    }

    try {
        const payload = { name, description };
        let response;

        if (classId) {
            // Update existing class
            response = await fetch(`/api/classes/${classId}?api_key=${apiKey}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            // Create new class
            response = await fetch(`/api/classes?api_key=${apiKey}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        if (response.status === 401) {
            clearApiKey();
            showNotification('Invalid API key', 'error');
            setTimeout(() => window.location.href = '/instructor-login', 2000);
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
    if (!confirm('Are you sure you want to archive this class? Meetings will remain accessible.')) {
        return;
    }

    try {
        const apiKey = getApiKey();
        const response = await fetch(`/api/classes/${classId}?api_key=${apiKey}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to archive class');
        }

        showNotification('Class archived successfully', 'success');
        loadClasses(); // Reload to update
    } catch (error) {
        console.error('Error archiving class:', error);
        showNotification('Failed to archive class', 'error');
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
