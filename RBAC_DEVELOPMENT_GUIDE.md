# RBAC Implementation Development Guide
## Phase-by-Phase Implementation and Testing Procedures

---

## Table of Contents

1. [Phase 1: Database Migration & Core Models](#phase-1-database-migration--core-models)
2. [Phase 2: Enhanced Authentication](#phase-2-enhanced-authentication)
3. [Phase 3: API Key Self-Service](#phase-3-api-key-self-service)
4. [Phase 4: User Management & Admin Functions](#phase-4-user-management--admin-functions)
5. [Phase 5: Cascading Deactivation](#phase-5-cascading-deactivation)
6. [Phase 6: Admin Interface & Analytics](#phase-6-admin-interface--analytics)
7. [Testing Framework](#testing-framework)
8. [Deployment & Rollback](#deployment--rollback)

---

## Phase 1: Database Migration & Core Models

**Duration**: 3-4 days
**Team Size**: 1-2 developers
**Risk Level**: High (schema modifications)

### 1.1 Objectives

- Add RBAC columns to instructor table without data loss
- Create new audit_log table for security tracking
- Enhance api_keys table with audit fields
- Migrate existing data safely
- Migrate current admin to SUPER_ADMIN instructor account

### 1.2 Implementation Steps

#### Step 1.2.1: Create Migration Script

**File**: `migrations/001_add_rbac_to_instructors.py`

```python
"""
Migration: Add RBAC fields to instructors table
- Adds role, role_granted_by, role_granted_at fields
- Adds deactivated_by, deactivated_at, deactivation_reason fields
- Creates foreign key self-references
- Sets defaults for existing data
"""

def upgrade():
    # Add RBAC columns
    op.add_column('instructors', sa.Column('role', sa.Enum('INACTIVE', 'INSTRUCTOR', 'ADMIN', 'SUPER_ADMIN'), 
                                           nullable=False, server_default='INSTRUCTOR'))
    op.add_column('instructors', sa.Column('role_granted_by', sa.Integer, 
                                          sa.ForeignKey('instructors.id'), nullable=True))
    op.add_column('instructors', sa.Column('role_granted_at', sa.DateTime, nullable=True))
    op.add_column('instructors', sa.Column('deactivated_by', sa.Integer,
                                          sa.ForeignKey('instructors.id'), nullable=True))
    op.add_column('instructors', sa.Column('deactivated_at', sa.DateTime, nullable=True))
    op.add_column('instructors', sa.Column('deactivation_reason', sa.Text, nullable=True))
    
    # Create indexes
    op.create_index('ix_instructors_role', 'instructors', ['role'])
    op.create_index('ix_instructors_is_active_role', 'instructors', ['is_active', 'role'])

def downgrade():
    op.drop_index('ix_instructors_is_active_role')
    op.drop_index('ix_instructors_role')
    op.drop_column('instructors', 'deactivation_reason')
    op.drop_column('instructors', 'deactivated_at')
    op.drop_column('instructors', 'deactivated_by')
    op.drop_column('instructors', 'role_granted_at')
    op.drop_column('instructors', 'role_granted_by')
    op.drop_column('instructors', 'role')
```

#### Step 1.2.2: Create Audit Log Table Migration

**File**: `migrations/002_create_audit_logs_table.py`

```python
"""
Migration: Create audit_logs table for comprehensive audit trail
- Tracks all administrative actions
- Immutable record of system changes
- Supports compliance and security monitoring
"""

def upgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('actor_id', sa.Integer, sa.ForeignKey('instructors.id'), nullable=False, index=True),
        sa.Column('target_id', sa.Integer, nullable=True, index=True),
        sa.Column('target_type', sa.String(50), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False, index=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, index=True),
    )
    
    # Create composite indexes for common queries
    op.create_index('ix_audit_logs_actor_created', 'audit_logs', ['actor_id', 'created_at'])
    op.create_index('ix_audit_logs_target_type', 'audit_logs', ['target_type', 'created_at'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action', 'created_at'])

def downgrade():
    op.drop_table('audit_logs')
```

#### Step 1.2.3: Enhance API Keys Table

**File**: `migrations/003_enhance_api_keys_table.py`

```python
"""
Migration: Add RBAC and audit fields to api_keys table
- created_by: Track who created the key
- permissions: JSON for future granular permissions
- revoked_by/revoked_at/revocation_reason: Revocation audit trail
"""

def upgrade():
    op.add_column('api_keys', sa.Column('created_by', sa.Integer,
                                       sa.ForeignKey('instructors.id'), nullable=True))
    op.add_column('api_keys', sa.Column('permissions', sa.JSON, nullable=True))
    op.add_column('api_keys', sa.Column('revoked_by', sa.Integer,
                                       sa.ForeignKey('instructors.id'), nullable=True))
    op.add_column('api_keys', sa.Column('revoked_at', sa.DateTime, nullable=True))
    op.add_column('api_keys', sa.Column('revocation_reason', sa.Text, nullable=True))
    
    # Set created_by to instructor_id for existing keys
    op.execute('UPDATE api_keys SET created_by = instructor_id WHERE created_by IS NULL')
    
    # Make created_by non-nullable after update
    op.alter_column('api_keys', 'created_by', existing_type=sa.Integer, nullable=False)
    
    op.create_index('ix_api_keys_created_by', 'api_keys', ['created_by'])
    op.create_index('ix_api_keys_revoked_at', 'api_keys', ['revoked_at'])

def downgrade():
    op.drop_index('ix_api_keys_revoked_at')
    op.drop_index('ix_api_keys_created_by')
    op.drop_column('api_keys', 'revocation_reason')
    op.drop_column('api_keys', 'revoked_at')
    op.drop_column('api_keys', 'revoked_by')
    op.drop_column('api_keys', 'permissions')
    op.drop_column('api_keys', 'created_by')
```

#### Step 1.2.4: Data Migration Script

**File**: `scripts/migrate_to_rbac.py`

```python
#!/usr/bin/env python3
"""
Data migration script for transitioning to RBAC system.
Run AFTER database migrations but BEFORE deploying new code.

Steps:
1. Create SUPER_ADMIN instructor from existing admin account
2. Verify all existing instructors have role set
3. Validate data integrity
4. Create audit log entries for migration
"""

import os
import sys
from datetime import datetime
from database import get_db, init_db
from models_v2 import Instructor
from models_config import SystemConfig
from security import get_password_hash
from logging_config import get_logger, log_security_event

logger = get_logger(__name__)

def migrate_to_rbac():
    """Execute RBAC migration"""
    
    db = next(get_db())
    
    print("\n" + "="*60)
    print("RBAC System Migration")
    print("="*60)
    
    # Step 1: Create SUPER_ADMIN instructor from admin account
    print("\n[1/4] Creating SUPER_ADMIN instructor account...")
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    if not admin_password:
        print("ERROR: ADMIN_PASSWORD not set. Cannot create admin instructor.")
        sys.exit(1)
    
    admin_instructor = db.query(Instructor).filter(
        Instructor.username == 'admin'
    ).first()
    
    if not admin_instructor:
        print("  Creating new admin instructor...")
        admin_instructor = Instructor(
            username='admin',
            email='admin@system.local',
            display_name='System Administrator',
            password_hash=get_password_hash(admin_password),
            role='SUPER_ADMIN',
            role_granted_at=datetime.utcnow(),
            is_active=True
        )
        db.add(admin_instructor)
        db.commit()
        print(f"  ✓ Created SUPER_ADMIN instructor (ID: {admin_instructor.id})")
    else:
        print("  Admin instructor already exists")
        if admin_instructor.role != 'SUPER_ADMIN':
            admin_instructor.role = 'SUPER_ADMIN'
            admin_instructor.role_granted_at = datetime.utcnow()
            db.commit()
            print(f"  ✓ Promoted to SUPER_ADMIN")
    
    # Step 2: Verify all instructors have role set
    print("\n[2/4] Verifying existing instructors...")
    instructors_without_role = db.query(Instructor).filter(
        Instructor.role == None
    ).count()
    
    if instructors_without_role > 0:
        print(f"  WARNING: {instructors_without_role} instructors without role")
        print("  Setting to default INSTRUCTOR role...")
        db.query(Instructor).filter(Instructor.role == None).update(
            {'role': 'INSTRUCTOR'},
            synchronize_session=False
        )
        db.commit()
    
    total_instructors = db.query(Instructor).count()
    print(f"  ✓ All {total_instructors} instructors have roles assigned")
    
    # Step 3: Verify API keys have created_by set
    print("\n[3/4] Verifying API keys...")
    from models_v2 import APIKey
    
    invalid_keys = db.query(APIKey).filter(APIKey.created_by == None).count()
    if invalid_keys > 0:
        print(f"  ERROR: {invalid_keys} API keys missing created_by")
        sys.exit(1)
    
    total_keys = db.query(APIKey).count()
    print(f"  ✓ All {total_keys} API keys have creator information")
    
    # Step 4: Validate data integrity
    print("\n[4/4] Validating data integrity...")
    
    # Check for orphaned foreign keys
    orphaned_roles = db.query(Instructor).filter(
        Instructor.role_granted_by != None,
        ~Instructor.role_granted_by.in_(
            db.query(Instructor.id)
        )
    ).count()
    
    if orphaned_roles > 0:
        print(f"  WARNING: {orphaned_roles} instructors with invalid role_granted_by")
        db.query(Instructor).filter(
            Instructor.role_granted_by != None,
            ~Instructor.role_granted_by.in_(db.query(Instructor.id))
        ).update({'role_granted_by': None}, synchronize_session=False)
        db.commit()
    
    print("  ✓ Data integrity verified")
    
    print("\n" + "="*60)
    print("✓ RBAC Migration Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Deploy new code with RBAC support")
    print("2. Test authentication with new token format")
    print("3. Monitor audit logs for migration events")
    print()

if __name__ == '__main__':
    try:
        migrate_to_rbac()
    except Exception as e:
        print(f"\nERROR: Migration failed - {str(e)}")
        logger.exception("RBAC migration failed")
        sys.exit(1)
```

### 1.3 Testing Phase 1

#### Test Case 1.3.1: Schema Integrity

```python
def test_instructor_role_column_exists():
    """Verify role column exists and has correct type"""
    inspector = inspect(db.engine)
    columns = {c['name']: c for c in inspector.get_columns('instructors')}
    
    assert 'role' in columns
    assert columns['role']['type'].python_type == str
    assert columns['role']['nullable'] == False

def test_audit_logs_table_created():
    """Verify audit_logs table was created"""
    inspector = inspect(db.engine)
    assert 'audit_logs' in inspector.get_table_names()
    
    columns = {c['name']: c for c in inspector.get_columns('audit_logs')}
    required_columns = ['id', 'actor_id', 'target_id', 'target_type', 
                       'action', 'details', 'created_at']
    for col in required_columns:
        assert col in columns, f"Missing column: {col}"
```

#### Test Case 1.3.2: Data Migration

```python
def test_admin_instructor_created():
    """Verify admin instructor was created with SUPER_ADMIN role"""
    admin = db.query(Instructor).filter(Instructor.username == 'admin').first()
    assert admin is not None
    assert admin.role == 'SUPER_ADMIN'
    assert admin.is_active == True

def test_existing_instructors_have_role():
    """Verify all existing instructors have a role"""
    instructors_without_role = db.query(Instructor).filter(
        Instructor.role == None
    ).count()
    assert instructors_without_role == 0, "Found instructors without role"

def test_api_keys_have_creator():
    """Verify all API keys have created_by set"""
    keys_without_creator = db.query(APIKey).filter(
        APIKey.created_by == None
    ).count()
    assert keys_without_creator == 0, "Found API keys without creator"
```

#### Test Case 1.3.3: Backward Compatibility

```python
def test_is_active_field_unchanged():
    """Verify is_active field still works as before"""
    # Deactivate an instructor
    instructor = db.query(Instructor).first()
    instructor.is_active = False
    db.commit()
    
    # Query should still work
    active_count = db.query(Instructor).filter(Instructor.is_active == True).count()
    inactive_count = db.query(Instructor).filter(Instructor.is_active == False).count()
    
    assert active_count > 0 or inactive_count > 0
```

### 1.4 Validation Checklist

- [ ] All migrations run without errors
- [ ] No data loss during migration
- [ ] Schema changes are backward compatible
- [ ] Indexes are created and functional
- [ ] Admin instructor created with SUPER_ADMIN role
- [ ] All existing instructors have role assigned
- [ ] All API keys have created_by populated
- [ ] No orphaned foreign key references
- [ ] Data integrity tests pass
- [ ] Rollback procedure tested successfully

---

## Phase 2: Enhanced Authentication

**Duration**: 4-5 days
**Team Size**: 1-2 developers
**Risk Level**: High (core authentication)

### 2.1 Objectives

- Update JWT token generation to include role and permissions
- Implement new authorization decorators for role-based access
- Enhance get_current_instructor to validate roles
- Create backward compatibility layer for existing tokens
- Update login endpoints to generate new tokens

### 2.2 Implementation Steps

#### Step 2.2.1: Update JWT Token Generation

**File**: `security.py` - Modify `create_access_token()` function

```python
def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access"
) -> str:
    """
    Create a JWT access token with role and permissions.
    
    Args:
        data: Token payload data
        expires_delta: Custom expiration time
        token_type: Type of token (access, refresh)
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": token_type
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=ALGORITHM
    )
    return encoded_jwt


def create_instructor_token(
    instructor_id: int, 
    username: str,
    role: str = "INSTRUCTOR",
    permissions: Optional[list] = None
) -> str:
    """
    Create JWT token for instructor with role and permissions.
    
    Args:
        instructor_id: ID of instructor
        username: Username of instructor
        role: Role of instructor (INSTRUCTOR, ADMIN, SUPER_ADMIN)
        permissions: List of specific permissions
    
    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    
    to_encode = {
        "sub": str(instructor_id),
        "username": username,
        "type": "instructor",  # Backward compatibility
        "role": role,
        "permissions": permissions or [],
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
```

#### Step 2.2.2: Create Authorization Decorators

**File**: `security.py` - Add new dependency factories

```python
from functools import wraps
from typing import List, Callable

# Role hierarchy for comparison
ROLE_HIERARCHY = {
    'INSTRUCTOR': 1,
    'ADMIN': 2,
    'SUPER_ADMIN': 3
}

def get_role_level(role: str) -> int:
    """Get numeric level of role for comparison"""
    return ROLE_HIERARCHY.get(role, 0)


def verify_role(required_role: str):
    """
    Dependency factory for role-based authorization.
    
    Usage:
        @router.get("/admin/users")
        def list_users(admin: Instructor = Depends(verify_role("ADMIN"))):
            pass
    """
    def _verify_role(
        current_user: Instructor = Depends(get_current_instructor)
    ) -> Instructor:
        user_level = get_role_level(current_user.role)
        required_level = get_role_level(required_role)
        
        if user_level < required_level:
            log_security_event(
                logger, "UNAUTHORIZED_ROLE_ACCESS",
                f"User {current_user.username} attempted to access {required_role} endpoint",
                severity="warning"
            )
            raise HTTPException(
                status_code=403,
                detail=f"This operation requires {required_role} role"
            )
        
        if not current_user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Your account has been deactivated"
            )
        
        return current_user
    
    return _verify_role


def verify_permission(permission: str):
    """
    Dependency factory for permission-based authorization.
    
    Usage:
        @router.post("/admin/users")
        def create_user(admin: Instructor = Depends(verify_permission("create_users"))):
            pass
    """
    def _verify_permission(
        current_user: Instructor = Depends(get_current_instructor)
    ) -> Instructor:
        # Extract permissions from JWT claims
        # If user has admin+ role, they have all permissions
        if get_role_level(current_user.role) >= get_role_level("ADMIN"):
            return current_user
        
        # For future granular permissions
        # Check if permission is in user's permission list
        if permission not in getattr(current_user, 'permissions', []):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required"
            )
        
        return current_user
    
    return _verify_permission
```

#### Step 2.2.3: Enhanced Current User Dependency

**File**: `routes_instructor.py` - Update `get_current_instructor()`

```python
def get_current_instructor(
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
) -> Instructor:
    """
    Enhanced dependency to get current authenticated instructor.
    
    Handles both new and old token formats for backward compatibility.
    Validates instructor is active and role hasn't changed.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Missing authentication token"
        )

    token = authorization.split(" ")[1]
    
    try:
        payload = verify_instructor_token(token)
    except HTTPException as e:
        log_security_event(
            logger, "INVALID_TOKEN",
            f"Invalid token provided",
            severity="warning"
        )
        raise
    
    instructor_id = int(payload.get("sub"))
    
    # Fetch current instructor state from database
    instructor = db.query(Instructor).filter(
        Instructor.id == instructor_id
    ).first()
    
    if not instructor:
        log_security_event(
            logger, "INSTRUCTOR_NOT_FOUND",
            f"Instructor {instructor_id} not found",
            severity="warning"
        )
        raise HTTPException(
            status_code=401, 
            detail="Instructor not found"
        )
    
    if not instructor.is_active:
        log_security_event(
            logger, "INACTIVE_INSTRUCTOR_LOGIN",
            f"Inactive instructor attempted access: {instructor.username}",
            severity="warning"
        )
        raise HTTPException(
            status_code=403, 
            detail="Your account has been deactivated"
        )
    
    # Verify role in token matches database
    # This ensures role changes are enforced immediately
    token_role = payload.get("role", "INSTRUCTOR")
    if token_role != instructor.role:
        log_security_event(
            logger, "ROLE_MISMATCH",
            f"Token role {token_role} != database role {instructor.role}",
            severity="warning"
        )
        # Don't fail, but use database role (enforces role change)
        # Could optionally force re-login here
    
    # Update last_login timestamp
    instructor.last_login = datetime.utcnow()
    db.commit()
    
    return instructor
```

#### Step 2.2.4: Backward Compatibility Handler

**File**: `security.py` - Add token validation with fallback

```python
def verify_instructor_token(token: str) -> dict:
    """
    Verify instructor JWT token with backward compatibility.
    
    Handles both old format (type=instructor only) and new format (with role).
    Returns payload dict for token processing.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        
        # Check token type
        token_type = payload.get("type")
        if token_type != "instructor":
            # Could be old admin token, check that separately
            if payload.get("sub") == "admin":
                raise HTTPException(
                    status_code=401, 
                    detail="Please login with instructor credentials"
                )
            raise HTTPException(
                status_code=401, 
                detail="Invalid token type"
            )
        
        # Add default role if not present (backward compatibility)
        if "role" not in payload:
            payload["role"] = "INSTRUCTOR"
        
        return payload
        
    except jwt.ExpiredSignatureError:
        log_security_event(
            logger, "EXPIRED_TOKEN",
            "Expired instructor token",
            severity="info"
        )
        raise HTTPException(
            status_code=401, 
            detail="Token expired"
        )
    except jwt.JWTError as e:
        log_security_event(
            logger, "INVALID_TOKEN",
            f"Token validation failed: {str(e)}",
            severity="warning"
        )
        raise HTTPException(
            status_code=401, 
            detail="Invalid token"
        )
```

#### Step 2.2.5: Update Login Endpoints

**File**: `routes_instructor.py` - Update login endpoint to use new token

```python
@router.post("/login", response_model=Token)
def login_instructor(data: InstructorLogin, db: DBSession = Depends(get_db)):
    """
    Login with username/email and password.
    
    Updated to return JWT with role and permissions included.
    """
    # Try to find instructor by username first, then by email
    instructor = db.query(Instructor).filter(
        Instructor.username == data.username
    ).first()
    
    if not instructor:
        # Try email if username doesn't match
        instructor = db.query(Instructor).filter(
            Instructor.email == data.username
        ).first()

    # Check if instructor found and password matches
    if not instructor:
        log_security_event(
            logger, "LOGIN_FAILED", 
            f"No instructor found for: {data.username}", 
            severity="warning"
        )
        raise HTTPException(
            status_code=401, 
            detail="Incorrect username/email or password"
        )

    if not verify_password(data.password, instructor.password_hash):
        log_security_event(
            logger, "LOGIN_FAILED", 
            f"Failed login attempt for: {data.username}", 
            severity="warning"
        )
        raise HTTPException(
            status_code=401, 
            detail="Incorrect username/email or password"
        )

    if not instructor.is_active:
        log_security_event(
            logger, "LOGIN_FAILED", 
            f"Inactive account login attempt: {instructor.username}", 
            severity="warning"
        )
        raise HTTPException(
            status_code=401, 
            detail="Account is inactive"
        )

    # Create token with role included
    access_token = create_instructor_token(
        instructor.id, 
        instructor.username,
        role=instructor.role,
        permissions=[]  # Future: extract from database
    )
    
    # Update last_login
    instructor.last_login = datetime.utcnow()
    db.commit()
    
    log_security_event(
        logger, "LOGIN_SUCCESS", 
        f"Instructor logged in: {instructor.username}", 
        severity="info"
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": instructor.role
    }
```

### 2.3 Testing Phase 2

#### Test Case 2.3.1: Token Generation

```python
def test_create_instructor_token_with_role():
    """Verify token includes role claim"""
    token = create_instructor_token(1, "testuser", role="ADMIN")
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    
    assert payload["role"] == "ADMIN"
    assert payload["sub"] == "1"
    assert payload["username"] == "testuser"
    assert payload["type"] == "instructor"

def test_backward_compatible_token():
    """Verify old tokens without role still work"""
    # Create old-style token
    to_encode = {
        "sub": "1",
        "username": "testuser",
        "type": "instructor",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    
    # Should still be valid
    payload = verify_instructor_token(token)
    assert payload["role"] == "INSTRUCTOR"  # Default
```

#### Test Case 2.3.2: Authorization Decorators

```python
def test_verify_role_admin_access():
    """Verify admin can access admin endpoints"""
    admin_instructor = create_test_instructor(role="ADMIN")
    
    # Should not raise exception
    result = verify_role("ADMIN")(admin_instructor)
    assert result.role == "ADMIN"

def test_verify_role_instructor_denied():
    """Verify instructor cannot access admin endpoints"""
    instructor = create_test_instructor(role="INSTRUCTOR")
    
    with pytest.raises(HTTPException) as exc_info:
        verify_role("ADMIN")(instructor)
    
    assert exc_info.value.status_code == 403
```

#### Test Case 2.3.3: Login Flow

```python
def test_login_returns_role():
    """Verify login response includes role"""
    instructor = create_test_instructor(role="ADMIN")
    
    response = test_client.post(
        "/api/instructors/login",
        json={"username": instructor.username, "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "role" in data
    assert data["role"] == "ADMIN"

def test_inactive_instructor_login_fails():
    """Verify inactive instructors cannot login"""
    instructor = create_test_instructor(is_active=False)
    
    response = test_client.post(
        "/api/instructors/login",
        json={"username": instructor.username, "password": "password123"}
    )
    
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()
```

### 2.4 Validation Checklist

- [ ] New tokens include role and permissions claims
- [ ] Backward compatibility with old tokens confirmed
- [ ] Authorization decorators work for all roles
- [ ] Role hierarchy correctly enforced
- [ ] Login endpoint returns role in response
- [ ] Role mismatches detected and handled
- [ ] Inactive accounts cannot login
- [ ] Token expiration still works
- [ ] Security events logged for failed auth
- [ ] All tests pass with new auth system

---

## Phase 3: API Key Self-Service

**Duration**: 3-4 days
**Team Size**: 1-2 developers
**Risk Level**: Medium (new functionality)

### 3.1 Objectives

- Implement instructor self-service API key creation
- Add API key management endpoints (list, update, revoke)
- Implement admin ability to create keys for other instructors
- Add comprehensive audit logging for key operations
- Update API key validation to work with new creator model

### 3.2 Implementation Steps

#### Step 3.2.1: Create API Key Service Class

**File**: `services/api_key_service.py` - New file

```python
"""
Service layer for API key management.
Handles creation, revocation, and validation with audit logging.
"""

from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from models_v2 import Instructor, APIKey
from models_config import AuditLog
from logging_config import log_security_event, get_logger
from typing import Optional, List

logger = get_logger(__name__)


class APIKeyService:
    """Service for API key management operations"""
    
    @staticmethod
    def create_key_for_self(
        creator: Instructor,
        name: str,
        db: DBSession
    ) -> APIKey:
        """
        Instructor creates API key for themselves.
        
        Args:
            creator: The instructor creating the key (authenticated user)
            name: Human-readable name for the key
            db: Database session
        
        Returns:
            Created APIKey object
        
        Raises:
            HTTPException: If key creation fails
        """
        if not creator.is_active:
            raise HTTPException(
                status_code=403,
                detail="Cannot create keys with inactive account"
            )
        
        # Generate secure key
        key_value = APIKey.generate_key()
        
        # Create API key
        api_key = APIKey(
            instructor_id=creator.id,
            key=key_value,
            name=name,
            created_by=creator.id,
            is_active=True
        )
        
        db.add(api_key)
        db.commit()
        
        # Log creation
        AuditLog.log(
            db=db,
            actor_id=creator.id,
            target_id=api_key.id,
            target_type="api_key",
            action="CREATE",
            details={
                "key_name": name,
                "for_instructor": creator.id,
                "self_created": True
            }
        )
        
        log_security_event(
            logger,
            "API_KEY_CREATED",
            f"Instructor {creator.username} created API key: {name}",
            severity="info"
        )
        
        return api_key
    
    @staticmethod
    def create_key_for_other(
        creator: Instructor,
        target_instructor: Instructor,
        name: str,
        db: DBSession
    ) -> APIKey:
        """
        Admin creates API key for another instructor.
        
        Args:
            creator: The admin creating the key (authenticated user)
            target_instructor: The instructor the key is for
            name: Human-readable name for the key
            db: Database session
        
        Returns:
            Created APIKey object
        
        Raises:
            HTTPException: If not authorized or creation fails
        """
        from security import get_role_level
        
        # Check authorization
        if get_role_level(creator.role) < get_role_level("ADMIN"):
            log_security_event(
                logger,
                "UNAUTHORIZED_KEY_CREATION",
                f"Non-admin {creator.username} attempted to create key for others",
                severity="warning"
            )
            raise HTTPException(
                status_code=403,
                detail="Admin role required to create keys for other instructors"
            )
        
        if not target_instructor.is_active:
            raise HTTPException(
                status_code=400,
                detail="Cannot create keys for inactive instructors"
            )
        
        # Generate secure key
        key_value = APIKey.generate_key()
        
        # Create API key
        api_key = APIKey(
            instructor_id=target_instructor.id,
            key=key_value,
            name=name,
            created_by=creator.id,
            is_active=True
        )
        
        db.add(api_key)
        db.commit()
        
        # Log creation
        AuditLog.log(
            db=db,
            actor_id=creator.id,
            target_id=api_key.id,
            target_type="api_key",
            action="CREATE",
            details={
                "key_name": name,
                "for_instructor": target_instructor.id,
                "created_by_admin": creator.id
            }
        )
        
        log_security_event(
            logger,
            "API_KEY_CREATED_FOR_USER",
            f"Admin {creator.username} created API key for {target_instructor.username}",
            severity="info"
        )
        
        return api_key
    
    @staticmethod
    def revoke_key(
        revoker: Instructor,
        key_id: int,
        reason: str,
        db: DBSession
    ) -> APIKey:
        """
        Revoke an API key.
        
        Args:
            revoker: The instructor revoking the key
            key_id: ID of key to revoke
            reason: Reason for revocation
            db: Database session
        
        Returns:
            Updated APIKey object
        
        Raises:
            HTTPException: If not authorized or key not found
        """
        from security import get_role_level
        
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Check authorization
        # User can revoke their own keys, or admin can revoke any key
        is_own_key = (api_key.instructor_id == revoker.id)
        is_admin = get_role_level(revoker.role) >= get_role_level("ADMIN")
        
        if not (is_own_key or is_admin):
            log_security_event(
                logger,
                "UNAUTHORIZED_KEY_REVOCATION",
                f"{revoker.username} attempted to revoke key they don't own",
                severity="warning"
            )
            raise HTTPException(
                status_code=403,
                detail="Cannot revoke other users' API keys"
            )
        
        # Revoke the key
        api_key.is_active = False
        api_key.revoked_by = revoker.id
        api_key.revoked_at = datetime.utcnow()
        api_key.revocation_reason = reason
        
        db.commit()
        
        # Log revocation
        AuditLog.log(
            db=db,
            actor_id=revoker.id,
            target_id=api_key.id,
            target_type="api_key",
            action="REVOKE",
            details={
                "key_name": api_key.name,
                "reason": reason,
                "revoked_by": revoker.id
            }
        )
        
        log_security_event(
            logger,
            "API_KEY_REVOKED",
            f"API key revoked: {api_key.name} (Reason: {reason})",
            severity="info"
        )
        
        return api_key
    
    @staticmethod
    def list_keys_for_instructor(
        instructor: Instructor,
        db: DBSession,
        include_revoked: bool = False
    ) -> List[APIKey]:
        """
        List all API keys for an instructor.
        
        Args:
            instructor: Instructor to list keys for
            db: Database session
            include_revoked: Whether to include revoked keys
        
        Returns:
            List of APIKey objects
        """
        query = db.query(APIKey).filter(
            APIKey.instructor_id == instructor.id
        )
        
        if not include_revoked:
            query = query.filter(APIKey.is_active == True)
        
        return query.all()
```

#### Step 3.2.2: Create API Key Endpoints

**File**: `routes/api_keys.py` - New router

```python
"""
Self-service API key management endpoints.
Allows instructors to manage their own keys and admins to manage all keys.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List

from database import get_db
from models_v2 import Instructor, APIKey
from schemas_v2 import APIKeyResponse, APIKeyCreateRequest
from routes_instructor import get_current_instructor
from security import verify_role
from services.api_key_service import APIKeyService
from logging_config import log_security_event, get_logger

router = APIRouter(prefix="/api/instructors/api-keys", tags=["api-keys"])
logger = get_logger(__name__)


@router.post("", response_model=APIKeyResponse)
def create_api_key(
    request: APIKeyCreateRequest,
    current_user: Instructor = Depends(get_current_instructor),
    db: DBSession = Depends(get_db)
):
    """
    Create a new API key for the authenticated instructor.
    
    Each instructor can create multiple API keys for different applications/integrations.
    
    Args:
        request: APIKeyCreateRequest with key name
        current_user: Authenticated instructor
        db: Database session
    
    Returns:
        APIKeyResponse with created key details (key value only shown once)
    """
    api_key = APIKeyService.create_key_for_self(
        creator=current_user,
        name=request.name,
        db=db
    )
    
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=api_key.key,  # Only shown at creation time
        created_at=api_key.created_at,
        last_used=api_key.last_used,
        is_active=api_key.is_active
    )


@router.get("", response_model=List[APIKeyResponse])
def list_api_keys(
    current_user: Instructor = Depends(get_current_instructor),
    db: DBSession = Depends(get_db)
):
    """
    List all active API keys for the authenticated instructor.
    
    Args:
        current_user: Authenticated instructor
        db: Database session
    
    Returns:
        List of APIKeyResponse objects (key values not included)
    """
    keys = APIKeyService.list_keys_for_instructor(
        instructor=current_user,
        db=db,
        include_revoked=False
    )
    
    return [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            created_at=key.created_at,
            last_used=key.last_used,
            is_active=key.is_active
        )
        for key in keys
    ]


@router.delete("/{key_id}")
def revoke_api_key(
    key_id: int,
    current_user: Instructor = Depends(get_current_instructor),
    db: DBSession = Depends(get_db)
):
    """
    Revoke an API key.
    
    Users can revoke their own keys. Admins can revoke any key.
    
    Args:
        key_id: ID of key to revoke
        current_user: Authenticated instructor
        db: Database session
    
    Returns:
        Success message
    """
    api_key = APIKeyService.revoke_key(
        revoker=current_user,
        key_id=key_id,
        reason="User revocation",
        db=db
    )
    
    return {"message": f"API key '{api_key.name}' has been revoked"}


@router.put("/{key_id}")
def update_api_key(
    key_id: int,
    name: str,
    current_user: Instructor = Depends(get_current_instructor),
    db: DBSession = Depends(get_db)
):
    """
    Update API key name/metadata.
    
    Users can update their own keys. Admins can update any key.
    
    Args:
        key_id: ID of key to update
        name: New name for the key
        current_user: Authenticated instructor
        db: Database session
    
    Returns:
        Updated APIKeyResponse
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Check authorization
    if api_key.instructor_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Cannot update other users' API keys"
        )
    
    old_name = api_key.name
    api_key.name = name
    db.commit()
    
    log_security_event(
        logger,
        "API_KEY_UPDATED",
        f"API key updated: '{old_name}' -> '{name}'",
        severity="info"
    )
    
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        created_at=api_key.created_at,
        last_used=api_key.last_used,
        is_active=api_key.is_active
    )
```

#### Step 3.2.3: Update Schemas

**File**: `schemas_v2.py` - Add API key schemas

```python
class APIKeyCreateRequest(BaseModel):
    """Request to create a new API key"""
    name: str = Field(..., min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    """Response with API key information"""
    id: int
    name: str
    key: Optional[str] = None  # Only included at creation time
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """List of API keys for display"""
    keys: List[APIKeyResponse]
    total: int
```

### 3.3 Testing Phase 3

#### Test Case 3.3.1: Self-Service Key Creation

```python
def test_instructor_create_own_key():
    """Instructor can create their own API key"""
    instructor = create_test_instructor()
    
    response = test_client.post(
        "/api/instructors/api-keys",
        headers={"Authorization": f"Bearer {get_test_token(instructor)}"},
        json={"name": "My Integration"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Integration"
    assert "key" in data
    assert data["is_active"] == True

def test_list_own_keys():
    """Instructor can list their own keys"""
    instructor = create_test_instructor()
    create_test_api_key(instructor)
    create_test_api_key(instructor)
    
    response = test_client.get(
        "/api/instructors/api-keys",
        headers={"Authorization": f"Bearer {get_test_token(instructor)}"}
    )
    
    assert response.status_code == 200
    keys = response.json()
    assert len(keys) == 2
```

#### Test Case 3.3.2: Admin Key Management

```python
def test_admin_create_key_for_other():
    """Admin can create API key for other instructor"""
    admin = create_test_instructor(role="ADMIN")
    instructor = create_test_instructor()
    
    # Admin creates key for instructor
    response = test_client.post(
        f"/api/admin/instructors/{instructor.id}/api-keys",
        headers={"Authorization": f"Bearer {get_test_token(admin)}"},
        json={"name": "Admin Created Key"}
    )
    
    assert response.status_code == 201
    
    # Verify instructor can see the key
    response = test_client.get(
        "/api/instructors/api-keys",
        headers={"Authorization": f"Bearer {get_test_token(instructor)}"}
    )
    
    assert response.status_code == 200
    keys = response.json()
    assert any(k["name"] == "Admin Created Key" for k in keys)

def test_instructor_cannot_create_for_others():
    """Regular instructor cannot create keys for others"""
    instructor1 = create_test_instructor()
    instructor2 = create_test_instructor()
    
    response = test_client.post(
        f"/api/admin/instructors/{instructor2.id}/api-keys",
        headers={"Authorization": f"Bearer {get_test_token(instructor1)}"},
        json={"name": "Malicious Key"}
    )
    
    assert response.status_code == 403
```

#### Test Case 3.3.3: Key Revocation

```python
def test_revoke_own_key():
    """Instructor can revoke their own key"""
    instructor = create_test_instructor()
    api_key = create_test_api_key(instructor)
    
    response = test_client.delete(
        f"/api/instructors/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {get_test_token(instructor)}"}
    )
    
    assert response.status_code == 200
    
    # Verify key is inactive
    db_key = db.query(APIKey).filter(APIKey.id == api_key.id).first()
    assert db_key.is_active == False
    assert db_key.revoked_at is not None
    assert db_key.revoked_by == instructor.id
```

### 3.4 Validation Checklist

- [ ] Instructors can create their own API keys
- [ ] Instructors can list their own keys
- [ ] Instructors can revoke their own keys
- [ ] Instructors can update their own key names
- [ ] Admins can create keys for other instructors
- [ ] Admins can revoke any API key
- [ ] Revoked keys cannot be used for authentication
- [ ] Key creation events are logged
- [ ] Key revocation events are logged
- [ ] All API key endpoints require authentication
- [ ] All tests pass

---

## Phase 4: User Management & Admin Functions

**Duration**: 4-5 days
**Team Size**: 2 developers
**Risk Level**: High (core admin functionality)

### 4.1 Objectives

- Implement role promotion/demotion endpoints
- Create instructor activation/deactivation endpoints
- Build bulk operations for admin efficiency
- Add admin user management interface
- Implement comprehensive authorization checks

### 4.2 Implementation Steps

*(Due to length constraints, this section follows same patterns as Phase 3)*

#### Step 4.2.1: User Management Service

**File**: `services/user_management_service.py` - New file

Key methods:
- `promote_to_admin(admin, target, db)` - Promote instructor to admin
- `demote_from_admin(super_admin, target, db)` - Remove admin privileges
- `deactivate_instructor(admin, target, reason, db)` - Deactivate account
- `reactivate_instructor(admin, target, db)` - Reactivate account
- `bulk_deactivate(admin, instructor_ids, reason, db)` - Batch deactivation

#### Step 4.2.2: Admin Endpoints

**File**: `routes/admin_users.py` - New router

Endpoints:
- `POST /api/admin/instructors` - Create new instructor
- `PUT /api/admin/instructors/{id}/role` - Change role
- `PUT /api/admin/instructors/{id}/deactivate` - Deactivate user
- `PUT /api/admin/instructors/{id}/activate` - Reactivate user
- `GET /api/admin/instructors` - List all instructors with filters
- `GET /api/admin/instructors/{id}` - Get instructor details
- `POST /api/admin/bulk-actions` - Bulk operations

### 4.3 Testing Phase 4

Similar pattern to previous phases with tests for:
- Role promotion/demotion with proper authorization
- Deactivation workflows
- Bulk operations
- Authorization enforcement

---

## Phase 5: Cascading Deactivation

**Duration**: 3-4 days
**Team Size**: 1-2 developers
**Risk Level**: Medium (affects existing data)

### 5.1 Objectives

- Implement cascade logic for deactivated instructors
- Classes and sessions become read-only
- API keys automatically revoked
- Historical data preserved and accessible
- Real-time enforcement of read-only state

### 5.2 Implementation Steps

#### Step 5.2.1: Deactivation Cascade Service

**File**: `services/deactivation_service.py` - New file

```python
class DeactivationService:
    @staticmethod
    def deactivate_instructor_cascade(
        instructor_id: int,
        db: DBSession,
        reason: str = ""
    ):
        """
        Cascade deactivation to all instructor resources.
        
        1. Revoke all active API keys
        2. Mark all classes as archived
        3. End all active sessions
        4. Make all historical data read-only
        """
        # Step 1: Revoke API keys
        keys = db.query(APIKey).filter(
            APIKey.instructor_id == instructor_id,
            APIKey.is_active == True
        ).all()
        
        for key in keys:
            key.is_active = False
            key.revoked_by = instructor_id  # Self-revoked
            key.revoked_at = datetime.utcnow()
            key.revocation_reason = f"Account deactivated: {reason}"
        
        # Step 2: Archive classes
        classes = db.query(Class).filter(
            Class.instructor_id == instructor_id
        ).all()
        
        for cls in classes:
            cls.is_archived = True
        
        # Step 3: End active sessions
        active_meetings = db.query(ClassMeeting).filter(
            ClassMeeting.class_id.in_([c.id for c in classes]),
            ClassMeeting.is_active == True
        ).all()
        
        for meeting in active_meetings:
            meeting.is_active = False
            meeting.ended_at = datetime.utcnow()
        
        db.commit()
```

#### Step 5.2.2: Read-Only Enforcement

Add checks to all write endpoints to prevent modifications to:
- Classes belonging to deactivated instructors
- Sessions belonging to deactivated instructors  
- Questions in sessions of deactivated instructors

---

## Phase 6: Admin Interface & Analytics

**Duration**: 4-5 days
**Team Size**: 2 developers (1 backend, 1 frontend)
**Risk Level**: Low (UI/presentation layer)

### 6.1 Objectives

- Build admin user management interface
- Create audit log viewer
- Implement analytics dashboard
- Add export functionality

### 6.2 Frontend Changes

Update `templates/admin.html`:
- New "Users" tab for instructor management
- User list with search/filter
- Role change UI
- Deactivation dialog
- Bulk operations interface

### 6.3 API Endpoints for UI

- `GET /api/admin/analytics` - System statistics
- `GET /api/admin/audit-logs` - Paginated audit logs
- `POST /api/admin/audit-logs/export` - Export audit trail
- `GET /api/admin/security-events` - Security monitoring

---

## Testing Framework

### Unit Test Structure

```python
# tests/test_rbac_auth.py
class TestRBACAuthentication:
    def test_token_includes_role(self): ...
    def test_role_hierarchy(self): ...
    def test_backward_compatibility(self): ...

# tests/test_api_key_service.py
class TestAPIKeyService:
    def test_create_own_key(self): ...
    def test_admin_create_for_other(self): ...
    def test_revoke_key(self): ...

# tests/test_user_management.py
class TestUserManagement:
    def test_promote_to_admin(self): ...
    def test_deactivate_cascade(self): ...
    def test_bulk_operations(self): ...

# tests/test_authorization.py
class TestAuthorization:
    def test_role_boundaries(self): ...
    def test_permission_checks(self): ...
    def test_audit_logging(self): ...
```

### Integration Test Structure

```python
# tests/integration/test_full_workflows.py
class TestAdminWorkflows:
    def test_promote_instructor_to_admin(self): ...
    def test_deactivate_and_verify_cascade(self): ...
    def test_audit_trail_completeness(self): ...

class TestInstructorWorkflows:
    def test_create_and_use_api_key(self): ...
    def test_manage_own_keys(self): ...
    def test_cannot_access_admin_features(self): ...
```

### Security Test Structure

```python
# tests/security/test_rbac_security.py
class TestRBACSecurityVulnerabilities:
    def test_privilege_escalation_prevention(self): ...
    def test_token_tampering_detection(self): ...
    def test_role_boundary_enforcement(self): ...
    def test_audit_log_integrity(self): ...
```

---

## Deployment & Rollback

### Pre-Deployment Checklist

- [ ] All unit tests pass (100% coverage of auth code)
- [ ] All integration tests pass
- [ ] Security testing completed
- [ ] Performance benchmarking completed
- [ ] Database backups created
- [ ] Rollback procedures tested
- [ ] Communication sent to users
- [ ] Support team trained

### Deployment Steps

1. **Phase 1-2 (Low Risk)**: Deploy database + auth changes
   - Run migrations
   - Deploy code
   - Monitor for errors
   
2. **Phase 3-4 (Medium Risk)**: Deploy new endpoints
   - Deploy new services
   - Enable new endpoints
   - Monitor adoption
   
3. **Phase 5-6 (High Risk)**: Deploy UI + cascading features
   - Deploy frontend updates
   - Enable cascading features
   - Monitor cascade operations

### Rollback Procedure

If critical issues arise:

1. Stop accepting new requests (circuit breaker)
2. Downgrade code to previous version
3. Run rollback migrations
4. Verify system functionality
5. Post-mortem analysis

---

## Success Metrics & Monitoring

### Functional Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Auth Success Rate | >99.9% | Hourly auth success count |
| API Key Valid Rate | 100% | Failed key validations |
| Cascade Completion | 100% | Failed cascade operations |

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Auth Latency | <10ms | P95 response time |
| API Key Validation | <5ms | P95 validation time |
| Role Check Overhead | <5ms | P95 authorization check |

### Security Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Failed Auth Log | 100% | Audit log completeness |
| Privilege Escalation | 0 | Security test results |
| Token Tampering | 0 | Tamper detection tests |

---

## Phase 7: Code Cleanup & Package Finalization

**Duration**: 2-3 days
**Team Size**: 1-2 developers
**Risk Level**: Low (refactoring only)

### 7.1 Objectives

- Remove deprecated admin authentication system
- Clean up legacy code and imports
- Consolidate authorization functions
- Remove temporary backward compatibility shims
- Update all documentation
- Final code review and testing

### 7.2 Cleanup Implementation

#### Step 7.2.1: Remove Legacy Admin Authentication

**Files to delete/deprecate:**
1. `routes_admin.py` - `verify_admin()` function
2. `main.py` - `admin_login()` endpoint and `AdminLogin` schema
3. Legacy admin JWT generation code

**Migration path:**
```python
# OLD - to be removed
@router.post("/api/admin/login")
def admin_login(login_data: AdminLogin):
    # Single password check
    if login_data.password == settings.admin_password:
        return JWT with sub="admin"

# NEW - uses instructor system
@router.post("/api/instructors/login")
def login_instructor(login_data: InstructorLogin):
    # Authenticate as SUPER_ADMIN instructor
    # Returns JWT with role="SUPER_ADMIN"
```

**Implementation script:**

```python
# scripts/cleanup_legacy_admin.py
"""
Cleanup script to remove legacy admin system references.
Run AFTER RBAC implementation is confirmed stable.
"""

import os
import re
from pathlib import Path

def remove_legacy_admin_references():
    """Remove all references to legacy admin system"""
    
    files_to_clean = [
        'routes_admin.py',  # Can be deleted entirely, endpoints migrated
        'main.py',  # Remove admin_login endpoint and AdminLogin schema
        'schemas_v2.py',  # Remove AdminLogin class
        'templates/admin-login.html',  # Migrate to instructor-login flow
        'templates/admin.html'  # No changes needed, still valid
    ]
    
    # Step 1: Remove verify_admin function from routes_admin.py
    # This function is replaced by verify_role("SUPER_ADMIN")
    
    # Step 2: Remove admin_login endpoint from main.py
    print("Removing legacy admin_login endpoint...")
    
    # Step 3: Remove AdminLogin schema from schemas_v2.py
    print("Removing AdminLogin schema...")
    
    # Step 4: Update environment documentation
    print("Removing ADMIN_PASSWORD from documentation...")
    # ADMIN_PASSWORD can still exist for backward compatibility,
    # but is no longer used by the system
    
    # Step 5: Remove test files for old admin system
    print("Removing legacy admin tests...")
    test_files = list(Path('tests').glob('test_admin_legacy*.py'))
    for test_file in test_files:
        test_file.unlink()
    
    print("✓ Legacy admin system cleanup complete")


if __name__ == '__main__':
    remove_legacy_admin_references()
```

#### Step 7.2.2: Consolidate Authorization Functions

**File**: `security.py` - Organization refactor

```python
# BEFORE: Mixed auth functions scattered
def verify_jwt_token(token: str): ...
def create_access_token(data: dict): ...
def verify_instructor_token(token: str): ...
def create_instructor_token(instructor_id, username, role): ...
def verify_role(required_role): ...
def verify_permission(permission): ...

# AFTER: Well-organized module structure
class TokenManager:
    """Token generation and validation"""
    @staticmethod
    def create_instructor_token(...): ...
    @staticmethod
    def verify_instructor_token(...): ...

class AuthorizationManager:
    """Authorization and role-based access control"""
    @staticmethod
    def verify_role(required_role): ...
    @staticmethod
    def verify_permission(permission): ...
    @staticmethod
    def has_role(user, required_role): ...
    @staticmethod
    def can_manage_user(actor, target): ...
```

#### Step 7.2.3: Remove Backward Compatibility Shims

After 2-3 months of stable RBAC operation:

**Remove from security.py:**
```python
# OLD - backward compatibility for tokens without role claim
if "role" not in payload:
    payload["role"] = "INSTRUCTOR"  # DEFAULT FOR OLD TOKENS

# Can be removed once all old tokens are expired
# (After 30 days of access token expiration)
```

**Remove from routes_instructor.py:**
```python
# OLD - handling role mismatches gracefully
if token_role != instructor.role:
    # Could log but continue
    # This was temporary while tokens were updating

# Can be removed - enforce strict role checking
if token_role != instructor.role:
    raise HTTPException(403, "Token role mismatch")
```

#### Step 7.2.4: Update Imports Throughout Codebase

**Script to update imports:**

```python
# Old imports to be replaced
from routes_admin import verify_admin  # REMOVE
# Replace with:
from security import verify_role

# Old schema imports to be removed
from schemas_v2 import AdminLogin  # REMOVE

# Update all route decorators
# OLD: @router.get(..., dependencies=[Depends(verify_admin)])
# NEW: @router.get(..., dependencies=[Depends(verify_role("SUPER_ADMIN"))])
```

#### Step 7.2.5: Clean Up Configuration

**config.py** - Remove/deprecate admin settings:

```python
class Settings(BaseModel):
    # DEPRECATED - no longer used
    # admin_password: Optional[str] = None  
    # Can be removed after confirmed stable deployment
    
    # NEW - role-based system configuration
    role_hierarchy: Dict[str, int] = {
        'INSTRUCTOR': 1,
        'ADMIN': 2,
        'SUPER_ADMIN': 3
    }
    
    access_token_expire_minutes: int = 30 * 24 * 60
    
    # NEW - security settings for RBAC
    token_revocation_check_enabled: bool = True
    audit_logging_enabled: bool = True
```

#### Step 7.2.6: Clean Up Templates

**Remove deprecated files:**
- `templates/admin-login.html` - Merge into `templates/instructor-login.html` if needed, or retire

**Update templates:**
- `templates/admin.html` - Keep, but update references to use role-based checks
- `templates/instructor.html` - No changes needed
- `templates/profile.html` - Add RBAC role display for admins

#### Step 7.2.7: Consolidate Test Files

**Before:**
```
tests/
├── test_admin_legacy.py          # OLD
├── test_admin_new.py              # NEW
├── test_api_key_auth.py           # OLD
├── test_api_keys_service.py       # NEW
└── test_rbac_auth.py
```

**After:**
```
tests/
├── test_authentication.py          # Consolidated
├── test_authorization.py           # Consolidated
├── test_api_key_management.py      # Consolidated
├── test_user_management.py         # Consolidated
├── test_cascading_deactivation.py
└── security/
    ├── test_privilege_escalation.py
    ├── test_token_tampering.py
    └── test_audit_integrity.py
```

#### Step 7.2.8: Documentation Cleanup

**Files to update/remove:**

1. **README.md**
   - Remove "Admin Password Setup" section
   - Update "Getting Started" with new instructor-admin flow
   - Add RBAC overview

2. **SETUP.md / DEPLOYMENT.md**
   - Remove ADMIN_PASSWORD requirement
   - Update with RBAC initialization steps
   - Add role management documentation

3. **SECURITY.md**
   - Update authentication section
   - Add RBAC security considerations
   - Update audit trail documentation

4. **Environment Variables Documentation**
   ```
   # DEPRECATED
   ADMIN_PASSWORD=...  # No longer needed, kept for backward compatibility
   
   # NEW (if needed)
   RBAC_ENABLED=true   # Feature flag (can be removed once stable)
   ```

### 7.3 Cleanup Validation

#### Test Case 7.3.1: No Legacy Code References

```python
def test_no_verify_admin_imports():
    """Ensure verify_admin is not imported anywhere"""
    import os
    import re
    
    for root, dirs, files in os.walk('app'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file)) as f:
                    content = f.read()
                    assert 'from routes_admin import verify_admin' not in content
                    assert 'verify_admin' not in content

def test_no_admin_login_endpoint():
    """Ensure old admin_login endpoint is removed"""
    response = test_client.post("/api/admin/login")
    assert response.status_code == 404  # Endpoint should not exist

def test_admin_login_redirects_to_instructor():
    """Verify admin login redirects to instructor flow"""
    response = test_client.get("/admin-login")
    # Should redirect to /instructor-login
    assert response.status_code in [301, 302]
    assert "instructor-login" in response.headers.get("location", "")
```

#### Test Case 7.3.2: Code Quality Checks

```python
def test_imports_are_organized():
    """Verify imports follow standard organization"""
    # Python stdlib imports
    # Third-party imports
    # Local imports
    
def test_no_circular_imports():
    """Ensure no circular import dependencies"""
    # Import all modules - should not raise ImportError
    
def test_deprecated_code_warnings():
    """Ensure deprecated code properly marked"""
    import warnings
    # Deprecated functions should emit DeprecationWarning
```

#### Test Case 7.3.3: Documentation Completeness

```python
def test_documentation_updated():
    """Verify documentation reflects new RBAC system"""
    docs_files = [
        'README.md',
        'SETUP.md',
        'SECURITY.md'
    ]
    
    for doc_file in docs_files:
        with open(doc_file) as f:
            content = f.read()
            # Should not reference old admin_password setup
            assert 'ADMIN_PASSWORD setup' not in content
            # Should reference RBAC
            assert 'RBAC' in content or 'role' in content.lower()
```

### 7.4 Cleanup Checklist

#### Code Cleanup
- [ ] Remove `verify_admin()` function from `routes_admin.py`
- [ ] Delete `admin_login()` endpoint from `main.py`
- [ ] Remove `AdminLogin` schema from `schemas_v2.py`
- [ ] Remove backward compatibility shims from auth code
- [ ] Consolidate auth functions in `security.py`
- [ ] Update all imports throughout codebase
- [ ] Remove legacy test files
- [ ] Update `config.py` to remove admin_password settings

#### Template Cleanup
- [ ] Deprecate/remove `templates/admin-login.html`
- [ ] Update `templates/admin.html` for role display
- [ ] Update `templates/instructor-login.html` for admin login

#### Documentation Cleanup
- [ ] Update `README.md` with RBAC overview
- [ ] Update `SETUP.md` with new initialization
- [ ] Update `SECURITY.md` with RBAC details
- [ ] Update all environment variable documentation
- [ ] Remove old admin setup instructions
- [ ] Add role management guide

#### Testing Cleanup
- [ ] Consolidate test files
- [ ] Remove legacy admin tests
- [ ] Add RBAC-specific tests
- [ ] Verify 100% test coverage of auth code
- [ ] Run final integration tests

#### Configuration Cleanup
- [ ] Update `.env.example` to remove ADMIN_PASSWORD
- [ ] Update Docker configuration
- [ ] Update deployment guides
- [ ] Remove admin-specific environment variables

#### Final Verification
- [ ] No "TODO" comments related to RBAC
- [ ] No dead code or unused imports
- [ ] All functions documented
- [ ] No hardcoded credentials
- [ ] Code follows project standards
- [ ] All tests pass
- [ ] Security review completed

### 7.5 Cleanup Timeline

**Week 1-2 (After Phase 6):**
- Monitor RBAC system in production
- Collect feedback and issues
- Plan cleanup activities

**Week 2-4:**
- Perform Phase 7 cleanup
- Update documentation
- Run extended testing

**Week 4+:**
- Remove backward compatibility shims (after token expiration)
- Archive legacy code
- Final code review

### 7.6 Deprecation Policy

Items marked for removal:

| Item | Removal Date | Reason |
|------|--------------|--------|
| `verify_admin()` | 2 weeks | Replaced by `verify_role("SUPER_ADMIN")` |
| `AdminLogin` schema | 2 weeks | Use `InstructorLogin` instead |
| `admin_login()` endpoint | 2 weeks | Use instructor login with SUPER_ADMIN role |
| Backward compat tokens | 60 days | After token expiration |
| `ADMIN_PASSWORD` env var | 90 days | No longer used |

---

## Conclusion

This development guide provides a complete roadmap for implementing RBAC in RaiseMyHand. Each phase builds on the previous one, with comprehensive testing at every step. The phased approach ensures that the system remains stable and functional throughout the transition.

Key success factors:
1. **Thorough Testing**: Comprehensive tests at each phase
2. **Security First**: Security considerations throughout
3. **Backward Compatibility**: Seamless transition for users
4. **Clear Communication**: Team and user alignment
5. **Monitoring & Observability**: Real-time issue detection
6. **Clean Closure**: Phase 7 ensures a final clean codebase

Follow this guide phase by phase, and the RBAC system will be successfully implemented with minimal disruption to existing users, resulting in a clean, maintainable final package.