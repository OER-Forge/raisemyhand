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

        if (!isAuthenticated()) {
            console.warn('[Profile] No authentication found, redirecting to login');
            window.location.href = '/instructor-login';
            return;
        }

        const response = await authenticatedFetch('/api/instructors/profile');

        console.log('[Profile] API response status:', response.status);

        if (response.status === 401) {
            console.error('[Profile] 401 Unauthorized');
            handleAuthError();
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

        if (!isAuthenticated()) {
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

        const response = await authenticatedFetch('/api/instructors/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            handleAuthError();
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
 * Load and display API key information
 */
async function loadApiKeys() {
    try {
        console.log('[Profile] loadApiKeys() called');

        if (!isAuthenticated()) {
            return;
        }

        const response = await authenticatedFetch('/api/instructors/api-keys');

        if (response.status === 401) {
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to load API keys');
        }

        const apiKeys = await response.json();

        // Get the first API key (instructors should have only one)
        const apiKey = apiKeys.length > 0 ? apiKeys[0] : null;

        const apiKeyContainer = document.getElementById('apiKeyContainer');
        const apiKeyLoading = document.getElementById('apiKeyLoading');

        if (apiKey) {
            // Show the API key info
            const maskedKey = apiKey.key_masked || apiKey.key_preview || '****';
            document.getElementById('apiKeyDisplay').textContent = maskedKey;
            document.getElementById('apiKeyCreatedDate').textContent = formatDateTime(apiKey.created_at) || '—';
            document.getElementById('apiKeyLastUsed').textContent = apiKey.last_used
                ? formatDateTime(apiKey.last_used)
                : 'Never';

            // Store the key ID for later use
            window.currentApiKeyId = apiKey.id;

            apiKeyContainer.style.display = 'block';
            apiKeyLoading.style.display = 'none';
        } else {
            // No API key found
            apiKeyLoading.innerHTML = '<p style="color: #dc3545;">No API key found. Please contact an administrator.</p>';
            apiKeyLoading.style.display = 'block';
        }

    } catch (error) {
        console.error('[Profile] Error loading API keys:', error);
        document.getElementById('apiKeyLoading').innerHTML = '<p style="color: #dc3545;">Failed to load API key information</p>';
    }
}

/**
 * Toggle API key reveal interface
 */
function toggleApiKeyReveal() {
    const passwordGroup = document.getElementById('passwordConfirmGroup');
    const revealBtn = document.getElementById('revealApiKeyBtn');
    const confirmBtn = document.getElementById('confirmRevealBtn');
    const copyBtn = document.getElementById('copyApiKeyBtn');
    const cancelBtn = document.getElementById('cancelRevealBtn');
    const revealPassword = document.getElementById('revealPassword');

    // Check if already revealed (button says "Hide")
    if (revealBtn.textContent.includes('Hide')) {
        // Hide the key
        cancelApiKeyReveal();
        return;
    }

    // Show password input
    passwordGroup.style.display = 'block';
    revealBtn.style.display = 'none';
    confirmBtn.style.display = 'inline-block';
    copyBtn.style.display = 'none';
    cancelBtn.style.display = 'inline-block';
    revealPassword.focus();
}

/**
 * Reveal full API key with password confirmation
 */
async function revealApiKey() {
    try {
        const password = document.getElementById('revealPassword').value;

        if (!password) {
            showNotification('Please enter your password', 'error');
            return;
        }

        const response = await authenticatedFetch(`/api/instructors/api-keys/${window.currentApiKeyId}/reveal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password: password })
        });

        if (response.status === 401) {
            if (response.headers.get('content-type')?.includes('application/json')) {
                const error = await response.json();
                if (error.detail === 'Invalid password') {
                    showNotification('Invalid password', 'error');
                    return;
                }
            }
            handleAuthError();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to reveal API key');
        }

        const apiKey = await response.json();

        // Display full key
        document.getElementById('apiKeyDisplay').textContent = apiKey.key;
        document.getElementById('apiKeyDisplay').style.userSelect = 'all';

        // Hide password input and show copy/cancel buttons
        document.getElementById('passwordConfirmGroup').style.display = 'none';
        document.getElementById('revealPassword').value = '';
        document.getElementById('revealApiKeyBtn').textContent = '🙈 Hide';
        document.getElementById('revealApiKeyBtn').style.display = 'inline-block';
        document.getElementById('confirmRevealBtn').style.display = 'none';
        document.getElementById('copyApiKeyBtn').style.display = 'inline-block';
        document.getElementById('cancelRevealBtn').style.display = 'inline-block';

        showNotification('API key revealed! Be careful with this sensitive information.', 'warning');

    } catch (error) {
        console.error('[Profile] Error revealing API key:', error);
        showNotification('Failed to reveal API key', 'error');
    }
}

/**
 * Cancel API key reveal
 */
function cancelApiKeyReveal() {
    const passwordGroup = document.getElementById('passwordConfirmGroup');
    const revealBtn = document.getElementById('revealApiKeyBtn');
    const confirmBtn = document.getElementById('confirmRevealBtn');
    const copyBtn = document.getElementById('copyApiKeyBtn');
    const cancelBtn = document.getElementById('cancelRevealBtn');
    const revealPassword = document.getElementById('revealPassword');

    // Restore masked key
    loadApiKeys();

    // Reset UI
    passwordGroup.style.display = 'none';
    revealPassword.value = '';
    revealBtn.textContent = '👁️ Reveal';
    revealBtn.style.display = 'inline-block';
    confirmBtn.style.display = 'none';
    copyBtn.style.display = 'none';
    cancelBtn.style.display = 'none';
}

/**
 * Copy API key to clipboard
 */
function copyApiKey() {
    const keyText = document.getElementById('apiKeyDisplay').textContent;

    navigator.clipboard.writeText(keyText).then(() => {
        showNotification('API key copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback
        const textArea = document.createElement('textarea');
        textArea.value = keyText;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('API key copied to clipboard!', 'success');
    });
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
        loadApiKeys();

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
