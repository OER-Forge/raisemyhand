"""
Admin user management endpoints for creating and managing instructors.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session as DBSession
from typing import List, Optional
from pydantic import BaseModel
import secrets
import string

from database import get_db
from models_v2 import Instructor, Class, ClassMeeting, Question, Answer, APIKey
from schemas_v2 import InstructorResponse
from routes_instructor import get_current_instructor
from security import verify_role, get_password_hash
from services.user_management_service import UserManagementService
from logging_config import log_security_event, get_logger

router = APIRouter(prefix="/api/admin/instructors", tags=["admin-users"])
logger = get_logger(__name__)


class InstructorCreateRequest(BaseModel):
    """Request schema for creating instructor"""
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    password: str
    role: str = "INSTRUCTOR"


class DeactivateRequest(BaseModel):
    """Request schema for deactivating instructor"""
    reason: Optional[str] = "Administrative decision"


@router.post("/")
def create_instructor_admin(
    request: InstructorCreateRequest,
    admin = Depends(verify_role("ADMIN")),
    db: DBSession = Depends(get_db)
):
    """
    Admin creates a new instructor account.
    
    Args:
        request: Request containing username, password, email, display_name, role
        admin: Authenticated admin user
        db: Database session
    
    Returns:
        Dict with created instructor details
    
    Raises:
        403: If caller is not admin
        400: If username/email already exists or validation fails
    """
    # Validate input
    if len(request.username) < 3 or len(request.username) > 50:
        raise HTTPException(status_code=400, detail="Username must be 3-50 characters")
    
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    if request.role not in ["INSTRUCTOR", "ADMIN"]:
        raise HTTPException(status_code=400, detail="Role must be INSTRUCTOR or ADMIN")
    
    # Check if caller is admin (admin object has role attribute)
    if not hasattr(admin, 'role') or admin.role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Admin role required to create instructor accounts"
        )
    
    # Only SUPER_ADMIN can create ADMIN accounts
    if request.role == "ADMIN" and getattr(admin, 'role', None) != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only SUPER_ADMIN can create admin accounts"
        )
    
    # Create instructor using service
    instructor = UserManagementService.create_instructor(
        admin=admin,
        username=request.username,
        email=request.email,
        display_name=request.display_name,
        password=request.password,
        role=request.role,
        db=db
    )
    
    return {
        "id": instructor.id,
        "username": instructor.username,
        "email": instructor.email,
        "display_name": instructor.display_name,
        "created_at": instructor.created_at,
        "last_login": instructor.last_login,
        "is_active": instructor.is_active
    }


@router.get("/")
def list_instructors(
    active_only: bool = True,
    admin = Depends(verify_role("ADMIN")),
    db: DBSession = Depends(get_db)
):
    """
    List all instructors (with optional filtering).
    
    Args:
        active_only: Only show active instructors (default: true)
        admin: Authenticated admin user
        db: Database session
    
    Returns:
        List of instructor objects as dictionaries
    """
    query = db.query(Instructor)
    
    if active_only:
        query = query.filter(Instructor.is_active == True)
    
    instructors = query.all()
    
    return [
        {
            "id": i.id,
            "username": i.username,
            "email": i.email,
            "display_name": i.display_name,
            "created_at": i.created_at,
            "last_login": i.last_login,
            "is_active": i.is_active
        }
        for i in instructors
    ]


@router.get("/{instructor_id}")
def get_instructor_detail(
    instructor_id: int,
    admin = Depends(verify_role("ADMIN")),
    db: DBSession = Depends(get_db)
):
    """
    Get detailed information about a specific instructor.
    
    Args:
        instructor_id: ID of instructor to retrieve
        admin: Authenticated admin user
        db: Database session
    
    Returns:
        Detailed instructor object with stats and recent sessions
    """
    from models_v2 import Class, ClassMeeting
    from sqlalchemy import func
    
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    
    # Get classes for this instructor
    classes = db.query(Class).filter(Class.instructor_id == instructor_id).all()
    class_ids = [c.id for c in classes]
    
    # Get sessions for this instructor's classes
    recent_sessions = []
    if class_ids:
        sessions = db.query(ClassMeeting).filter(
            ClassMeeting.class_id.in_(class_ids)
        ).order_by(ClassMeeting.created_at.desc()).limit(10).all()
        
        for session in sessions:
            recent_sessions.append({
                "id": session.id,
                "title": session.title,
                "is_active": session.is_active,
                "created_at": session.created_at.isoformat(),
                "question_count": len(session.questions) if session.questions else 0
            })
    
    # Get statistics
    total_questions = db.query(func.count(Question.id)).join(
        ClassMeeting, Question.meeting_id == ClassMeeting.id
    ).join(
        Class, ClassMeeting.class_id == Class.id
    ).filter(Class.instructor_id == instructor_id).scalar()
    
    total_upvotes = db.query(func.sum(Question.upvote_count)).join(
        ClassMeeting, Question.meeting_id == ClassMeeting.id
    ).join(
        Class, ClassMeeting.class_id == Class.id
    ).filter(Class.instructor_id == instructor_id).scalar() or 0
    
    unique_students = db.query(func.count(Answer.student_id.distinct())).join(
        Question, Answer.question_id == Question.id
    ).join(
        ClassMeeting, Question.meeting_id == ClassMeeting.id
    ).join(
        Class, ClassMeeting.class_id == Class.id
    ).filter(Class.instructor_id == instructor_id).scalar() or 0
    
    return {
        "id": instructor.id,
        "username": instructor.username,
        "email": instructor.email,
        "display_name": instructor.display_name,
        "created_at": instructor.created_at.isoformat(),
        "last_login": instructor.last_login.isoformat() if instructor.last_login else None,
        "is_active": instructor.is_active,
        "role": instructor.role,
        "role_granted_by": instructor.role_granted_by,
        "role_granted_at": instructor.role_granted_at.isoformat() if instructor.role_granted_at else None,
        "deactivated_by": instructor.deactivated_by,
        "deactivated_at": instructor.deactivated_at.isoformat() if instructor.deactivated_at else None,
        "deactivation_reason": instructor.deactivation_reason,
        "api_keys": [
            {
                "id": key.id,
                "name": key.name,
                "is_active": key.is_active,
                "created_at": key.created_at.isoformat(),
                "last_used": key.last_used.isoformat() if key.last_used else None
            }
            for key in instructor.api_keys
        ],
        "stats": {
            "classes_count": len(classes),
            "active_sessions": len([s for s in recent_sessions if s["is_active"]]),
            "total_sessions": len(recent_sessions),
            "questions_count": total_questions or 0,
            "upvotes_count": int(total_upvotes),
            "unique_students_count": unique_students
        },
        "recent_sessions": recent_sessions
    }


@router.put("/{instructor_id}/deactivate")
def deactivate_instructor_admin(
    instructor_id: int,
    request: DeactivateRequest,
    admin = Depends(verify_role("ADMIN")),
    db: DBSession = Depends(get_db)
):
    """
    Deactivate an instructor account and cascade effects.
    
    When deactivated:
    1. Account is marked inactive (cannot login)
    2. All active sessions are ended
    3. All API keys are revoked
    4. All classes are archived
    5. Historical data remains accessible for review
    
    Args:
        instructor_id: ID of instructor to deactivate
        request: Request containing reason for deactivation
        admin: Authenticated admin user
        db: Database session
    
    Returns:
        Success message
    """
    target = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Instructor not found")
    
    # Don't allow deactivating yourself
    admin_id = getattr(admin, 'id', 0)
    if target.id == admin_id and admin_id != 0:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    UserManagementService.deactivate_instructor(
        admin=admin,
        target_instructor=target,
        reason=request.reason or "Administrative deactivation",
        db=db
    )
    
    return {
        "message": f"Instructor {target.username} has been deactivated",
        "reason": request.reason
    }


@router.put("/{instructor_id}/activate")
def reactivate_instructor_admin(
    instructor_id: int,
    admin = Depends(verify_role("ADMIN")),
    db: DBSession = Depends(get_db)
):
    """
    Reactivate a deactivated instructor account.
    
    Note: Archived classes remain archived and must be manually restored if needed.
    Revoked API keys remain revoked and must be manually recreated.
    
    Args:
        instructor_id: ID of instructor to reactivate
        admin: Authenticated admin user
        db: Database session
    
    Returns:
        Success message
    """
    target = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Instructor not found")
    
    if not target.is_active.value:  # type: ignore
        raise HTTPException(status_code=400, detail="Instructor is already active")
    
    target.is_active = True  # type: ignore
    target.deactivated_by = None  # type: ignore
    target.deactivated_at = None  # type: ignore
    target.deactivation_reason = None  # type: ignore
    
    db.commit()
    
    log_security_event(
        logger,
        "INSTRUCTOR_REACTIVATED",
        f"Admin {admin.username} reactivated instructor {target.username}",
        severity="info"
    )
    
    return {"message": f"Instructor {target.username} has been reactivated"}


@router.post("/{instructor_id}/reset-password")
def reset_instructor_password(
    instructor_id: int,
    admin = Depends(verify_role("ADMIN")),
    db: DBSession = Depends(get_db)
):
    """
    Reset an instructor's password and generate a temporary password.
    
    Args:
        instructor_id: ID of instructor whose password to reset
        admin: Authenticated admin user
        db: Database session
    
    Returns:
        Dictionary with temporary password
    """
    target = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Instructor not found")
    
    # Generate a strong temporary password
    chars = string.ascii_letters + string.digits + string.punctuation
    temp_password = ''.join(secrets.choice(chars) for i in range(16))
    
    # Update password hash
    target.password_hash = get_password_hash(temp_password)
    db.commit()
    
    log_security_event(
        logger,
        "PASSWORD_RESET",
        f"Admin {getattr(admin, 'username', 'unknown')} reset password for instructor {target.username}",
        severity="warning"
    )
    
    return {"temporary_password": temp_password}
