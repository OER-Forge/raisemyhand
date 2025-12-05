# Issue #31a: Authentication Hardening

**Priority: HIGH** | **Labels: security, enhancement, authentication**  
**Milestone: Pre-Production Security**  
**Estimated Effort: 3-5 days**

## Description

Implement advanced authentication security features required before production deployment. This includes two-factor authentication, password policies, session management, and brute force protection.

---

## Motivation

Current authentication system uses basic JWT tokens with password hashing, but lacks critical security features expected in production systems:
- No multi-factor authentication for privileged accounts
- No password expiration or rotation policies
- Unlimited login attempts allow brute force attacks
- Session tokens never expire (30-day fixed duration)

**Risk**: Admin accounts are high-value targets. A compromised admin account can access all instructor data, classes, and meetings.

---

## Features

### 1. Two-Factor Authentication (2FA/TOTP)

**User Story**: As an admin, I want to enable 2FA so unauthorized users cannot access my account even if they know my password.

**Requirements**:
- [ ] TOTP-based 2FA using authenticator apps (Google Authenticator, Authy, etc.)
- [ ] QR code generation for easy setup
- [ ] 6-digit time-based codes with 30-second validity window
- [ ] 8 backup codes for account recovery (one-time use)
- [ ] Admin-enforced 2FA for ADMIN and SUPER_ADMIN roles
- [ ] Grace period: 7 days to enable 2FA after role elevation
- [ ] Optional 2FA for INSTRUCTOR role (user choice)

**Implementation**:
```python
# Database changes
class Instructor(Base):
    twofa_secret = Column(String, nullable=True)  # Base32 encoded TOTP secret
    twofa_enabled = Column(Boolean, default=False, index=True)
    twofa_backup_codes = Column(JSON, nullable=True)  # List of hashed backup codes
    twofa_enabled_at = Column(DateTime, nullable=True)
    twofa_enforce_deadline = Column(DateTime, nullable=True)  # For grace period
    
# API endpoints
POST /api/instructors/2fa/setup
  → Returns: QR code image, secret key, backup codes
  
POST /api/instructors/2fa/enable
  Body: {"code": "123456"}
  → Verifies code and enables 2FA
  
POST /api/instructors/2fa/disable
  Body: {"password": "...", "code": "123456"}
  → Requires password AND current 2FA code
  
POST /api/instructors/2fa/verify
  Body: {"code": "123456"} OR {"backup_code": "12345678"}
  → Called during login after password verification
  
POST /api/instructors/2fa/regenerate-backup-codes
  Body: {"code": "123456"}
  → Generates new backup codes, invalidates old ones

# Login flow changes
1. POST /api/instructors/login → Returns {"requires_2fa": true, "temp_token": "..."}
2. POST /api/instructors/2fa/verify → Returns final JWT token
```

**Dependencies**:
- `pyotp==2.9.0` - TOTP implementation
- `qrcode[pil]==7.4.2` - QR code generation
- `pillow==10.1.0` - Image processing

**UI Changes**:
- Settings page: "Enable 2FA" section with QR code display
- Login page: 2FA code input after password (if enabled)
- Admin dashboard: Warning banner for users with 2FA enforcement deadline

---

### 2. Password Expiration Policies

**User Story**: As a security administrator, I want to enforce password rotation so compromised passwords have limited validity.

**Requirements**:
- [ ] Configurable password expiration (default: 90 days)
- [ ] Warning notifications 7 days before expiration
- [ ] Force password change on first login (for admin-created accounts)
- [ ] Password history tracking (prevent reuse of last 5 passwords)
- [ ] Minimum password age: 1 day (prevent rapid rotation)
- [ ] Password strength requirements: min 12 chars, 1 uppercase, 1 lowercase, 1 number, 1 special

