# Security Guide for RaiseMyHand

This document outlines the security features and best practices for deploying RaiseMyHand safely.

## Security Features

### 1. Admin Panel Authentication

The admin panel (`/admin`) is protected with HTTP Basic Authentication:

- **Environment Variables**:
  - `ADMIN_USERNAME`: Admin username (default: "admin")
  - `ADMIN_PASSWORD`: Admin password (default: "changeme123")

- **Protected Endpoints**:
  - `/admin` - Admin dashboard HTML
  - `/api/admin/stats` - System statistics
  - `/api/admin/sessions` - List all sessions
  - `/api/admin/sessions/{id}` - Delete session
  - `/api/admin/sessions/bulk/*` - Bulk operations

- **Authentication Method**: HTTP Basic Auth
- **Browser Behavior**: Browser will prompt for username/password

### 2. Instructor Code Security

Instructor codes have been enhanced for security:

- **Length**: Increased from 8 to 32 characters
- **Cryptographic Strength**: Uses `secrets.token_urlsafe()`
- **Guessing Difficulty**: 2^192 possible combinations (virtually impossible to guess)
- **Rate Limiting**: Applied to all instructor endpoints

### 3. Rate Limiting

Rate limiting prevents brute force attacks on instructor endpoints:

- **Get instructor session**: 30 requests/minute
- **End session**: 10 requests/minute
- **Restart session**: 10 requests/minute
- **Session reports**: 20 requests/minute
- **Library**: slowapi (Redis-like rate limiting for FastAPI)

### 4. Student Access

Student access remains simple and secure:
- **Session codes**: 32 characters, cryptographically random
- **No authentication**: Students only need the session code
- **WebSocket isolation**: Each session has isolated real-time communication

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required for production
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password

# Optional (has sensible defaults)
HOST=0.0.0.0
PORT=8000
BASE_URL=https://your-domain.com
TIMEZONE=America/New_York
DATABASE_URL=sqlite:///./raisemyhand.db
```

### Docker Configuration

Update `docker-compose.yml`:

```yaml
services:
  raisemyhand:
    environment:
      - ADMIN_USERNAME=your_admin_username
      - ADMIN_PASSWORD=your_secure_password
      - BASE_URL=https://your-domain.com
```

## Security Best Practices

### For Local Development

1. **Change default credentials**:
   ```bash
   export ADMIN_USERNAME=admin
   export ADMIN_PASSWORD=your_development_password
   ```

2. **Use localhost**:
   ```bash
   export BASE_URL=http://localhost:8000
   ```

### For Production Deployment

#### 1. Strong Admin Credentials
```bash
# Generate a strong password
openssl rand -base64 32

# Set strong credentials
ADMIN_USERNAME=admin_$(date +%s)
ADMIN_PASSWORD=generated_strong_password
```

#### 2. Network Security

**Option A: Firewall Protection**
```bash
# Only allow campus IPs to access admin panel
# Example nginx configuration:
location /admin {
    allow 192.168.1.0/24;    # Campus network
    allow 10.0.0.0/8;        # Internal network
    deny all;
    
    proxy_pass http://localhost:8000;
}
```

**Option B: VPN Access**
- Deploy behind campus VPN
- Admin panel only accessible when connected to VPN

**Option C: Reverse Proxy Authentication**
```nginx
# Add additional auth layer with nginx
location /admin {
    auth_basic "Admin Area";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}
```

#### 3. HTTPS Configuration

**Use Let's Encrypt**:
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d raisemyhand.university.edu

# Update BASE_URL
export BASE_URL=https://raisemyhand.university.edu
```

#### 4. Database Security

**For SQLite (default)**:
- File permissions: `chmod 600 raisemyhand.db`
- Backup encryption: `gpg -c raisemyhand.db`

