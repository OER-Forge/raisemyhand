/**
 * Instructor Profile Management
 * Handles loading, editing, and updating instructor profile information
 */

let originalData = {};

/**
 * Setup navigation menu toggle for mobile
 */
function setupNavigationMenu() {
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const navMenu = document.getElementById('nav-menu');
    const navOverlay = document.getElementById('nav-overlay');

    if (!hamburgerBtn) return;

    hamburgerBtn.addEventListener('click', () => {
        const isOpen = hamburgerBtn.getAttribute('aria-expanded') === 'true';
        hamburgerBtn.setAttribute('aria-expanded', !isOpen);
        navMenu.classList.toggle('open');
        navOverlay.classList.toggle('open');
    });

    // Close menu when clicking on a link
    const navLinks = navMenu.querySelectorAll('a, button');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            hamburgerBtn.setAttribute('aria-expanded', 'false');
            navMenu.classList.remove('open');
            navOverlay.classList.remove('open');
        });
    });

    // Close menu when clicking on overlay
    navOverlay.addEventListener('click', () => {
        hamburgerBtn.setAttribute('aria-expanded', 'false');
        navMenu.classList.remove('open');
        navOverlay.classList.remove('open');
    });
}

/**
 * Load instructor profile from API
 */
async function loadProfile() {
    try {
        const token = localStorage.getItem('instructor_token');
        if (!token) {
            window.location.href = '/instructor-login';
            return;
        }

        const response = await fetch('/api/instructors/profile', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401) {
            localStorage.removeItem('instructor_token');
            window.location.href = '/instructor-login';
            return;
        }

        if (!response.ok) {
            throw new Error(`Failed to load profile: ${response.statusText}`);
        }

        const data = await response.json();
        populateProfile(data);
        originalData = JSON.parse(JSON.stringify(data));
    } catch (error) {
        console.error('Error loading profile:', error);
        showNotification('Failed to load profile. Please refresh the page.', 'error');
    }
}

/**
 * Populate form fields with profile data
 */
function populateProfile(data) {
    document.getElementById('username').textContent = data.username || 'N/A';
    document.getElementById('email').value = data.email || '';
    document.getElementById('displayName').value = data.display_name || '';
    document.getElementById('memberSince').textContent = formatDateTime(data.created_at);
    document.getElementById('lastLogin').textContent = data.last_login ? formatDateTime(data.last_login) : 'Never';
    document.getElementById('accountStatus').textContent = data.is_active ? 'Active' : 'Inactive';
}

/**
 * Validate form data before submission
 */
function validateForm() {
    const email = document.getElementById('email').value.trim();
    const displayName = document.getElementById('displayName').value.trim();
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (email && !emailRegex.test(email)) {
        showNotification('Please enter a valid email address', 'error');
        return false;
    }

    // Validate display name length
    if (displayName.length > 100) {
        showNotification('Display name must be 100 characters or less', 'error');
        return false;
    }

    // If changing password, validate requirements
    if (newPassword) {
        if (!currentPassword) {
            showNotification('Current password is required to change your password', 'error');
            return false;
        }

        if (newPassword.length < 8) {
            showNotification('New password must be at least 8 characters long', 'error');
            return false;
        }

        if (newPassword !== confirmPassword) {
            showNotification('Passwords do not match', 'error');
            return false;
        }

        if (newPassword === currentPassword) {
            showNotification('New password must be different from current password', 'error');
            return false;
        }
    }

    return true;
}

/**
 * Handle profile form submission
 */
document.getElementById('profileForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!validateForm()) {
        return;
    }

    const token = localStorage.getItem('instructor_token');
    if (!token) {
        window.location.href = '/instructor-login';
        return;
    }

    // Build update payload
    const payload = {
        email: document.getElementById('email').value.trim() || null,
        display_name: document.getElementById('displayName').value.trim() || null
    };

    const newPassword = document.getElementById('newPassword').value;
    const currentPassword = document.getElementById('currentPassword').value;

    if (newPassword) {
        payload.current_password = currentPassword;
        payload.new_password = newPassword;
    }

    try {
        showLoader(true);

        const response = await fetch('/api/instructors/profile', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            localStorage.removeItem('instructor_token');
            window.location.href = '/instructor-login';
            return;
        }

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Failed to update profile: ${response.statusText}`);
        }

        const updatedData = await response.json();
        populateProfile(updatedData);
        originalData = JSON.parse(JSON.stringify(updatedData));

        // Clear password fields
        document.getElementById('currentPassword').value = '';
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmPassword').value = '';

        showNotification('Profile updated successfully!', 'success');
    } catch (error) {
        console.error('Error updating profile:', error);
        showNotification(error.message || 'Failed to update profile. Please try again.', 'error');
    } finally {
        showLoader(false);
    }
});

/**
 * Reset form to original data
 */
function resetForm() {
    populateProfile(originalData);
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmPassword').value = '';
    showNotification('Changes discarded', 'success');
}

/**
 * Show/hide loader
 */
function showLoader(show) {
    const loader = document.getElementById('loader');
    const btn = document.getElementById('saveBtn');

    if (show) {
        loader.classList.add('show');
        btn.disabled = true;
    } else {
        loader.classList.remove('show');
        btn.disabled = false;
    }
}

/**
 * Show notification message
 */
function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification show ${type}`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
}

/**
 * Logout instructor
 */
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('instructor_token');
        window.location.href = '/instructor-login';
    }
}

/**
 * Initialize profile page
 */
function initProfile() {
    setupNavigationMenu();
    loadProfile();

    // Set up keyboard shortcut for save (Ctrl+S or Cmd+S)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            document.getElementById('profileForm').dispatchEvent(new Event('submit'));
        }
    });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initProfile);