**Implementation**:
```python
# Database changes
class Instructor(Base):
    password_changed_at = Column(DateTime, nullable=True, index=True)
    password_expires_at = Column(DateTime, nullable=True, index=True)
    password_history = Column(JSON, nullable=True)  # List of last 5 hashed passwords
    force_password_change = Column(Boolean, default=False, index=True)
    password_change_token = Column(String, nullable=True)  # For forced resets

class SystemConfig(Base):  # Extend existing model
    password_expiration_days = Column(Integer, default=90)
    password_min_length = Column(Integer, default=12)
    password_require_uppercase = Column(Boolean, default=True)
    password_require_lowercase = Column(Boolean, default=True)
    password_require_number = Column(Boolean, default=True)
    password_require_special = Column(Boolean, default=True)
    password_history_count = Column(Integer, default=5)
    password_min_age_days = Column(Integer, default=1)

# API endpoints
POST /api/instructors/change-password
  Body: {"current_password": "...", "new_password": "...", "code_2fa": "123456"}
  → Validates: current password, password strength, password history, min age
  
POST /api/instructors/force-password-change
  Body: {"token": "...", "new_password": "..."}
  → Used for forced password changes (first login, admin reset)
  
GET /api/admin/password-policy
  → Returns current password policy configuration
  
PUT /api/admin/password-policy
  Body: {"password_expiration_days": 60, ...}
  → Updates password policy (SUPER_ADMIN only)

# Background job
async def check_password_expiration():
    """Daily job to check for expiring passwords and send notifications"""
    # Find passwords expiring in 7 days
    # Send email notifications
    # Mark accounts with force_password_change=True if expired
```

**Dependencies**:
- `zxcvbn==4.4.28` (optional) - Password strength estimation

**UI Changes**:
- Password change modal with strength meter
- Dashboard banner: "Your password expires in X days"
- Admin page: Password policy configuration form
- Login page: Force password change flow

---

### 3. Session Management

**User Story**: As a user, I want my session to expire after inactivity so my account is protected if I leave my computer unattended.

**Requirements**:
- [ ] Configurable session timeout (default: 30 minutes inactivity)
- [ ] Activity tracking: update `last_activity` on each API request
- [ ] "Remember me" option for 30-day tokens (desktop only)
- [ ] Automatic token refresh for active sessions
- [ ] Manual "Logout all devices" functionality
- [ ] Admin ability to revoke all sessions for a user

**Implementation**:
```python
# Database changes
class SessionToken(Base):
    """Replace in-memory JWT with tracked sessions"""
    __tablename__ = "session_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)  # SHA256 hash of JWT
    device_name = Column(String, nullable=True)  # From User-Agent parsing
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_activity = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    remember_me = Column(Boolean, default=False)
    revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    
    instructor = relationship("Instructor")

class SystemConfig(Base):  # Extend
    session_timeout_minutes = Column(Integer, default=30)
    remember_me_enabled = Column(Boolean, default=True)
    remember_me_duration_days = Column(Integer, default=30)

# API endpoints
GET /api/instructors/sessions
  → Returns list of active sessions (current device highlighted)
  
DELETE /api/instructors/sessions/{session_id}
  → Revoke a specific session
  
DELETE /api/instructors/sessions/all
  → Revoke all sessions except current
  
POST /api/instructors/refresh-token
  → Refresh JWT token if session is active

# Middleware changes
async def verify_session_token(token: str):
    """Check if token is valid and session is not expired/revoked"""
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.query(SessionToken).filter_by(token_hash=token_hash).first()
    
    if not session or session.revoked:
        raise HTTPException(401, "Session revoked")
    
    # Check session timeout
    timeout = timedelta(minutes=config.session_timeout_minutes)
    if datetime.utcnow() - session.last_activity > timeout:
        session.revoked = True
        db.commit()
        raise HTTPException(401, "Session expired")
    
    # Update activity
    session.last_activity = datetime.utcnow()
    db.commit()
    
    return session.instructor_id
```

**UI Changes**:
- Settings page: "Active Sessions" list with device info
- Login page: "Remember me" checkbox
- Auto-logout modal: "Your session will expire in 2 minutes. Extend session?"

---

### 4. Brute Force Protection

**User Story**: As the system, I want to prevent brute force attacks by limiting login attempts and adding friction after failures.

**Requirements**:
- [ ] Track failed login attempts per username
- [ ] Account lockout after 5 failed attempts (15-minute duration)
- [ ] Exponential backoff: 1st fail = no delay, 3rd fail = CAPTCHA, 5th fail = lockout
- [ ] CAPTCHA challenge after 3 failed attempts
- [ ] Email notification on account lockout
- [ ] Admin ability to unlock accounts
- [ ] Clear counters on successful login

