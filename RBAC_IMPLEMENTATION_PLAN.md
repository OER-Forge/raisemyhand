# Role-Based Access Control (RBAC) Implementation Plan
## RaiseMyHand Admin → Instructor Hierarchy System
> on branch: admin-fixes

### Executive Summary

This plan outlines a comprehensive implementation of Role-Based Access Control (RBAC) that will transform the current binary admin/instructor system into a flexible, secure, hierarchical permission model. The implementation will maintain backward compatibility while introducing granular control over system access and operations.

---

## Current System Analysis

### Authentication Architecture
- **Admin Authentication**: Single hardcoded password (`ADMIN_PASSWORD`) + JWT tokens with `sub: "admin"`
- **Instructor Authentication**: Username/password + JWT tokens with `sub: instructor_id` + `type: "instructor"`
- **API Key System**: Admin-created keys tied to instructors, used for session management
- **Complete Separation**: No overlap between admin and instructor systems

### Current Models
```python
class Instructor(Base):
    id, username, email, display_name, password_hash
    created_at, last_login, is_active
    # Relationships: api_keys, classes, answers

class APIKey(Base):
    id, instructor_id, key, name
    created_at, last_used, is_active
    # Tied to instructor, used for class meetings
```

### Current Authorization Flow
1. **Admin**: `ADMIN_PASSWORD` → JWT with `sub: "admin"` → `verify_admin()` checks
2. **Instructor**: Username/password → JWT with `sub: instructor_id` → `get_current_instructor()` 
3. **API Key**: Admin creates → Instructor uses for sessions → `verify_api_key()`

### Critical Issues Identified
1. **API Key Ownership**: Instructors cannot create/manage their own API keys
2. **Binary Permissions**: No intermediate admin levels
3. **Cascade Deactivation**: No system for instructor deactivation affecting resources
4. **Admin Scalability**: Single admin account doesn't scale
5. **Audit Trail**: Limited tracking of admin actions by instructor identity

---

## Proposed RBAC System

### Core Design Principles
1. **Instructor-Centric**: All users are instructors with assigned roles
2. **Hierarchical Permissions**: Clear role inheritance and boundaries
3. **Self-Service**: Instructors manage their own API keys and resources
4. **Cascading Controls**: Deactivation properly cascades to dependent resources
5. **Audit Transparency**: Full traceability of actions to instructor identity

### Role Hierarchy

```
SUPER_ADMIN (Level 3)
├─ Full system control
├─ Manage all instructors and roles
├─ System configuration
├─ Emergency overrides
└─ Migration from current ADMIN_PASSWORD

ADMIN (Level 2)  
├─ Manage instructors in their domain
├─ Create/revoke instructor accounts
├─ View system analytics
├─ Manage API keys for others
└─ Cannot promote users to ADMIN or above

INSTRUCTOR (Level 1)
├─ Manage own classes and sessions
├─ Create/manage own API keys
├─ Access own analytics
└─ Standard teaching functionality

INACTIVE (Level 0)
├─ Read-only access to own historical data
├─ Cannot create new resources
└─ Cannot access live sessions
```

---

## Database Schema Changes

### 1. Enhanced Instructor Model

```python
class Instructor(Base):
    __tablename__ = "instructors"

    # Existing fields
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=True, index=True)
    display_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # NEW RBAC fields
    role = Column(Enum('INACTIVE', 'INSTRUCTOR', 'ADMIN', 'SUPER_ADMIN'), 
                  default='INSTRUCTOR', nullable=False, index=True)
    role_granted_by = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    role_granted_at = Column(DateTime, nullable=True)
    deactivated_by = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    deactivation_reason = Column(Text, nullable=True)
    
    # Self-referential relationships
    role_granter = relationship("Instructor", foreign_keys=[role_granted_by], remote_side=[id])
    deactivator = relationship("Instructor", foreign_keys=[deactivated_by], remote_side=[id])
    granted_roles = relationship("Instructor", foreign_keys=[role_granted_by], 
                                back_populates="role_granter")
    deactivated_users = relationship("Instructor", foreign_keys=[deactivated_by],
                                   back_populates="deactivator")
```

