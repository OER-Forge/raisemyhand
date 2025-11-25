# Security Migration Guide

This guide helps you migrate from the previous version to the new security-enhanced version of RaiseMyHand.

## 🔒 What Changed?

We've implemented several critical security improvements:

1. **API Keys moved to Authorization headers** (instead of URL query parameters)
2. **Admin password now required** (no more hardcoded defaults)
3. **CSRF protection** for state-changing operations
4. **sessionStorage** instead of localStorage for API keys (better security)

---

## 📋 Migration Checklist

### For All Users

- [ ] Update `.env` file with required `ADMIN_PASSWORD`
- [ ] Update any scripts or API clients to use Authorization headers
- [ ] Test the new authentication flow

### For Docker Users

- [ ] Create `secrets/admin_password.txt` file
- [ ] Update `docker-compose.yml` if using custom configuration

### For Developers

- [ ] Review API client code for header-based authentication
- [ ] Update any automated scripts
- [ ] Test CSRF token handling

---

## 🔧 Step-by-Step Migration

### Step 1: Update Environment Variables

**REQUIRED:** Set admin password in `.env` file:

```bash
# OLD (insecure - no longer supported)
ADMIN_PASSWORD=changeme123

# NEW (required)
ADMIN_PASSWORD=your_strong_secure_password_here
```

⚠️ **IMPORTANT:** The application will **not start** without `ADMIN_PASSWORD` set!

**For Docker deployments:**

```bash
# Create password file
echo "your_secure_password" > secrets/admin_password.txt

# Or use environment variable
export ADMIN_PASSWORD=your_secure_password
```

---

### Step 2: Update API Client Code

#### Old Way (Deprecated):
```javascript
// API key in URL query parameter (INSECURE)
fetch(`/api/sessions?api_key=${apiKey}`)
```

#### New Way (Secure):
```javascript
// API key in Authorization header
fetch('/api/sessions', {
    headers: {
        'Authorization': `Bearer ${apiKey}`
    }
})
```

**Good news:** The old query parameter method still works (with deprecation warning) for backward compatibility, but will be removed in a future version.

---

### Step 3: Use the Shared JavaScript Utilities

If you're using the web interface, the changes are automatic! We've created `shared.js` with helper functions:

```javascript
// Automatically handles Authorization headers and CSRF tokens
const response = await authenticatedFetch('/api/sessions', {
    method: 'POST',
    body: JSON.stringify(sessionData)
});
```

All instructor pages now automatically:
- ✅ Use Authorization headers
- ✅ Include CSRF tokens for POST/PUT/DELETE requests
- ✅ Store API keys in sessionStorage (more secure)
- ✅ Handle token expiration

---

### Step 4: Update External Scripts

If you have scripts that create sessions programmatically:

#### Python Example:
```python
import requests

api_key = "your_api_key_here"

# OLD (deprecated)
response = requests.post(
    "http://localhost:8000/api/sessions?api_key=" + api_key,
    json={"title": "My Session"}
)

# NEW (recommended)
response = requests.post(
    "http://localhost:8000/api/sessions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"title": "My Session"}
)
```

#### cURL Example:
```bash
# OLD (deprecated)
curl -X POST "http://localhost:8000/api/sessions?api_key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Session"}'

# NEW (recommended)
curl -X POST "http://localhost:8000/api/sessions" \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Session"}'
```

---

### Step 5: CSRF Token Handling

For operations like ending/restarting sessions, you now need a CSRF token:

```javascript
// 1. Get CSRF token (handled automatically by authenticatedFetch)
const csrfResponse = await fetch('/api/csrf-token');
const { csrf_token } = await csrfResponse.json();

// 2. Include in POST/PUT/DELETE requests
const response = await fetch('/api/sessions/ABC123/end', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${apiKey}`,
        'X-CSRF-Token': csrf_token
    }
});
```

**Note:** If you use `authenticatedFetch()` from `shared.js`, CSRF tokens are handled automatically!

---

## 🐛 Troubleshooting

### Error: "ADMIN_PASSWORD environment variable must be set!"

**Solution:** Add `ADMIN_PASSWORD` to your `.env` file or create `secrets/admin_password.txt`

```bash
# Local development
echo "ADMIN_PASSWORD=your_password" >> .env

