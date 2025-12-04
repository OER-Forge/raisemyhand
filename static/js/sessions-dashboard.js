// Sessions Dashboard JavaScript - View all meetings for an API key (v2 API)
// NOTE: Uses shared.js for authentication utilities

let allMeetings = [];
let filterClassId = null;
let currentDateRange = 'all';
let currentViewMode = 'flat';

// Check authentication on load
function checkAuth() {
    const apiKey = getApiKey();

    // Check for class_id filter in URL
    const urlParams = new URLSearchParams(window.location.search);
    filterClassId = urlParams.get('class_id');

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
    const avgQuestions = allMeetings.length > 0 ? Math.round(totalQuestions / allMeetings.length * 10) / 10 : 0;

    document.getElementById('total-sessions').textContent = allMeetings.length;
    document.getElementById('active-sessions').textContent = activeMeetings.length;
    document.getElementById('total-questions').textContent = totalQuestions;
    document.getElementById('avg-questions').textContent = avgQuestions;
}

// Filter meetings
function filterSessions() {
    const filter = document.querySelector('input[name="status-filter"]:checked').value;
    const searchTerm = document.getElementById('search-sessions')?.value.toLowerCase() || '';
    const sortBy = document.getElementById('sort-sessions')?.value || 'created-newest';
    renderMeetings(filter, searchTerm, sortBy, currentDateRange);
}

// Set date range filter
function setDateRange(days) {
    currentDateRange = days;
    
    // Update button styling
    document.querySelectorAll('.date-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-date-range="${days}"]`).classList.add('active');
    
    filterSessions();
}

// Set view mode (flat or by class)
function setViewMode(mode) {
    currentViewMode = mode;
    
    // Update button styling and accessibility
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        const isActive = btn.dataset.view === mode;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-pressed', isActive);
    });
    
    // Re-render with new view mode
    filterSessions();
}

// Render meetings (v2 API)
function renderMeetings(filter = 'all', searchTerm = '', sortBy = 'created-newest', dateRange = 'all') {
    const container = document.getElementById('sessions-list');
    const emptyState = document.getElementById('empty-state');

    let meetingsToShow = allMeetings;

    // Filter by class_id if provided in URL
    if (filterClassId) {
        meetingsToShow = meetingsToShow.filter(m => m.class_id === parseInt(filterClassId));
        // Show class filter info
        const pageTitle = document.querySelector('header h1');
        if (pageTitle && !pageTitle.dataset.filtered) {
            const className = meetingsToShow.length > 0 ? (meetingsToShow[0].class_name || `Class ${filterClassId}`) : `Class ${filterClassId}`;
            pageTitle.innerHTML = `Meetings for: ${escapeHtml(className)} <a href="/sessions" style="font-size: 0.6em; margin-left: 10px; color: white; text-decoration: underline;">View All</a>`;
            pageTitle.dataset.filtered = 'true';
        }
    }

    // Filter by date range
    if (dateRange !== 'all') {
        const daysAgo = parseInt(dateRange);
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - daysAgo);
        
        meetingsToShow = meetingsToShow.filter(m => {
            const meetingDate = new Date(m.created_at);
            return meetingDate >= cutoffDate;
        });
    }

    // Filter by search term (title or meeting code)
    if (searchTerm) {
        meetingsToShow = meetingsToShow.filter(m => 
            m.title.toLowerCase().includes(searchTerm) || 
            m.meeting_code.toLowerCase().includes(searchTerm)
        );
    }

    // Filter by status
    if (filter === 'active') {
        meetingsToShow = meetingsToShow.filter(m => m.is_active);
    } else if (filter === 'ended') {
        meetingsToShow = meetingsToShow.filter(m => !m.is_active);
    }

    // Sort meetings
    if (sortBy === 'created-newest') {
        meetingsToShow.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (sortBy === 'created-oldest') {
        meetingsToShow.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    } else if (sortBy === 'questions-high') {
        meetingsToShow.sort((a, b) => (b.question_count || 0) - (a.question_count || 0));
    } else if (sortBy === 'questions-low') {
        meetingsToShow.sort((a, b) => (a.question_count || 0) - (b.question_count || 0));
    } else if (sortBy === 'updated-newest') {
        meetingsToShow.sort((a, b) => new Date(b.ended_at || b.created_at) - new Date(a.ended_at || a.created_at));
    }

    if (meetingsToShow.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        if (filterClassId) {
            emptyState.innerHTML = `
                <div class="empty-state-icon">📅</div>
                <h2>No meetings for this class</h2>
                <p>Create a meeting from the class page.</p>
                <a href="/classes" class="btn btn-primary">Back to Classes</a>
            `;
        }
        return;
    }

    container.style.display = currentViewMode === 'flat' ? 'grid' : 'block';
    emptyState.style.display = 'none';

    // Render based on view mode
    if (currentViewMode === 'class') {
        renderByClass(meetingsToShow, container);
    } else {
        renderFlat(meetingsToShow, container);
    }
}