### 2. Enhanced API Key Model

```python
class APIKey(Base):
    __tablename__ = "api_keys"

    # Existing fields
    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="CASCADE"), 
                          nullable=False, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # NEW RBAC fields
    created_by = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    permissions = Column(JSON, nullable=True)  # For future granular permissions
    revoked_by = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Enhanced relationships
    creator = relationship("Instructor", foreign_keys=[created_by])
    revoker = relationship("Instructor", foreign_keys=[revoked_by])
```

### 3. New Audit Log Model

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False, index=True)
    target_id = Column(Integer, nullable=True, index=True)  # ID of affected resource
    target_type = Column(String, nullable=False, index=True)  # instructor, api_key, class, etc.
    action = Column(String, nullable=False, index=True)  # CREATE, UPDATE, DELETE, DEACTIVATE
    details = Column(JSON, nullable=True)  # Structured details about the action
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    actor = relationship("Instructor", foreign_keys=[actor_id])
```

---

## Authentication & Authorization Changes

### 1. Enhanced JWT Token Structure

```python
# Current Admin Token
{
    "sub": "admin",
    "exp": timestamp
}

# Current Instructor Token  
{
    "sub": "123",
    "username": "dannycab",
    "type": "instructor", 
    "exp": timestamp
}

# NEW Unified Token Structure
{
    "sub": "123",                    # instructor_id
    "username": "dannycab",
    "role": "ADMIN",                 # INSTRUCTOR, ADMIN, SUPER_ADMIN
    "permissions": ["manage_users"], # Future expansion
    "type": "instructor",            # Maintain backward compatibility
    "exp": timestamp
}
```

### 2. New Authorization Functions

```python
def verify_role(required_role: str):
    """Dependency factory for role-based authorization."""
    def _verify_role(current_user: Instructor = Depends(get_current_instructor)):
        role_hierarchy = {
            'INSTRUCTOR': 1,
            'ADMIN': 2, 
            'SUPER_ADMIN': 3
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(status_code=403, detail=f"{required_role} role required")
        
        return current_user
    return _verify_role

# Usage examples
@router.get("/admin/users")
def list_users(admin: Instructor = Depends(verify_role("ADMIN"))):
    pass

@router.post("/admin/promote")  
def promote_user(super_admin: Instructor = Depends(verify_role("SUPER_ADMIN"))):
    pass
```

### 3. Enhanced API Key Management

```python
class APIKeyService:
    @staticmethod
    def create_key_for_self(instructor: Instructor, name: str, db: DBSession) -> APIKey:
        """Instructors can create their own API keys."""
        
    @staticmethod 
    def create_key_for_other(creator: Instructor, target_instructor: Instructor, 
                           name: str, db: DBSession) -> APIKey:
        """Admins can create keys for other instructors."""
        if creator.role not in ['ADMIN', 'SUPER_ADMIN']:
            raise HTTPException(403, "Admin role required")
            
    @staticmethod
    def revoke_key(revoker: Instructor, key_id: int, reason: str, db: DBSession):
        """Revoke API key with audit trail."""
```

---

## Implementation Phases

### Phase 1: Database Migration & Core Models (Week 1)
- [ ] Add RBAC columns to instructor table
- [ ] Create audit_log table  
- [ ] Enhance api_keys table
- [ ] Write migration script for existing data
- [ ] Migrate current admin to SUPER_ADMIN instructor

### Phase 2: Enhanced Authentication (Week 2) 
- [ ] Update JWT token generation with role claims
- [ ] Implement new authorization decorators
- [ ] Update `get_current_instructor` to handle roles
- [ ] Create backward compatibility layer for existing tokens
- [ ] Test authentication flows

### Phase 3: API Key Self-Service (Week 2-3)
- [ ] Implement instructor API key creation endpoints
- [ ] Add API key management UI to instructor dashboard  
- [ ] Update admin API key management with enhanced controls
- [ ] Implement key revocation with audit trails
- [ ] Test API key workflows

### Phase 4: User Management & Admin Functions (Week 3-4)
- [ ] Implement role promotion/demotion endpoints
- [ ] Create instructor deactivation with cascade logic
- [ ] Build admin user management interface
- [ ] Implement bulk operations for admin efficiency
- [ ] Add comprehensive audit logging

### Phase 5: Cascading Deactivation (Week 4)
- [ ] Implement instructor deactivation cascade logic
- [ ] Classes → read-only when instructor deactivated
- [ ] Sessions → end active sessions, prevent new ones
- [ ] API Keys → revoke all keys for deactivated instructor
- [ ] Test deactivation scenarios

### Phase 6: Admin Interface & Analytics (Week 5)
- [ ] Enhanced admin dashboard with role management
- [ ] User analytics and activity monitoring
- [ ] Audit log viewer and export functionality
- [ ] System health and security monitoring
- [ ] Documentation and training materials

---

## API Endpoint Changes

### New Instructor Self-Service Endpoints
```python
# API Key Management
POST   /api/instructors/api-keys              # Create own API key
GET    /api/instructors/api-keys              # List own API keys  
DELETE /api/instructors/api-keys/{key_id}     # Revoke own API key
PUT    /api/instructors/api-keys/{key_id}     # Update key name/settings

# Profile & Settings
GET    /api/instructors/profile               # Enhanced with role info
PUT    /api/instructors/profile               # Update profile
GET    /api/instructors/activity              # Own activity log
```

### Enhanced Admin Endpoints
```python
# User Management (ADMIN+ role required)
GET    /api/admin/instructors                 # List all instructors
POST   /api/admin/instructors                 # Create instructor account
PUT    /api/admin/instructors/{id}/role       # Change user role
PUT    /api/admin/instructors/{id}/deactivate # Deactivate user
PUT    /api/admin/instructors/{id}/activate   # Reactivate user

# API Key Management (ADMIN+ role)  
POST   /api/admin/instructors/{id}/api-keys   # Create key for user
GET    /api/admin/api-keys                    # List all API keys
DELETE /api/admin/api-keys/{key_id}           # Revoke any key

# Audit & Monitoring (ADMIN+ role)
GET    /api/admin/audit-logs                  # System audit trail
GET    /api/admin/analytics                   # System analytics
GET    /api/admin/security-events             # Security monitoring
```

---

## Security Considerations

### Authentication Security
- **Token Claims**: Role included in JWT for efficient authorization
- **Token Validation**: Enhanced validation with role verification
- **Session Management**: Proper token invalidation on role changes
- **Backward Compatibility**: Graceful handling of old token formats

### Authorization Security  
- **Principle of Least Privilege**: Minimal required permissions by default
- **Role Boundaries**: Clear separation between role capabilities
- **Elevation Protection**: SUPER_ADMIN required for role promotions
- **Self-Service Limits**: Users can only manage their own resources

### Audit & Monitoring
- **Complete Audit Trail**: All administrative actions logged
- **Tamper Protection**: Audit logs immutable and cryptographically signed
- **Real-time Monitoring**: Security events trigger immediate alerts
- **Compliance Ready**: Structured logging for regulatory requirements

### Data Protection
- **Cascading Protection**: Deactivated users' data remains protected
- **Access Control**: Historical data accessible only to authorized users
- **Encryption**: Sensitive data encrypted at rest and in transit
- **Backup Security**: Role information included in backup/restore procedures

---

## Migration Strategy

### Data Migration
```sql
-- Phase 1: Add new columns with defaults
ALTER TABLE instructors ADD COLUMN role VARCHAR(20) DEFAULT 'INSTRUCTOR';
ALTER TABLE instructors ADD COLUMN role_granted_by INTEGER REFERENCES instructors(id);
-- ... other columns

-- Phase 2: Create super admin from existing admin
INSERT INTO instructors (username, email, display_name, password_hash, role, role_granted_at)
VALUES ('admin', 'admin@system.local', 'System Administrator', 
        '$2b$12$hash_of_admin_password', 'SUPER_ADMIN', NOW());

-- Phase 3: Update existing instructor API keys
UPDATE api_keys SET created_by = instructor_id WHERE created_by IS NULL;
```

### Backward Compatibility
- Existing JWT tokens remain valid during transition period
- Old admin endpoints redirected to new role-based equivalents  
- Legacy API key authentication preserved
- Graceful degradation for unsupported clients

### Rollback Plan
- Database migration scripts include rollback procedures
- Feature flags allow disabling new RBAC features
- Original admin authentication maintained as fallback
- Data preservation during rollback scenarios

---

## Testing Strategy

### Unit Testing
- [ ] Role assignment and verification logic
- [ ] JWT token generation and validation  
- [ ] API key creation and revocation
- [ ] Cascading deactivation logic
- [ ] Audit log creation and integrity

### Integration Testing
- [ ] End-to-end authentication flows
- [ ] Role-based authorization across all endpoints
- [ ] Admin user management workflows
- [ ] Instructor self-service functionality
- [ ] Security event logging and monitoring

### Security Testing
- [ ] Privilege escalation prevention
- [ ] Token tampering and forgery attempts
- [ ] Role boundary enforcement
- [ ] Audit log tampering detection
- [ ] Brute force and rate limiting

### Performance Testing
- [ ] Authentication/authorization overhead measurement
- [ ] Database query optimization for role checks
- [ ] Audit logging performance impact
- [ ] Large-scale user management operations
- [ ] API key validation performance

---

## Risk Assessment & Mitigation

### High-Risk Areas
1. **Migration Complexity**: Large schema changes with existing data
   - *Mitigation*: Extensive testing, staged rollout, rollback procedures

2. **Authentication Disruption**: Changes to core auth could break existing users
   - *Mitigation*: Backward compatibility, gradual migration, monitoring

3. **Performance Impact**: Additional role checks on every request  
   - *Mitigation*: Efficient caching, database optimization, performance testing

4. **Security Vulnerabilities**: New complexity could introduce attack vectors
   - *Mitigation*: Security reviews, penetration testing, audit logging

### Medium-Risk Areas
1. **User Experience**: Complex role system could confuse users
   - *Mitigation*: Clear documentation, gradual feature introduction, training

2. **Administrative Overhead**: More complex user management
   - *Mitigation*: Automated workflows, bulk operations, intuitive interfaces

### Low-Risk Areas
1. **Feature Scope Creep**: RBAC could expand beyond requirements
   - *Mitigation*: Clear requirements, phased implementation, regular reviews

---

## Success Metrics

### Functional Metrics
- [ ] 100% of existing functionality preserved during migration
- [ ] All instructor self-service features working within 2 weeks
- [ ] Admin user management completed within 4 weeks
- [ ] Zero authentication-related downtime during transition

### Security Metrics  
- [ ] Complete audit trail for all administrative actions
- [ ] Zero privilege escalation vulnerabilities
- [ ] 100% role boundary enforcement across all endpoints
- [ ] Real-time security event monitoring operational

### Performance Metrics
- [ ] Authentication latency impact < 10ms
- [ ] Role authorization overhead < 5ms per request
- [ ] Database query performance maintained within 95% of baseline
- [ ] API key validation performance unchanged

### User Experience Metrics
- [ ] Instructor satisfaction with self-service features > 90%
- [ ] Admin efficiency in user management improved by 50%
- [ ] Zero user confusion incidents related to role system
- [ ] Complete documentation and training materials delivered

---

## Conclusion

This comprehensive RBAC implementation will transform RaiseMyHand from a simple binary permission system into a robust, scalable, enterprise-ready platform. The phased approach ensures minimal disruption while delivering significant security and usability improvements.

The role-based hierarchy provides clear growth paths for the platform while maintaining strict security boundaries. Instructors gain autonomy over their resources while administrators retain comprehensive control capabilities.

Most importantly, the complete audit trail and cascading deactivation features ensure the platform meets enterprise security requirements while remaining intuitive for educational users.

**Estimated Timeline**: 5-6 weeks for complete implementation
**Risk Level**: Medium (well-mitigated with comprehensive testing)
**ROI**: High (significant security and scalability improvements)