# Docker
echo "your_password" > secrets/admin_password.txt
```

---

### Error: "Invalid or missing CSRF token"

**Cause:** POST/PUT/DELETE requests to protected endpoints need CSRF tokens.

**Solution:**
1. Use `authenticatedFetch()` from `shared.js` (recommended)
2. Or manually fetch from `/api/csrf-token` and include in `X-CSRF-Token` header

---

### Error: "Invalid or inactive API key" (Status 401)

**Causes:**
1. API key not in Authorization header
2. Malformed Authorization header
3. Invalid/expired API key

**Solutions:**
```javascript
// ✅ Correct format
headers: { 'Authorization': 'Bearer YOUR_API_KEY' }

// ❌ Wrong formats
headers: { 'Authorization': 'YOUR_API_KEY' }  // Missing "Bearer"
headers: { 'X-API-Key': 'YOUR_API_KEY' }      // Wrong header name
```

---

### Warning: "API key in query parameter is deprecated"

**Cause:** You're using the old `?api_key=...` method.

**Action:** Update to use Authorization headers (see Step 2 above).

**Note:** Query parameter auth still works but will be removed in v2.0.

---

## 🔐 Security Best Practices

### API Key Storage

**Before (Insecure):**
```javascript
// localStorage is vulnerable to XSS attacks
localStorage.setItem('api_key', key);
```

**After (More Secure):**
```javascript
// sessionStorage is cleared when tab closes
sessionStorage.setItem('instructor_api_key', key);
```

**Best (Most Secure):**
Use httpOnly cookies (requires backend changes - on roadmap).

---

### Password Requirements

Set strong admin passwords:
- ✅ At least 12 characters
- ✅ Mix of letters, numbers, symbols
- ✅ Not a dictionary word
- ✅ Unique to this application

**Bad examples:**
- `admin`
- `password123`
- `changeme123`

**Good examples:**
- `mK9#xP2$vL4@qW8!`
- Generated password managers
- Long passphrases: `correct-horse-battery-staple-2024`

---

## 📊 Compatibility Matrix

| Feature | Old Version | New Version | Compatible? |
|---------|------------|-------------|-------------|
| Query param auth | ✅ Default | ⚠️ Deprecated | Yes (with warning) |
| Header auth | ❌ Not supported | ✅ Required | N/A |
| CSRF tokens | ❌ None | ✅ Required | Auto-handled |
| Default admin password | ✅ `changeme123` | ❌ Must set | No |
| localStorage | ✅ Used | ⚠️ Deprecated | Auto-migrated |
| sessionStorage | ❌ Not used | ✅ Default | N/A |

---

## 🚀 Rolling Back (If Needed)

If you need to temporarily roll back:

1. **Restore old code:**
   ```bash
   git checkout <previous-commit-hash>
   ```

2. **Or temporarily allow old auth:**
   ```python
   # In main.py, comment out the ADMIN_PASSWORD check
   # (NOT RECOMMENDED - security risk!)
   ```

---

## 📞 Getting Help

- **Issues:** https://github.com/your-repo/issues
- **Security concerns:** security@your-domain.com
- **Documentation:** Check README.md and other docs

---

## ✅ Testing Your Migration

Run this checklist to verify everything works:

### Web Interface Test:
1. [ ] Navigate to admin login
2. [ ] Login with new password
3. [ ] Create API key
4. [ ] Create session with API key
5. [ ] End session
6. [ ] View sessions dashboard

### API Test:
```bash
# Test 1: Get CSRF token
curl http://localhost:8000/api/csrf-token

# Test 2: Create session with headers
curl -X POST http://localhost:8000/api/sessions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session"}'

# Test 3: Verify old method shows warning (check server logs)
curl -X GET "http://localhost:8000/api/sessions/my-sessions?api_key=YOUR_KEY"
```

---

## 🎉 You're Done!

Your RaiseMyHand instance is now more secure! Key improvements:

- ✅ No hardcoded passwords
- ✅ API keys not exposed in URLs
- ✅ CSRF protection against cross-site attacks
- ✅ Better token storage practices

**Questions?** Check the main README.md or open an issue!
