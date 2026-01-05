"""
Admin user management service for creating and managing instructors.
Provides functionality for admin to create instructor accounts.
"""

from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from models_v2 import Instructor, ClassMeeting, APIKey
from security import get_password_hash
from logging_config import log_security_event, get_logger
from typing import Optional
from services.api_key_service import APIKeyService

logger = get_logger(__name__)


class UserManagementService:
    """Service for admin user management operations"""
    
    @staticmethod
    def create_instructor(
        admin: Instructor,
        username: str,
        email: Optional[str],
        display_name: Optional[str],
        password: str,
        role: str = "INSTRUCTOR",
        db: DBSession = None  # type: ignore
    ) -> Instructor:
        """
        Admin creates a new instructor account.
        
        Args:
            admin: The admin creating the account (authenticated user)
            username: Username for the new instructor
            email: Email address (optional)
            display_name: Display name (optional)
            password: Initial password
            role: Initial role (default: INSTRUCTOR)
            db: Database session
        
        Returns:
            Created Instructor object
        
        Raises:
        """
        from fastapi import HTTPException
        
        if not admin or getattr(admin, 'role', None) not in ["ADMIN", "SUPER_ADMIN"]:
            admin_name = getattr(admin, 'username', 'unknown') if admin else 'unknown'
            log_security_event(
                logger,
                "UNAUTHORIZED_USER_CREATION",
                f"Non-admin {admin_name} attempted to create instructor",
                severity="warning"
            )
            raise HTTPException(
                status_code=403,
                detail="Admin role required to create instructor accounts"
            )
        
        # Check if username already exists
        existing = db.query(Instructor).filter(
            Instructor.username == username
        ).first()
        
        if existing:
            log_security_event(
                logger,
                "DUPLICATE_USERNAME",
                f"Attempt to create instructor with existing username: {username}",
                severity="warning"
            )
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )
        
        # Check if email already exists (if provided)
        if email:
            existing_email = db.query(Instructor).filter(
                Instructor.email == email
            ).first()
            
            if existing_email:
                log_security_event(
                    logger,
                    "DUPLICATE_EMAIL",
                    f"Attempt to create instructor with existing email: {email}",
                    severity="warning"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
        
        # Create instructor
        # Get admin ID if available, otherwise use 0 for system admin
        admin_id = getattr(admin, 'id', 0) if admin else 0
        
        instructor = Instructor(
            username=username,
            email=email,
            display_name=display_name,
            password_hash=get_password_hash(password),
            role=role,
            role_granted_by=admin_id if admin_id != 0 else None,
            role_granted_at=datetime.utcnow() if admin else None,
            is_active=True
        )
        
        db.add(instructor)
        db.commit()
        db.refresh(instructor)

        # Auto-generate API key for the instructor
        try:
            APIKeyService.auto_generate_api_key(instructor, db)
        except Exception as e:
            logger.error(f"Failed to auto-generate API key for instructor {instructor.id}: {e}", exc_info=True)
            # Don't fail the instructor creation if API key generation fails
            # Log it but continue

        log_security_event(
            logger,
            "INSTRUCTOR_CREATED",
            f"Admin {admin.username} created instructor: {username} (role: {role})",
            severity="info"
        )

        return instructor
    
    @staticmethod
    def deactivate_instructor(
        admin: Instructor,
        target_instructor: Instructor,
        reason: str,
        db: DBSession
    ) -> Instructor:
        """
        Deactivate an instructor and cascade effects.
        
        When an instructor is deactivated:
        1. Mark instructor as inactive
        2. End all active sessions immediately
        3. Revoke all API keys
        4. Archive all classes
        
        Args:
            admin: The admin deactivating (authenticated user)
            target_instructor: Instructor to deactivate
            reason: Reason for deactivation
            db: Database session
        
        Returns:
            Updated Instructor object
        """
        from fastapi import HTTPException
        
        if admin.role not in ["ADMIN", "SUPER_ADMIN"]:
            raise HTTPException(
                status_code=403,
                detail="Admin role required"
            )
        
        if target_instructor.is_active == False:  # type: ignore
            raise HTTPException(
                status_code=400,
                detail="Instructor is already inactive"
            )
        
        # Mark as inactive
        target_instructor.is_active = False  # type: ignore
        target_instructor.deactivated_by = admin.id  # type: ignore
        target_instructor.deactivated_at = datetime.utcnow()  # type: ignore
        target_instructor.deactivation_reason = reason  # type: ignore
        
        # End all active sessions for this instructor
        from models_v2 import Class, ClassMeeting
        
        active_meetings = db.query(ClassMeeting).join(
            Class, ClassMeeting.class_id == Class.id
        ).filter(
            Class.instructor_id == target_instructor.id,
            ClassMeeting.is_active == True
        ).all()
        
        for meeting in active_meetings:
            meeting.is_active = False  # type: ignore
            meeting.ended_at = datetime.utcnow()  # type: ignore
        
        # Revoke all API keys
        api_keys = db.query(APIKey).filter(
            APIKey.instructor_id == target_instructor.id,
            APIKey.is_active == True
        ).all()
        
        for key in api_keys:
            key.is_active = False  # type: ignore
            key.revoked_by = admin.id  # type: ignore
            key.revoked_at = datetime.utcnow()  # type: ignore
            key.revocation_reason = f"Account deactivated: {reason}"  # type: ignore
        
        # Archive all classes
        classes = db.query(Class).filter(
            Class.instructor_id == target_instructor.id
        ).all()
        
        for cls in classes:
            cls.is_archived = True  # type: ignore
        
        db.commit()
        
        log_security_event(
            logger,
            "INSTRUCTOR_DEACTIVATED",
            f"Admin {admin.username} deactivated instructor {target_instructor.username}: {reason}",
            severity="warning"
        )
        
        return target_instructor
