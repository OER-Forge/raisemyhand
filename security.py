"""Security utilities for authentication and token management."""

from datetime import datetime, timedelta
from typing import Optional
import secrets
from jose import jwt, JWTError
from passlib.context import CryptContext
from config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, stored_token: str) -> bool:
    """Verify a CSRF token."""
    return secrets.compare_digest(token, stored_token)


def verify_role(required_role: str):
    """
    Dependency function for role-based authorization.
    Works for both admin and instructor tokens.
    
    Usage:
        @router.post("/route")
        def some_endpoint(admin: Instructor = Depends(verify_role("ADMIN"))):
            ...
    
    Args:
        required_role: Required role (INSTRUCTOR, ADMIN, SUPER_ADMIN)
    
    Returns:
        Dependency function that verifies authenticated user has the required role
    """
    from fastapi import Depends, HTTPException, status, Header
    from database import get_db
    from models_v2 import Instructor
    from sqlalchemy.orm import Session as DBSession
    
    async def verify_role_dependency(
        authorization: str = Header(None),
        db: DBSession = Depends(get_db)
    ):
        """Verify user has required role."""
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token"
            )
        
        token = authorization.split(" ")[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Handle admin token (sub == "admin" or admin username)
        sub = payload.get("sub")
        if sub in ["admin"]:
            # Return a mock admin instructor object with SUPER_ADMIN role
            # This allows the rest of the code to treat it like an Instructor
            class AdminUser:
                id = 0
                username = "admin"
                role = "SUPER_ADMIN"
                is_active = True
            return AdminUser()
        
        # Handle instructor token
        try:
            instructor_id = int(sub)
            instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
            
            if not instructor or not instructor.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Instructor not found or inactive"
                )
            
            # Role hierarchy: SUPER_ADMIN > ADMIN > INSTRUCTOR > INACTIVE
            role_hierarchy = {
                "INACTIVE": 0,
                "INSTRUCTOR": 1,
                "ADMIN": 2,
                "SUPER_ADMIN": 3
            }
            
            required_level = role_hierarchy.get(required_role, 0)
            user_level = role_hierarchy.get(instructor.role or "INSTRUCTOR", 1)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{required_role} role required"
                )
            
            return instructor
            
        except ValueError:
            # If sub is not an integer and not "admin", it's invalid
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
    
    return verify_role_dependency
