"""
Instructor management routes for v2 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session as DBSession
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional

from database import get_db
from models_v2 import Instructor, APIKey as APIKeyV2
from schemas_v2 import (
    InstructorRegister, InstructorLogin, InstructorResponse,
    InstructorUpdate, Token, APIKeyCreate, APIKeyResponse
)
from config import settings
from security import verify_password, get_password_hash
from logging_config import get_logger, log_security_event, log_database_operation

router = APIRouter(prefix="/api/instructors", tags=["instructors"])
logger = get_logger(__name__)


def create_instructor_token(instructor_id: int, username: str) -> str:
    """Create JWT token for instructor."""
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {
        "sub": str(instructor_id),
        "username": username,
        "type": "instructor",
        "exp": expire
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_instructor_token(token: str) -> dict:
    """Verify instructor JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "instructor":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_instructor(
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
) -> Instructor:
    """Dependency to get current authenticated instructor."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = authorization.split(" ")[1]
    payload = verify_instructor_token(token)
    instructor_id = int(payload.get("sub"))

    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not instructor or not instructor.is_active:
        raise HTTPException(status_code=401, detail="Instructor not found or inactive")

    return instructor


@router.post("/register", response_model=InstructorResponse, status_code=status.HTTP_201_CREATED)
def register_instructor(data: InstructorRegister, db: DBSession = Depends(get_db)):
    """Register a new instructor."""
    # Check if registration is enabled
    from models_config import SystemConfig
    registration_enabled = SystemConfig.get_value(db, "instructor_registration_enabled", default=True)
    
    if not registration_enabled:
        disabled_reason = SystemConfig.get_value(db, "instructor_registration_disabled_reason", default="Registration is currently disabled")
        log_security_event(logger, "REGISTRATION_BLOCKED", f"Registration attempt blocked: {data.username}", severity="warning")
        raise HTTPException(
            status_code=403, 
            detail=f"Instructor registration is currently disabled. {disabled_reason}"
        )
    
    # Check if username already exists
    existing = db.query(Instructor).filter(Instructor.username == data.username).first()
    if existing:
        log_security_event(logger, "REGISTRATION_FAILED", f"Username already exists: {data.username}", severity="warning")
        raise HTTPException(status_code=400, detail="Username already taken")

    # Check if email already exists (if provided)
    if data.email:
        existing_email = db.query(Instructor).filter(Instructor.email == data.email).first()
        if existing_email:
            log_security_event(logger, "REGISTRATION_FAILED", f"Email already exists: {data.email}", severity="warning")
            raise HTTPException(status_code=400, detail="Email already registered")

    # Create instructor
    instructor = Instructor(
        username=data.username,
        email=data.email,
        display_name=data.display_name,
        password_hash=get_password_hash(data.password),
        created_at=datetime.utcnow()
    )

    try:
        db.add(instructor)
        db.commit()
        db.refresh(instructor)
        log_security_event(logger, "REGISTRATION_SUCCESS", f"New instructor registered: {data.username}", severity="info")
        log_database_operation(logger, "CREATE", "instructors", instructor.id, success=True)
        return instructor
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to register instructor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to register instructor")


@router.post("/login", response_model=Token)
def login_instructor(data: InstructorLogin, db: DBSession = Depends(get_db)):
    """Login with username/email and password."""
    # Try to find instructor by username first, then by email
    instructor = db.query(Instructor).filter(Instructor.username == data.username).first()
    
    if not instructor:
        # Try email if username doesn't match
        instructor = db.query(Instructor).filter(Instructor.email == data.username).first()

    # Check if instructor found and password matches
    if not instructor:
        log_security_event(logger, "LOGIN_FAILED", f"No instructor found for: {data.username}", severity="warning")
        raise HTTPException(status_code=401, detail="Incorrect username/email or password")

    if not verify_password(data.password, instructor.password_hash):
        log_security_event(logger, "LOGIN_FAILED", f"Failed login attempt for: {data.username}", severity="warning")
        raise HTTPException(status_code=401, detail="Incorrect username/email or password")

    if not instructor.is_active:
        log_security_event(logger, "LOGIN_FAILED", f"Inactive account login attempt: {instructor.username}", severity="warning")
        raise HTTPException(status_code=401, detail="Account is inactive")

    # Update last_login
    instructor.last_login = datetime.utcnow()
    db.commit()

    # Create token
    access_token = create_instructor_token(instructor.id, instructor.username)
    log_security_event(logger, "LOGIN_SUCCESS", f"Instructor logged in: {instructor.username}", severity="info")

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/profile", response_model=InstructorResponse)
def get_profile(instructor: Instructor = Depends(get_current_instructor)):
    """Get current instructor's profile."""
    return instructor


@router.put("/profile", response_model=InstructorResponse)
def update_profile(
    data: InstructorUpdate,
    instructor: Instructor = Depends(get_current_instructor),
    db: DBSession = Depends(get_db)
):
    """Update instructor profile (email, display name, password)."""
    try:
        # Update display name
        if data.display_name is not None:
            instructor.display_name = data.display_name

        # Update email
        if data.email is not None:
            # Check if email is already taken by another instructor
            existing = db.query(Instructor).filter(
                Instructor.email == data.email,
                Instructor.id != instructor.id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            instructor.email = data.email

        # Update password
        if data.new_password is not None:
            # Verify current password
            if not data.current_password:
                raise HTTPException(status_code=400, detail="Current password required to change password")

            if not verify_password(data.current_password, instructor.password_hash):
                log_security_event(logger, "PASSWORD_CHANGE_FAILED", f"Invalid current password for: {instructor.username}", severity="warning")
                raise HTTPException(status_code=401, detail="Current password is incorrect")

            # Verify new password is different
            if verify_password(data.new_password, instructor.password_hash):
                raise HTTPException(status_code=400, detail="New password must be different from current password")

            # Update password
            instructor.password_hash = get_password_hash(data.new_password)
            log_security_event(logger, "PASSWORD_CHANGED", f"Password changed for: {instructor.username}", severity="info")

        db.commit()
        db.refresh(instructor)
        log_database_operation(logger, "UPDATE", "instructors", instructor.id, success=True)
        return instructor
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.get("/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(
    instructor: Instructor = Depends(get_current_instructor),
    db: DBSession = Depends(get_db)
):
    """List instructor's API keys."""
    keys = db.query(APIKeyV2).filter(APIKeyV2.instructor_id == instructor.id).all()
    return keys


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    data: APIKeyCreate,
    instructor: Instructor = Depends(get_current_instructor),
    db: DBSession = Depends(get_db)
):
    """Create a new API key for instructor."""
    try:
        api_key = APIKeyV2(
            instructor_id=instructor.id,
            key=APIKeyV2.generate_key(),
            name=data.name,
            created_at=datetime.utcnow()
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        log_database_operation(logger, "CREATE", "api_keys", api_key.id, success=True)
        return api_key
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    key_id: int,
    instructor: Instructor = Depends(get_current_instructor),
    db: DBSession = Depends(get_db)
):
    """Deactivate an API key."""
    api_key = db.query(APIKeyV2).filter(
        APIKeyV2.id == key_id,
        APIKeyV2.instructor_id == instructor.id
    ).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    try:
        api_key.is_active = False
        db.commit()
        log_database_operation(logger, "UPDATE", "api_keys", api_key.id, success=True)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to deactivate API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to deactivate API key")
