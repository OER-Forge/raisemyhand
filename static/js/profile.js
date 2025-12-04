/**
 * Instructor Profile Management
 * Handles loading, editing, and updating instructor profile information
 */

console.log('[PROFILE.JS] Script loaded');

let originalData = {};

/**
 * Load profile data from API
 */
async function loadProfile() {
    try {
        console.log('[Profile] loadProfile() called');
        const token = getJwtToken();
        console.log('[Profile] Token found:', !!token);
        
        if (!token) {
            console.warn('[Profile] No token found, redirecting to login');
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

        console.log('[Profile] API response status:', response.status);
        
        if (response.status === 401) {
            console.error('[Profile] 401 Unauthorized');
            clearJwtToken();
            window.location.href = '/instructor-login';
            return;
        }

        if (!response.ok) {
            throw new Error(`Failed to load profile: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('[Profile] Profile data received');
        populateProfile(data);
        originalData = JSON.parse(JSON.stringify(data));
    } catch (error) {
        console.error('[Profile] Error loading profile:', error);
        document.getElementById('error').textContent = 'Failed to load profile. Please refresh the page.';
        document.getElementById('error').style.display = 'block';
    }
}

/**
 * Populate form fields with profile data
 */
function populateProfile(data) {
    console.log('[Profile] populateProfile() called');
    document.getElementById('username').textContent = data.username || 'N/A';
    document.getElementById('email').value = data.email || '';
    document.getElementById('displayName').value = data.display_name || '';
    document.getElementById('memberSince').textContent = formatDateTime(data.created_at) || 'N/A';
    document.getElementById('lastLogin').textContent = formatDateTime(data.last_login) || 'Never';
    document.getElementById('accountStatus').textContent = data.is_active ? 'Active' : 'Inactive';
    
    document.getElementById('loading').style.display = 'none';
    document.getElementById('profileContainer').style.display = 'block';
}

/**
 * Save profile changes
 */
async function saveProfile() {
    try {
        console.log('[Profile] saveProfile() called');
        
        if (!validateForm()) {
            return;
        }

        const token = getJwtToken();
        if (!token) {
            window.location.href = '/instructor-login';
            return;
        }

        const payload = {
            email: document.getElementById('email').value.trim(),
            display_name: document.getElementById('displayName').value.trim()
        };

        // Only include password if user entered one
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        
        if (newPassword) {
            if (!currentPassword) {
                document.getElementById('error').textContent = 'Current password required to change password';
                document.getElementById('error').style.display = 'block';
                return;
            }
            payload.current_password = currentPassword;
            payload.new_password = newPassword;
        }

        const response = await fetch('/api/instructors/profile', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            clearJwtToken();
            window.location.href = '/instructor-login';
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            document.getElementById('error').textContent = error.detail || 'Failed to save profile';
            document.getElementById('error').style.display = 'block';
            return;
        }

        const updatedData = await response.json();
        originalData = JSON.parse(JSON.stringify(updatedData));
        
        document.getElementById('success').textContent = 'Profile updated successfully!';
        document.getElementById('success').style.display = 'block';
        
        // Clear password fields
        document.getElementById('currentPassword').value = '';
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmPassword').value = '';
        
        // Hide success message after 3 seconds
        setTimeout(() => {
            document.getElementById('success').style.display = 'none';
        }, 3000);
        
    } catch (error) {
        console.error('[Profile] Error saving profile:', error);
        document.getElementById('error').textContent = 'Error saving profile. Please try again.';
        document.getElementById('error').style.display = 'block';
    }
}

/**
 * Validate form inputs
 */
function validateForm() {
    const email = document.getElementById('email').value.trim();
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    document.getElementById('error').style.display = 'none';
    
    // Validate email
    if (email && !isValidEmail(email)) {
        document.getElementById('error').textContent = 'Please enter a valid email address';
        document.getElementById('error').style.display = 'block';
        return false;
    }
    
    // Validate passwords match
    if (newPassword && confirmPassword && newPassword !== confirmPassword) {
        document.getElementById('error').textContent = 'Passwords do not match';
        document.getElementById('error').style.display = 'block';
        return false;
    }
    
    // Validate password length
    if (newPassword && newPassword.length < 8) {
        document.getElementById('error').textContent = 'Password must be at least 8 characters long';
        document.getElementById('error').style.display = 'block';
        return false;
    }
    
    return true;
}

/**
 * Check if email is valid
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Reset form to original data
 */
function resetForm() {
    document.getElementById('email').value = originalData.email || '';
    document.getElementById('displayName').value = originalData.display_name || '';
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmPassword').value = '';
    document.getElementById('error').style.display = 'none';
    document.getElementById('success').style.display = 'none';
}

/**
 * Setup navigation menu
 */
function setupNavigationMenu() {
    console.log('[Profile] Setting up navigation menu');
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const navMenu = document.getElementById('nav-menu');
    const navOverlay = document.getElementById('nav-overlay');

    if (!hamburgerBtn) {
        console.warn('[Profile] No hamburger button found');
        return;
    }

    hamburgerBtn.addEventListener('click', () => {
        const isOpen = hamburgerBtn.getAttribute('aria-expanded') === 'true';
        hamburgerBtn.setAttribute('aria-expanded', !isOpen);
        navMenu.classList.toggle('open');
        navOverlay.classList.toggle('open');
    });

    if (navOverlay) {
        navOverlay.addEventListener('click', () => {
            hamburgerBtn.setAttribute('aria-expanded', 'false');
            navMenu.classList.remove('open');
            navOverlay.classList.remove('open');
        });
    }

    // Close menu when a link is clicked
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            hamburgerBtn.setAttribute('aria-expanded', 'false');
            navMenu.classList.remove('open');
            navOverlay.classList.remove('open');
        });
    });
}

/**
 * Initialize profile page
 */
function initProfile() {
    console.log('[Profile] Initializing profile page');
    
    try {
        setupNavigationMenu();
        loadProfile();
        
        // Setup form submission
        const form = document.getElementById('profileForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                saveProfile();
            });
        }
    } catch (error) {
        console.error('[Profile] Error initializing:', error);
        document.getElementById('error').textContent = 'Error loading page';
        document.getElementById('error').style.display = 'block';
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Profile] Page loaded');
    initProfile();
});