**Implementation**:
```python
# Database changes
class Instructor(Base):
    failed_login_attempts = Column(Integer, default=0, index=True)
    locked_until = Column(DateTime, nullable=True, index=True)
    last_failed_login = Column(DateTime, nullable=True)
    last_failed_login_ip = Column(String, nullable=True)
    lockout_count = Column(Integer, default=0)  # How many times locked out

class SystemConfig(Base):  # Extend
    max_login_attempts = Column(Integer, default=5)
    lockout_duration_minutes = Column(Integer, default=15)
    captcha_after_attempts = Column(Integer, default=3)
    lockout_email_notifications = Column(Boolean, default=True)

# API endpoints
POST /api/instructors/login
  Body: {"username": "...", "password": "...", "captcha_token": "..."}
  → Returns: 429 if locked, 401 with captcha_required=true after 3 fails
  
POST /api/admin/security/unlock-account/{instructor_id}
  Body: {"reason": "User verified via phone"}
  → Resets failed attempts and clears lockout

# Login flow
async def handle_login(username: str, password: str, captcha_token: str = None):
    instructor = get_instructor_by_username(username)
    
    if not instructor:
        await asyncio.sleep(2)  # Constant-time response
        raise HTTPException(401, "Invalid credentials")
    
    # Check if locked
    if instructor.locked_until and datetime.utcnow() < instructor.locked_until:
        raise HTTPException(429, f"Account locked until {instructor.locked_until}")
    
    # Check if CAPTCHA required
    if instructor.failed_login_attempts >= config.captcha_after_attempts:
        if not captcha_token or not verify_captcha(captcha_token):
            raise HTTPException(401, {"message": "CAPTCHA required", "captcha_required": True})
    
    # Verify password
    if not verify_password(password, instructor.password_hash):
        instructor.failed_login_attempts += 1
        instructor.last_failed_login = datetime.utcnow()
        instructor.last_failed_login_ip = request.client.host
        
        # Lock account if threshold reached
        if instructor.failed_login_attempts >= config.max_login_attempts:
            instructor.locked_until = datetime.utcnow() + timedelta(minutes=config.lockout_duration_minutes)
            instructor.lockout_count += 1
            db.commit()
            
            # Send email notification
            if config.lockout_email_notifications:
                await send_lockout_email(instructor)
            
            raise HTTPException(429, "Account locked due to repeated failed logins")
        
        db.commit()
        raise HTTPException(401, "Invalid credentials")
    
    # Successful login - reset counters
    instructor.failed_login_attempts = 0
    instructor.locked_until = None
    instructor.last_login = datetime.utcnow()
    db.commit()
    
    return create_access_token({"sub": instructor.id})
```

**Dependencies**:
- `hcaptcha==0.1.0` or `google-recaptcha==1.1.0` - CAPTCHA verification

**UI Changes**:
- Login page: CAPTCHA widget after 3 fails
- Login page: Error message with unlock time
- Admin page: "Unlock Account" button on user detail page

---

## Database Migration

```python
"""Add authentication hardening fields

Revision ID: auth_hardening_v1
Revises: previous_migration
Create Date: 2025-12-05
"""

def upgrade():
    # Add 2FA fields
    op.add_column('instructors', sa.Column('twofa_secret', sa.String(), nullable=True))
    op.add_column('instructors', sa.Column('twofa_enabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('instructors', sa.Column('twofa_backup_codes', sa.JSON(), nullable=True))
    op.add_column('instructors', sa.Column('twofa_enabled_at', sa.DateTime(), nullable=True))
    op.add_column('instructors', sa.Column('twofa_enforce_deadline', sa.DateTime(), nullable=True))
    
    # Add password policy fields
    op.add_column('instructors', sa.Column('password_changed_at', sa.DateTime(), nullable=True))
    op.add_column('instructors', sa.Column('password_expires_at', sa.DateTime(), nullable=True))
    op.add_column('instructors', sa.Column('password_history', sa.JSON(), nullable=True))
    op.add_column('instructors', sa.Column('force_password_change', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('instructors', sa.Column('password_change_token', sa.String(), nullable=True))
    
    # Add brute force protection fields
    op.add_column('instructors', sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False))
    op.add_column('instructors', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.add_column('instructors', sa.Column('last_failed_login', sa.DateTime(), nullable=True))
    op.add_column('instructors', sa.Column('last_failed_login_ip', sa.String(), nullable=True))
    op.add_column('instructors', sa.Column('lockout_count', sa.Integer(), server_default='0', nullable=False))
    
    # Create session_tokens table
    op.create_table('session_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instructor_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('device_name', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('remember_me', sa.Boolean(), nullable=False),
        sa.Column('revoked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instructor_id'], ['instructors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_session_tokens_token_hash', 'session_tokens', ['token_hash'], unique=True)
    op.create_index('ix_session_tokens_instructor_id', 'session_tokens', ['instructor_id'])
    op.create_index('ix_session_tokens_expires_at', 'session_tokens', ['expires_at'])
    
    # Add SystemConfig password policy fields
    op.add_column('system_config', sa.Column('password_expiration_days', sa.Integer(), server_default='90', nullable=False))
    op.add_column('system_config', sa.Column('password_min_length', sa.Integer(), server_default='12', nullable=False))
    op.add_column('system_config', sa.Column('password_require_uppercase', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('system_config', sa.Column('password_require_lowercase', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('system_config', sa.Column('password_require_number', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('system_config', sa.Column('password_require_special', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('system_config', sa.Column('password_history_count', sa.Integer(), server_default='5', nullable=False))
    op.add_column('system_config', sa.Column('password_min_age_days', sa.Integer(), server_default='1', nullable=False))
    op.add_column('system_config', sa.Column('session_timeout_minutes', sa.Integer(), server_default='30', nullable=False))
    op.add_column('system_config', sa.Column('remember_me_enabled', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('system_config', sa.Column('remember_me_duration_days', sa.Integer(), server_default='30', nullable=False))
    op.add_column('system_config', sa.Column('max_login_attempts', sa.Integer(), server_default='5', nullable=False))
    op.add_column('system_config', sa.Column('lockout_duration_minutes', sa.Integer(), server_default='15', nullable=False))
    op.add_column('system_config', sa.Column('captcha_after_attempts', sa.Integer(), server_default='3', nullable=False))
    op.add_column('system_config', sa.Column('lockout_email_notifications', sa.Boolean(), server_default='true', nullable=False))

def downgrade():
    # Reverse all changes
    pass
```

