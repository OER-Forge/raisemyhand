"""
Admin-specific routes for instructor and system management
Requires admin JWT authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import string

from database import get_db
from models_v2 import Instructor, Class, ClassMeeting, APIKey, Question
from schemas_v2 import (
    AdminInstructorListResponse,
    AdminInstructorDetailResponse,
    InstructorResetPasswordResponse,
    BulkInstructorActionRequest,
    BulkActionResponse,
    BulkPasswordResetResponse,
    InstructorExportData
)
from security import get_password_hash, verify_jwt_token
from logging_config import get_logger, log_security_event, log_database_operation

router = APIRouter(prefix="/api/admin/instructors", tags=["admin-instructors"])
logger = get_logger(__name__)


def verify_admin(authorization: str = Header(...)) -> str:
    """Dependency to verify admin JWT token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]
    payload = verify_jwt_token(token)

    # Check if JWT verification failed
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Check if token is for admin user (not instructor)
    if payload.get("sub") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return payload.get("sub")


# ============================================================================
# Instructor List & Search
# ============================================================================

@router.get("", response_model=List[AdminInstructorListResponse])
async def list_instructors(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,  # "active", "inactive", "placeholder"
    has_login: Optional[bool] = None,
    last_login_days: Optional[int] = None,  # Filter by last login within X days
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """
    List all instructors with filtering and search.

    Filters:
    - search: Search by username, email, or display_name
    - status: "active", "inactive", "placeholder"
    - has_login: True (has logged in at least once), False (never logged in)
    - last_login_days: Show only instructors who logged in within X days
    """
    query = db.query(Instructor)

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Instructor.username.ilike(search_term)) |
            (Instructor.email.ilike(search_term)) |
            (Instructor.display_name.ilike(search_term))
        )

    # Status filter
    if status == "active":
        query = query.filter(Instructor.is_active == True, Instructor.last_login.isnot(None))
    elif status == "inactive":
        query = query.filter(Instructor.is_active == False)
    elif status == "placeholder":
        # Placeholder = created by admin API key creation, never logged in
        query = query.filter(Instructor.last_login.is_(None))

    # Has login filter
    if has_login is True:
        query = query.filter(Instructor.last_login.isnot(None))
    elif has_login is False:
        query = query.filter(Instructor.last_login.is_(None))

    # Last login days filter
    if last_login_days:
        cutoff_date = datetime.utcnow() - timedelta(days=last_login_days)
        query = query.filter(Instructor.last_login >= cutoff_date)

    # Get instructors
    instructors = query.order_by(Instructor.created_at.desc()).offset(skip).limit(limit).all()

    # Build response with stats
    results = []
    for instructor in instructors:
        # Get counts
        classes_count = db.query(func.count(Class.id)).filter(
            Class.instructor_id == instructor.id,
            Class.is_archived == False
        ).scalar()

        sessions_count = db.query(func.count(ClassMeeting.id)).join(
            Class, ClassMeeting.class_id == Class.id
        ).filter(Class.instructor_id == instructor.id).scalar()

        active_sessions_count = db.query(func.count(ClassMeeting.id)).join(
            Class, ClassMeeting.class_id == Class.id
        ).filter(
            Class.instructor_id == instructor.id,
            ClassMeeting.is_active == True
        ).scalar()

        # Determine badge type
        if instructor.last_login is None:
            badge = "placeholder"
        elif instructor.is_active:
            badge = "active"
        else:
            badge = "inactive"

        results.append(AdminInstructorListResponse(
            id=instructor.id,
            username=instructor.username,
            email=instructor.email,
            display_name=instructor.display_name,
            created_at=instructor.created_at,
            last_login=instructor.last_login,
            is_active=instructor.is_active,
            badge=badge,
            classes_count=classes_count,
            sessions_count=sessions_count,
            active_sessions_count=active_sessions_count
        ))

    return results


# ============================================================================
# Instructor Detail View
# ============================================================================