// Render meetings as flat list
function renderFlat(meetingsToShow, container) {
    container.innerHTML = meetingsToShow.map(meeting => renderMeetingCard(meeting)).join('');
}

// Render meetings grouped by class
function renderByClass(meetingsToShow, container) {
    // Group meetings by class
    const groupedByClass = {};
    meetingsToShow.forEach(meeting => {
        const classId = meeting.class_id;
        if (!groupedByClass[classId]) {
            groupedByClass[classId] = {
                class_id: classId,
                class_name: meeting.class_name || `Class ${classId}`,
                meetings: []
            };
        }
        groupedByClass[classId].meetings.push(meeting);
    });

    // Sort classes by name
    const sortedClasses = Object.values(groupedByClass).sort((a, b) => 
        a.class_name.localeCompare(b.class_name)
    );

    // Render class groups
    let html = '';
    sortedClasses.forEach(classGroup => {
        const classId = `class-group-${classGroup.class_id}`;
        html += `
            <div class="class-group">
                <button 
                    class="class-group-header" 
                    aria-expanded="true" 
                    aria-controls="${classId}-content"
                    onclick="toggleClassGroup(this)"
                >
                    <h2 class="class-group-title">
                        <span class="class-group-toggle" aria-hidden="true">▼</span>
                        📚 ${escapeHtml(classGroup.class_name)}
                    </h2>
                    <div class="class-group-info">
                        <span>${classGroup.meetings.length} meeting${classGroup.meetings.length !== 1 ? 's' : ''}</span>
                    </div>
                </button>
                <div id="${classId}-content" class="class-group-content" role="region">
                    ${classGroup.meetings.map(meeting => renderMeetingCard(meeting)).join('')}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Toggle class group expansion
function toggleClassGroup(button) {
    const isExpanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', !isExpanded);
    
    const contentId = button.getAttribute('aria-controls');
    const content = document.getElementById(contentId);
    
    if (isExpanded) {
        content.hidden = true;
    } else {
        content.hidden = false;
    }
}

// Render single meeting card
function renderMeetingCard(meeting) {
    return `
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
                    <span class="session-stat-label">Class</span>
                    <span class="session-stat-value">${meeting.class_name || `Class ${meeting.class_id}`}</span>
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
    `;
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
async function openCreateSessionModal() {
    console.log('openCreateSessionModal called');
    const modal = document.getElementById('create-session-modal');
    if (!modal) {
        console.error('Modal element not found!');
        alert('Error: Modal element not found. Please refresh the page.');
        return;
    }
    console.log('Modal found, opening...');

    // Load classes for the dropdown
    await loadClassesForDropdown();

    modal.classList.add('active');
    document.getElementById('session-title').value = '';
    document.getElementById('session-password').value = '';
    document.getElementById('session-title').focus();
}

// Load classes into the dropdown
async function loadClassesForDropdown() {
    try {
        const apiKey = getApiKey();
        const response = await fetch(`/api/classes?api_key=${apiKey}`);

        if (!response.ok) {
            throw new Error('Failed to load classes');
        }

        const classes = await response.json();
        const select = document.getElementById('session-class');

        // Clear existing options
        select.innerHTML = '';

        if (classes.length === 0) {
            select.innerHTML = '<option value="">No classes found - create one first</option>';
            return;
        }

        // Add classes to dropdown
        classes.forEach(cls => {
            if (!cls.is_archived) {
                const option = document.createElement('option');
                option.value = cls.id;
                option.textContent = cls.name;
                select.appendChild(option);
            }
        });

        // Add "Create new class" option
        const newClassOption = document.createElement('option');
        newClassOption.value = 'new';
        newClassOption.textContent = '+ Create New Class';
        select.appendChild(newClassOption);

    } catch (error) {
        console.error('Error loading classes:', error);
        const select = document.getElementById('session-class');
        select.innerHTML = '<option value="">Error loading classes</option>';
    }
}

function closeCreateSessionModal() {
    const modal = document.getElementById('create-session-modal');
    modal.classList.remove('active');
}

// Create a new session (v2 API)
async function createSession(event) {
    event.preventDefault();

    const classSelect = document.getElementById('session-class');
    const selectedClassId = classSelect.value;
    const title = document.getElementById('session-title').value.trim();
    const password = document.getElementById('session-password').value;
    const apiKey = getApiKey();

    if (!selectedClassId) {
        showNotification('Please select a class', 'error');
        return;
    }

    if (!title) {
        showNotification('Please enter a session name', 'error');
        return;
    }

    // If user selected "Create new class", redirect to classes page
    if (selectedClassId === 'new') {
        if (confirm('You need to create a class first. Redirect to Classes page?')) {
            window.location.href = '/classes';
        }
        return;
    }

    try {
        // Create the meeting in the selected class
        const payload = { title: title };
        if (password) {
            payload.password = password;
        }

        const response = await fetch(`/api/classes/${selectedClassId}/meetings?api_key=${encodeURIComponent(apiKey)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            showNotification('Invalid API key', 'error');
            clearApiKey();
            setTimeout(() => window.location.href = '/instructor-login', 2000);
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
