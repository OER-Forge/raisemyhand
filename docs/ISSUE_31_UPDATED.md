# Issue #31 - UPDATED

## [PHASE 9] Security Features - Status Update & Refactoring

### 🎉 Completed Features (as of 2025-12-05)

The following features from the original Issue #31 have been **successfully implemented**:

#### ✅ Multi-level Admin Roles
- RBAC system with roles: INSTRUCTOR, ADMIN, SUPER_ADMIN, INACTIVE
- Permission-based feature access via role hierarchy
- Audit trails with `role_granted_by`, `deactivated_by` tracking
- See: `models_v2.py`, `RBAC_IMPLEMENTATION_PLAN.md`

#### ✅ Admin User Management
- Comprehensive instructor management system
- Account creation/deactivation workflows
- API key management and revocation
- See: `routes_admin_users.py`, commit 199d1f2

#### ✅ Password Security
- Bcrypt password hashing
- Password visibility toggles in UI
- Secure password reset flows
- See: `security.py`, commit 98c77bc

#### ✅ JWT Authentication
- Unified JWT/API key authentication system
- 30-day token expiration
- Secure token generation and validation
- See: `security.py`, `routes_instructor.py`

#### ✅ Rate Limiting (Basic)
- SlowAPI integration for rate limiting
- Configuration flag: `settings.rate_limit_enabled`
- WebSocket rate limiting tests
- See: `main.py`, `config.py`

#### ✅ System Configuration Controls
- Admin registration toggle
- SystemConfig database model
- Runtime configuration management
- See: commit 08ed82a

---

### 🔄 Remaining Work - Split into 3 New Issues

The original Issue #31 was too broad. The remaining security features have been divided into three focused issues:

---

## 📋 Issue #31a: Authentication Hardening
**Priority: HIGH** | **Label: security, enhancement**

Advanced authentication features required before production deployment.

### Features:
1. **Two-Factor Authentication (2FA/TOTP)**
   - Add `twofa_secret` field to Instructor model
   - Implement TOTP generation/validation (pyotp library)
   - QR code generation for authenticator apps
   - Backup codes for account recovery
   - Admin-enforced 2FA for ADMIN/SUPER_ADMIN roles

2. **Password Expiration Policies**
   - Add `password_changed_at`, `password_expires_at` to Instructor
   - Configurable expiration duration (default: 90 days)
   - Force password change on first login
   - Password history tracking (prevent reuse of last 5 passwords)

3. **Session Management**
   - Configurable session timeout (default: 30 minutes inactivity)
   - Session refresh tokens for mobile apps
   - "Remember me" option with extended tokens (30 days)
   - Revoke all sessions endpoint

4. **Brute Force Protection**
   - Failed login attempt tracking (max 5 attempts)
   - Account lockout after threshold (15 minutes)
   - CAPTCHA after 3 failed attempts
   - Email notification on suspicious login attempts

### Database Changes:
```python
class Instructor(Base):
    # 2FA fields
    twofa_secret = Column(String, nullable=True)
    twofa_enabled = Column(Boolean, default=False)
    twofa_backup_codes = Column(JSON, nullable=True)
    
    # Password policy fields
    password_changed_at = Column(DateTime, nullable=True)
    password_expires_at = Column(DateTime, nullable=True)
    password_history = Column(JSON, nullable=True)  # List of hashed passwords
    force_password_change = Column(Boolean, default=False)
    
    # Account security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_failed_login = Column(DateTime, nullable=True)
```

### API Endpoints:
- `POST /api/instructors/setup-2fa` - Generate TOTP secret and QR code
- `POST /api/instructors/enable-2fa` - Verify and enable 2FA
- `POST /api/instructors/disable-2fa` - Disable 2FA (requires current code)
- `POST /api/instructors/verify-2fa` - Verify TOTP code during login
- `POST /api/instructors/change-password` - Force password change
- `POST /api/admin/security/unlock-account` - Admin unlock after lockout

### Dependencies:
- `pyotp` - TOTP generation/validation
- `qrcode[pil]` - QR code generation
- `pillow` - Image generation

### Testing:
- [ ] 2FA enrollment flow
- [ ] 2FA login verification
- [ ] Password expiration enforcement
- [ ] Brute force lockout mechanism
- [ ] Session timeout behavior

---

## 📋 Issue #31b: Security Monitoring & Audit
**Priority: MEDIUM** | **Label: security, monitoring**

Comprehensive security event tracking and alerting system.

### Features:
1. **Security Event Logging**
   - Centralized SecurityLog table for all security events
   - Event types: login, logout, failed_login, password_change, role_change, api_key_created, api_key_revoked
   - IP address, user agent, and geolocation tracking
   - Structured JSON metadata for each event

2. **Audit Trail System**
   - AuditLog table for administrative actions
   - Track all CRUD operations on instructors, classes, meetings
   - Before/after snapshots for data changes
   - Immutable audit records (append-only)

3. **Security Dashboard**
   - Real-time security events feed
   - Failed login attempts visualization
   - Suspicious activity alerts (e.g., multiple IPs for same account)
   - Active sessions viewer
   - Geographic login map

4. **Alerting System**
   - Email/webhook alerts for critical security events
   - Alert rules: repeated failed logins, new device login, role elevation
   - Admin notification preferences
   - Integration with external monitoring (optional: Sentry, Datadog)

5. **API Key Monitoring**
   - Detect compromised API keys (unusual usage patterns)
   - Alert on API key used from multiple IPs simultaneously
   - Automatic revocation on suspected compromise