---

## Testing Checklist

### Unit Tests
- [ ] TOTP generation and validation
- [ ] Backup code generation and one-time use
- [ ] Password strength validation
- [ ] Password history checking
- [ ] Session expiration logic
- [ ] Brute force lockout thresholds

### Integration Tests
- [ ] 2FA enrollment flow end-to-end
- [ ] 2FA login with valid/invalid codes
- [ ] Password change with strength validation
- [ ] Forced password change flow
- [ ] Session timeout after inactivity
- [ ] "Remember me" token persistence
- [ ] Failed login attempt tracking
- [ ] Account lockout and unlock
- [ ] CAPTCHA challenge trigger

### Security Tests
- [ ] 2FA bypass attempts (without code)
- [ ] Password reuse prevention
- [ ] Session token tampering
- [ ] Brute force attack simulation
- [ ] CAPTCHA bypass attempts
- [ ] Token expiration enforcement

### Manual Testing
- [ ] 2FA setup with Google Authenticator
- [ ] QR code scanning
- [ ] Backup code usage
- [ ] Password expiration notification
- [ ] Session timeout warning modal
- [ ] Account lockout email notification
- [ ] Admin unlock account workflow

---

## Security Considerations

1. **TOTP Secret Storage**: Secrets are stored encrypted at rest (application-level encryption)
2. **Backup Codes**: Hashed with bcrypt before storage, never displayed after initial generation
3. **Password History**: Store only hashes, never plain text
4. **Session Tokens**: Hash tokens before storage, never store raw JWT in database
5. **Timing Attacks**: Use constant-time comparisons for password/code verification
6. **Rate Limiting**: Apply rate limits to all authentication endpoints (5 requests/minute)
7. **Audit Logging**: Log all authentication events to SecurityLog table

---

## Documentation Updates

- [ ] Update `/docs/AUTHENTICATION.md` with 2FA setup guide
- [ ] Add password policy documentation for administrators
- [ ] Update API documentation with new endpoints
- [ ] Create user guide for 2FA enrollment
- [ ] Add troubleshooting guide for locked accounts

---

## Rollout Plan

1. **Phase 1**: Deploy with all features disabled (flag-gated)
2. **Phase 2**: Enable password policies (non-breaking)
3. **Phase 3**: Enable session management (users will be logged out once)
4. **Phase 4**: Enable brute force protection
5. **Phase 5**: Enable 2FA (optional for all users)
6. **Phase 6**: Enforce 2FA for ADMIN/SUPER_ADMIN roles (7-day grace period)

---

## Related Issues

- Issue #31: Original security features umbrella issue
- Issue #31b: Security monitoring (will log events from this issue)
- Issue #31c: Compliance features (integrates with password policies)

---

## Success Metrics

- [ ] 90%+ adoption of 2FA among admin users within 30 days
- [ ] Zero successful brute force attacks in logs
- [ ] <1% of users locked out due to false positives
- [ ] Average session duration aligns with expected usage patterns
- [ ] Password reuse rate drops to 0%