**For PostgreSQL (production)**:
```bash
# Connection string with SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

## Security Levels

### Level 1: Basic (Local Development)
- ✅ Admin password changed from default
- ✅ localhost-only access
- ✅ Default rate limiting

### Level 2: Department (Shared Server)
- ✅ Strong admin credentials
- ✅ HTTPS enabled
- ✅ Firewall rules for admin panel
- ✅ Regular backups

### Level 3: Institutional (High Security)
- ✅ VPN-only admin access
- ✅ PostgreSQL with SSL
- ✅ Additional reverse proxy auth
- ✅ Audit logging
- ✅ Regular security updates

## Rate Limiting Details

Current limits (per IP address):

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `GET /api/instructor/sessions/{code}` | 30/min | Prevent code enumeration |
| `POST /api/sessions/{code}/end` | 10/min | Prevent session manipulation |
| `POST /api/sessions/{code}/restart` | 10/min | Prevent session manipulation |
| `GET /api/sessions/{code}/report` | 20/min | Prevent resource exhaustion |

### Customizing Rate Limits

Edit `main.py` to adjust limits:

```python
@limiter.limit("10/minute")  # Change to your preferred limit
def your_endpoint(request: Request, ...):
```

## Monitoring Security

### 1. Check for Unauthorized Access Attempts

Monitor server logs for:
- Multiple 401 responses (failed authentication)
- 429 responses (rate limiting triggered)
- Unusual patterns in instructor code requests

```bash
# Check for failed auth attempts
grep "401 Unauthorized" /var/log/raisemyhand.log

# Check for rate limiting
grep "429 Too Many Requests" /var/log/raisemyhand.log
```

### 2. Admin Panel Access Audit

Track admin panel access:
```bash
# Who accessed admin panel when
grep "GET /admin" /var/log/raisemyhand.log
```

### 3. Session Code Security

Monitor for potential attacks:
```bash
# Look for rapid instructor endpoint requests
grep "api/instructor/sessions" /var/log/raisemyhand.log | grep -c "$(date +%Y-%m-%d)"
```

## Upgrading Security

### From No Auth to Basic Auth

Already implemented! Just set environment variables.

### From Basic Auth to OAuth/SSO

Future enhancement options:
1. **Google OAuth**: For Gmail-based institutions
2. **SAML/LDAP**: For enterprise identity providers
3. **GitHub OAuth**: For technical institutions
4. **Custom JWT**: For existing user databases

### From SQLite to PostgreSQL

1. **Install PostgreSQL**:
   ```bash
   sudo apt install postgresql
   ```

2. **Update environment**:
   ```bash
   export DATABASE_URL=postgresql://user:pass@localhost/raisemyhand
   ```

3. **Install driver**:
   ```bash
   pip install psycopg2-binary
   ```

## Common Security Questions

### Q: Are instructor codes secure enough?
A: Yes. 32-character codes have 2^192 possible combinations. Even at 1 billion guesses per second, it would take longer than the age of the universe to guess one.

### Q: Can students access other sessions?
A: No. Students need the exact session code, and codes are cryptographically random with no predictable pattern.

### Q: What if someone finds an instructor code?
A: Instructors can end their session immediately, making the code useless. The system is designed for temporary access.

### Q: Is the admin panel secure enough for production?
A: Yes, with proper deployment:
- Strong password (not "changeme123")
- HTTPS enabled
- Firewall or VPN protection
- Regular password rotation

### Q: Should we add user accounts for instructors?
A: Not necessary for most use cases. The current session-code system provides good security with zero friction. Consider accounts only if you need:
- Usage analytics per instructor
- Institutional policy compliance
- Session ownership tracking

## Security Changelog

### v1.0.0 (Current)
- ✅ Admin HTTP Basic Authentication
- ✅ 32-character instructor codes
- ✅ Rate limiting on instructor endpoints
- ✅ Cryptographic session code generation
- ✅ WebSocket connection isolation

### Future Enhancements
- 🔄 OAuth/SSO integration
- 🔄 Audit logging
- 🔄 Session password protection (optional)
- 🔄 IP-based access controls
- 🔄 Multi-factor authentication for admin

## Support

For security-related questions:
1. Check this documentation first
2. Review deployment guides in `DEPLOYMENT.md`
3. Check server logs for specific error messages
4. Open an issue on GitHub (do not include sensitive information)

---

**⚠️ Security Notice**: Always change default credentials before deploying to production!