### Database Changes:
```python
class SecurityLog(Base):
    __tablename__ = "security_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    event_type = Column(String, nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=True, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    success = Column(Boolean, nullable=False, index=True)
    metadata = Column(JSON, nullable=True)  # Event-specific data
    
    instructor = relationship("Instructor")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    actor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE, REVOKE
    resource_type = Column(String, nullable=False, index=True)  # instructor, class, api_key
    resource_id = Column(Integer, nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    
    actor = relationship("Instructor")
```

### API Endpoints:
- `GET /api/admin/security/events` - List security events (filterable)
- `GET /api/admin/security/audit` - List audit trail
- `GET /api/admin/security/failed-logins` - Failed login report
- `GET /api/admin/security/active-sessions` - Active sessions
- `POST /api/admin/security/revoke-sessions` - Revoke all sessions for user
- `GET /api/admin/security/alerts` - List active alerts
- `POST /api/admin/security/alerts/configure` - Configure alert rules

### Frontend:
- Security dashboard page (`/admin/security`)
- Real-time event stream (WebSocket)
- Charts: failed logins over time, login heatmap
- Audit log viewer with filters
- Alert configuration UI

### Dependencies:
- `python-geoip` or `geoip2` - IP geolocation
- `user-agents` - User agent parsing

### Testing:
- [ ] Security event creation on login/logout
- [ ] Audit log creation on admin actions
- [ ] Failed login detection and alerting
- [ ] API key anomaly detection
- [ ] Dashboard displays real-time events

---

## 📋 Issue #31c: Compliance & Data Privacy
**Priority: MEDIUM-LOW** | **Label: compliance, privacy, enhancement**

GDPR/FERPA compliance features and data management tools.

### Features:
1. **Data Export**
   - Instructors can export all their data (classes, meetings, questions, answers)
   - JSON and CSV export formats
   - Automatic anonymization of student data
   - Scheduled automated backups (admin-configurable)

2. **Account Deletion with Retention**
   - Soft delete with configurable retention period (default: 90 days)
   - Hard delete after retention period
   - Data anonymization option (replace PII with placeholders)
   - Cascade deletion confirmation workflow

3. **Data Access Audit**
   - Track all data access by instructors
   - "Who viewed my data" log for transparency
   - Data access reports for compliance officers
   - GDPR Article 15 compliance (right to access)

4. **Privacy Controls**
   - Student data anonymization utilities
   - PII scrubbing for analytics
   - Data retention policy configuration
   - Cookie consent banner (if web-facing)

5. **IP Whitelisting (Optional)**
   - Configurable IP whitelist for admin panel
   - CIDR range support
   - Bypass for specific instructor accounts
   - Audit log for blocked access attempts

### Database Changes:
```python
class Instructor(Base):
    # Deletion tracking
    deletion_requested_at = Column(DateTime, nullable=True)
    deletion_scheduled_for = Column(DateTime, nullable=True)
    deletion_reason = Column(Text, nullable=True)
    anonymized = Column(Boolean, default=False)

class DataAccessLog(Base):
    __tablename__ = "data_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    accessor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False, index=True)
    resource_type = Column(String, nullable=False)  # class, meeting, question
    resource_id = Column(Integer, nullable=False)
    access_type = Column(String, nullable=False)  # read, export, delete
    ip_address = Column(String, nullable=True)
    
    accessor = relationship("Instructor")

class SystemConfig(Base):  # Add to existing model
    # Privacy settings
    data_retention_days = Column(Integer, default=90)
    allow_data_export = Column(Boolean, default=True)
    ip_whitelist = Column(JSON, nullable=True)  # List of allowed IPs/CIDRs
    cookie_consent_required = Column(Boolean, default=False)
```

### API Endpoints:
- `POST /api/instructors/export-data` - Request data export
- `GET /api/instructors/export-data/{export_id}` - Download export
- `POST /api/instructors/delete-account` - Request account deletion
- `POST /api/instructors/cancel-deletion` - Cancel pending deletion
- `GET /api/instructors/access-log` - View data access history
- `POST /api/admin/compliance/anonymize/{instructor_id}` - Anonymize user data
- `POST /api/admin/compliance/hard-delete/{instructor_id}` - Permanent deletion
- `GET /api/admin/compliance/retention-policy` - Get retention settings
- `PUT /api/admin/compliance/retention-policy` - Update retention settings
- `POST /api/admin/security/ip-whitelist` - Configure IP whitelist

### Privacy Documentation:
- Privacy policy template
- GDPR compliance checklist
- FERPA compliance documentation
- Data processing agreement template
- Student data handling guidelines

### Dependencies:
- `ipaddress` (built-in) - IP whitelist validation
- `pandas` (optional) - CSV export generation

### Testing:
- [ ] Data export generates complete dataset
- [ ] Account deletion workflow
- [ ] Data anonymization preserves functionality
- [ ] IP whitelist blocks unauthorized access
- [ ] Retention policy auto-deletes old accounts

---

## 🎯 Implementation Order Recommendation

1. **First: Issue #31a (Authentication Hardening)** - Critical for production security
2. **Second: Issue #31b (Security Monitoring)** - Enables detection and response
3. **Third: Issue #31c (Compliance)** - Required for institutional deployment

---

## 📚 Related Documentation

- `RBAC_IMPLEMENTATION_PLAN.md` - Completed RBAC architecture
- `ADMIN_INSTRUCTOR_MANAGEMENT_PLAN.md` - Admin system design
- `security.py` - Current authentication implementation
- `models_v2.py` - Current database schema

---

## 🔗 Original Issue Reference

Original Issue #31 opened by @dannycab on 2025-12-04
- Title: [PHASE 9] Implement admin security features and compliance controls
- Status: Open → Superseded by #31a, #31b, #31c
- Label: `priority: future` → Update to `status: split`