@router.get("/{instructor_id}", response_model=AdminInstructorDetailResponse)
async def get_instructor_detail(
    instructor_id: int,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """
    Get comprehensive details for a single instructor.

    Includes:
    - Account information
    - Usage statistics
    - API keys
    - Classes (with meeting counts)
    - Recent sessions
    """
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    # Get comprehensive stats
    classes_count = db.query(func.count(Class.id)).filter(
        Class.instructor_id == instructor_id,
        Class.is_archived == False
    ).scalar()

    archived_classes_count = db.query(func.count(Class.id)).filter(
        Class.instructor_id == instructor_id,
        Class.is_archived == True
    ).scalar()

    sessions_count = db.query(func.count(ClassMeeting.id)).join(
        Class, ClassMeeting.class_id == Class.id
    ).filter(Class.instructor_id == instructor_id).scalar()

    active_sessions_count = db.query(func.count(ClassMeeting.id)).join(
        Class, ClassMeeting.class_id == Class.id
    ).filter(
        Class.instructor_id == instructor_id,
        ClassMeeting.is_active == True
    ).scalar()

    # Total questions across all sessions
    questions_count = db.query(func.count(Question.id)).join(
        ClassMeeting, Question.meeting_id == ClassMeeting.id
    ).join(
        Class, ClassMeeting.class_id == Class.id
    ).filter(Class.instructor_id == instructor_id).scalar()

    # Total upvotes
    upvotes_count = db.query(func.sum(Question.upvotes)).join(
        ClassMeeting, Question.meeting_id == ClassMeeting.id
    ).join(
        Class, ClassMeeting.class_id == Class.id
    ).filter(Class.instructor_id == instructor_id).scalar() or 0

    # Unique students (by student_id in questions)
    unique_students = db.query(func.count(func.distinct(Question.student_id))).join(
        ClassMeeting, Question.meeting_id == ClassMeeting.id
    ).join(
        Class, ClassMeeting.class_id == Class.id
    ).filter(Class.instructor_id == instructor_id).scalar()

    # Get API keys
    api_keys = db.query(APIKey).filter(APIKey.instructor_id == instructor_id).all()

    # Get classes with meeting counts
    classes = db.query(Class).filter(Class.instructor_id == instructor_id).all()
    classes_list = []
    for cls in classes:
        meeting_count = db.query(func.count(ClassMeeting.id)).filter(
            ClassMeeting.class_id == cls.id
        ).scalar()
        classes_list.append({
            "id": cls.id,
            "name": cls.name,
            "description": cls.description,
            "is_archived": cls.is_archived,
            "created_at": cls.created_at,
            "meeting_count": meeting_count
        })

    # Get recent sessions (last 10)
    recent_sessions = db.query(ClassMeeting).join(
        Class, ClassMeeting.class_id == Class.id
    ).filter(
        Class.instructor_id == instructor_id
    ).order_by(ClassMeeting.created_at.desc()).limit(10).all()

    sessions_list = []
    for session in recent_sessions:
        question_count = db.query(func.count(Question.id)).filter(
            Question.meeting_id == session.id
        ).scalar()
        sessions_list.append({
            "id": session.id,
            "title": session.title,
            "meeting_code": session.meeting_code,
            "instructor_code": session.instructor_code,
            "created_at": session.created_at,
            "is_active": session.is_active,
            "question_count": question_count
        })

    return AdminInstructorDetailResponse(
        id=instructor.id,
        username=instructor.username,
        email=instructor.email,
        display_name=instructor.display_name,
        created_at=instructor.created_at,
        last_login=instructor.last_login,
        is_active=instructor.is_active,
        stats={
            "classes_count": classes_count,
            "archived_classes_count": archived_classes_count,
            "sessions_count": sessions_count,
            "active_sessions_count": active_sessions_count,
            "questions_count": questions_count,
            "upvotes_count": upvotes_count,
            "unique_students_count": unique_students
        },
        api_keys=api_keys,
        classes=classes_list,
        recent_sessions=sessions_list
    )


# ============================================================================
# Instructor Actions (Activate/Deactivate)
# ============================================================================

@router.patch("/{instructor_id}/activate")
async def activate_instructor(
    instructor_id: int,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Activate an instructor account."""
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    if instructor.is_active:
        raise HTTPException(status_code=400, detail="Instructor is already active")

    instructor.is_active = True
    db.commit()

    log_security_event(
        logger, "INSTRUCTOR_ACTIVATED",
        f"Admin activated instructor {instructor.username} (ID: {instructor_id})",
        severity="info"
    )

    return {"message": "Instructor activated successfully", "instructor_id": instructor_id}


@router.patch("/{instructor_id}/deactivate")
async def deactivate_instructor(
    instructor_id: int,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Deactivate an instructor account."""
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    if not instructor.is_active:
        raise HTTPException(status_code=400, detail="Instructor is already inactive")

    instructor.is_active = False
    db.commit()

    log_security_event(
        logger, "INSTRUCTOR_DEACTIVATED",
        f"Admin deactivated instructor {instructor.username} (ID: {instructor_id})",
        severity="warning"
    )

    return {"message": "Instructor deactivated successfully", "instructor_id": instructor_id}


# ============================================================================
# Password Reset
# ============================================================================

def generate_temporary_password(length: int = 16) -> str:
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/{instructor_id}/reset-password", response_model=InstructorResetPasswordResponse)
async def reset_instructor_password(
    instructor_id: int,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """
    Reset an instructor's password.

    Returns temporary password that admin can give to instructor.
    External systems can call this API and send password via their own email/SMS.
    """
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    # Generate temporary password
    temp_password = generate_temporary_password()

    # Hash and save
    instructor.password_hash = get_password_hash(temp_password)
    db.commit()

    log_security_event(
        logger, "PASSWORD_RESET_BY_ADMIN",
        f"Admin reset password for instructor {instructor.username} (ID: {instructor_id})",
        severity="warning"
    )

    # Return temporary password (only shown once!)
    return InstructorResetPasswordResponse(
        message="Password reset successfully",
        instructor_id=instructor_id,
        username=instructor.username,
        temporary_password=temp_password,
        must_change_on_login=True,  # Future feature
        reset_token=None  # For future email integration
    )


# ============================================================================
# Bulk Actions
# ============================================================================

@router.post("/bulk/activate", response_model=BulkActionResponse)
async def bulk_activate_instructors(
    request: BulkInstructorActionRequest,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Activate multiple instructors at once."""
    instructors = db.query(Instructor).filter(
        Instructor.id.in_(request.instructor_ids)
    ).all()

    activated_count = 0
    for instructor in instructors:
        if not instructor.is_active:
            instructor.is_active = True
            activated_count += 1

    db.commit()

    log_security_event(
        logger, "BULK_INSTRUCTOR_ACTIVATE",
        f"Admin activated {activated_count} instructors",
        severity="info"
    )

    return BulkActionResponse(
        message=f"Activated {activated_count} instructor(s)",
        successful_count=activated_count,
        failed_count=len(request.instructor_ids) - activated_count
    )


@router.post("/bulk/deactivate", response_model=BulkActionResponse)
async def bulk_deactivate_instructors(
    request: BulkInstructorActionRequest,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Deactivate multiple instructors at once."""
    instructors = db.query(Instructor).filter(
        Instructor.id.in_(request.instructor_ids)
    ).all()

    deactivated_count = 0
    for instructor in instructors:
        if instructor.is_active:
            instructor.is_active = False
            deactivated_count += 1

    db.commit()

    log_security_event(
        logger, "BULK_INSTRUCTOR_DEACTIVATE",
        f"Admin deactivated {deactivated_count} instructors",
        severity="warning"
    )

    return BulkActionResponse(
        message=f"Deactivated {deactivated_count} instructor(s)",
        successful_count=deactivated_count,
        failed_count=len(request.instructor_ids) - deactivated_count
    )


@router.post("/bulk/reset-passwords", response_model=BulkPasswordResetResponse)
async def bulk_reset_instructor_passwords(
    request: BulkInstructorActionRequest,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """
    Reset passwords for multiple instructors at once.
    Returns temporary passwords for each instructor.
    """
    instructors = db.query(Instructor).filter(
        Instructor.id.in_(request.instructor_ids)
    ).all()

    reset_results = []
    for instructor in instructors:
        # Generate temporary password
        temp_password = generate_temporary_password()
        
        # Hash and save
        instructor.password_hash = get_password_hash(temp_password)
        
        reset_results.append({
            "instructor_id": instructor.id,
            "username": instructor.username,
            "display_name": instructor.display_name,
            "temporary_password": temp_password
        })

    db.commit()

    log_security_event(
        logger, "BULK_PASSWORD_RESET",
        f"Admin reset passwords for {len(reset_results)} instructors",
        severity="warning"
    )

    return {
        "message": f"Reset passwords for {len(reset_results)} instructor(s)",
        "successful_count": len(reset_results),
        "failed_count": 0,
        "reset_results": reset_results
    }


@router.get("/export", response_model=List[InstructorExportData])
async def export_instructors_data(
    format: str = "json",  # json, csv
    include_stats: bool = True,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """
    Export instructor data for reporting and analysis.
    
    Formats:
    - json: Structured JSON export
    - csv: CSV format for spreadsheets
    """
    # Get all instructors with stats
    instructors = db.query(Instructor).order_by(Instructor.created_at.desc()).all()
    
    export_data = []
    for instructor in instructors:
        # Get stats if requested
        stats_data = None
        if include_stats:
            classes_count = db.query(func.count(Class.id)).filter(
                Class.instructor_id == instructor.id,
                Class.is_archived == False
            ).scalar()

            sessions_count = db.query(func.count(ClassMeeting.id)).join(
                Class, ClassMeeting.class_id == Class.id
            ).filter(Class.instructor_id == instructor.id).scalar()

            questions_count = db.query(func.count(Question.id)).join(
                ClassMeeting, Question.meeting_id == ClassMeeting.id
            ).join(
                Class, ClassMeeting.class_id == Class.id
            ).filter(Class.instructor_id == instructor.id).scalar()

            upvotes_count = db.query(func.sum(Question.upvotes)).join(
                ClassMeeting, Question.meeting_id == ClassMeeting.id
            ).join(
                Class, ClassMeeting.class_id == Class.id
            ).filter(Class.instructor_id == instructor.id).scalar() or 0

            unique_students = db.query(func.count(func.distinct(Question.student_id))).join(
                ClassMeeting, Question.meeting_id == ClassMeeting.id
            ).join(
                Class, ClassMeeting.class_id == Class.id
            ).filter(Class.instructor_id == instructor.id).scalar()

            stats_data = {
                "classes_count": classes_count,
                "sessions_count": sessions_count,
                "questions_count": questions_count,
                "upvotes_count": upvotes_count,
                "unique_students_count": unique_students
            }

        export_data.append({
            "id": instructor.id,
            "username": instructor.username,
            "email": instructor.email,
            "display_name": instructor.display_name,
            "created_at": instructor.created_at,
            "last_login": instructor.last_login,
            "is_active": instructor.is_active,
            "badge": "placeholder" if instructor.last_login is None else ("active" if instructor.is_active else "inactive"),
            "stats": stats_data
        })
    
    log_database_operation(
        logger, "INSTRUCTOR_DATA_EXPORT",
        f"Admin exported data for {len(export_data)} instructors (format: {format})"
    )
    
    return export_data


@router.delete("/bulk/delete", response_model=BulkActionResponse)
async def bulk_delete_instructors(
    request: BulkInstructorActionRequest,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """
    Delete multiple instructors at once.

    WARNING: This cascades to delete classes, sessions, and questions.
    Use with extreme caution.
    """
    # Get instructors
    instructors = db.query(Instructor).filter(
        Instructor.id.in_(request.instructor_ids)
    ).all()

    deleted_count = len(instructors)

    # Delete (CASCADE will handle related data)
    for instructor in instructors:
        db.delete(instructor)

    db.commit()

    log_security_event(
        logger, "BULK_INSTRUCTOR_DELETE",
        f"Admin deleted {deleted_count} instructors (CASCADE)",
        severity="critical"
    )

    return BulkActionResponse(
        message=f"Deleted {deleted_count} instructor(s) and all related data",
        successful_count=deleted_count,
        failed_count=0
    )
