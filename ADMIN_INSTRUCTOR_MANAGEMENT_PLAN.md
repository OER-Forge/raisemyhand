# Admin Instructor Management - Implementation Plan

**Version:** 1.0
**Date:** 2025-12-05
**Estimated Duration:** 2.5-3 weeks (17-21 days)
**Priority:** Tier 1 🔴

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Phase 1: Backend Foundation](#phase-1-backend-foundation)
4. [Phase 2: Tab Navigation Refactor](#phase-2-tab-navigation-refactor)
5. [Phase 3: Instructor List + Filtering](#phase-3-instructor-list--filtering)
6. [Phase 4: Quick View Modal](#phase-4-quick-view-modal)
7. [Phase 5: Full Details Page](#phase-5-full-details-page)
8. [Phase 6: Bulk Actions](#phase-6-bulk-actions)
9. [Phase 7: Accessibility Polish](#phase-7-accessibility-polish)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Checklist](#deployment-checklist)

---

## Overview

### Goals
- Give admin full visibility into instructor accounts (registered + placeholder)
- Enable instructor account management (activate/deactivate, password reset)
- Display comprehensive usage statistics per instructor
- Maintain consistency with existing design patterns
- Ensure WCAG AA accessibility compliance

### Current State
- Instructors CAN register and login (`/api/instructors/register`, `/api/instructors/login`)
- Instructors CAN manage their own API keys
- Admin CAN view/manage sessions and API keys
- Admin CANNOT see or manage instructor accounts

### New Capabilities
- View all instructors (list + detail views)
- Search and filter instructors
- Activate/deactivate instructor accounts
- Reset instructor passwords (API-friendly for external systems)
- View instructor statistics (classes, sessions, questions, students)
- Bulk operations (activate/deactivate/delete)

---

## Architecture Decisions

### 1. Password Reset Strategy
**Decision:** Option A with API flexibility

```python
# Admin triggers reset → API returns temporary password
POST /api/admin/instructors/{id}/reset-password
Response: {
    "message": "Password reset successfully",
    "temporary_password": "TempPass123!",
    "must_change_on_login": true,
    "reset_token": "abc123..."  # For future email integration
}
```

- Admin can copy password manually OR
- External system can call API and send via email/SMS
- Future: Add optional email service without breaking API

### 2. Navigation Structure
**Decision:** Tab-based navigation

```
Admin Dashboard
├─ Tab: Overview (System Stats)
├─ Tab: Instructors (NEW)
├─ Tab: API Keys
└─ Tab: Sessions
```

- **Desktop:** Horizontal tabs
- **Mobile:** Dropdown/accordion tabs
- **Accessibility:** ARIA tabs pattern with keyboard navigation

### 3. Instructor Display Strategy
**Decision:** Show all instructors with clear badges

- **Registered:** User created account via `/api/instructors/register`
- **Placeholder:** Created when admin makes API key (legacy flow)

Badge styles:
- 🟢 `[Active - Registered]` - Real instructor, active account
- 🟡 `[Placeholder]` - Created by admin API key creation, no login yet
- 🔴 `[Inactive]` - Deactivated account

### 4. Detail View Pattern
**Decision:** Modal + Full Page hybrid

- **Quick View (Modal):** Essential info + common actions (80% use case)
- **Full Details (Page):** Comprehensive stats + related data (20% use case)
- Both mobile-responsive with proper touch targets

### 5. Statistics Organization
**Progressive disclosure:**

| View          | Data Shown                                    |
|---------------|-----------------------------------------------|
| List Table    | Name, Status, Classes, Sessions, Last Login  |
| Quick Modal   | Account info + 3-6 key stats + quick actions |
| Full Page     | All stats + related tables (API keys, classes, sessions) |

---

## Phase 1: Backend Foundation

**Duration:** 3-4 days
**Goal:** Create API endpoints and database queries for instructor management

### 1.1 New API Endpoints

#### File: `routes_admin.py` (NEW FILE)

```python
"""
Admin-specific routes for instructor and system management
Requires admin JWT authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
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
    AdminInstructorStatsResponse,
    InstructorActivateRequest,
    InstructorResetPasswordResponse,
    BulkInstructorActionRequest,
    BulkActionResponse
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

        results.append({
            "id": instructor.id,
            "username": instructor.username,
            "email": instructor.email,
            "display_name": instructor.display_name,
            "created_at": instructor.created_at,
            "last_login": instructor.last_login,
            "is_active": instructor.is_active,
            "badge": badge,
            "classes_count": classes_count,
            "sessions_count": sessions_count,
            "active_sessions_count": active_sessions_count
        })

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

    return {
        "id": instructor.id,
        "username": instructor.username,
        "email": instructor.email,
        "display_name": instructor.display_name,
        "created_at": instructor.created_at,
        "last_login": instructor.last_login,
        "is_active": instructor.is_active,
        "stats": {
            "classes_count": classes_count,
            "archived_classes_count": archived_classes_count,
            "sessions_count": sessions_count,
            "active_sessions_count": active_sessions_count,
            "questions_count": questions_count,
            "upvotes_count": upvotes_count,
            "unique_students_count": unique_students
        },
        "api_keys": api_keys,
        "classes": classes_list,
        "recent_sessions": sessions_list
    }


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
    return {
        "message": "Password reset successfully",
        "instructor_id": instructor_id,
        "username": instructor.username,
        "temporary_password": temp_password,
        "must_change_on_login": True,  # Future feature
        "reset_token": None  # For future email integration
    }


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

    return {
        "message": f"Activated {activated_count} instructor(s)",
        "successful_count": activated_count,
        "failed_count": len(request.instructor_ids) - activated_count
    }


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

    return {
        "message": f"Deactivated {deactivated_count} instructor(s)",
        "successful_count": deactivated_count,
        "failed_count": len(request.instructor_ids) - deactivated_count
    }


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

    return {
        "message": f"Deleted {deleted_count} instructor(s) and all related data",
        "successful_count": deleted_count,
        "failed_count": 0
    }
```

### 1.2 New Pydantic Schemas

#### File: `schemas_v2.py` (APPEND)

```python
# ============================================================================
# Admin Instructor Management Schemas
# ============================================================================

class AdminInstructorListResponse(BaseModel):
    """Instructor list item for admin view."""
    id: int
    username: str
    email: Optional[str]
    display_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    badge: str  # "active", "inactive", "placeholder"
    classes_count: int
    sessions_count: int
    active_sessions_count: int

    class Config:
        from_attributes = True


class InstructorStatsDetail(BaseModel):
    """Detailed statistics for an instructor."""
    classes_count: int
    archived_classes_count: int
    sessions_count: int
    active_sessions_count: int
    questions_count: int
    upvotes_count: int
    unique_students_count: int


class InstructorClassInfo(BaseModel):
    """Class information for instructor detail view."""
    id: int
    name: str
    description: Optional[str]
    is_archived: bool
    created_at: datetime
    meeting_count: int


class InstructorSessionInfo(BaseModel):
    """Session information for instructor detail view."""
    id: int
    title: str
    meeting_code: str
    instructor_code: str
    created_at: datetime
    is_active: bool
    question_count: int


class AdminInstructorDetailResponse(BaseModel):
    """Comprehensive instructor details for admin."""
    id: int
    username: str
    email: Optional[str]
    display_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    stats: InstructorStatsDetail
    api_keys: List[APIKeyResponse]
    classes: List[InstructorClassInfo]
    recent_sessions: List[InstructorSessionInfo]

    class Config:
        from_attributes = True


class InstructorResetPasswordResponse(BaseModel):
    """Response from password reset (includes temporary password)."""
    message: str
    instructor_id: int
    username: str
    temporary_password: str
    must_change_on_login: bool
    reset_token: Optional[str]  # For future email integration


class BulkInstructorActionRequest(BaseModel):
    """Request to perform bulk action on instructors."""
    instructor_ids: List[int] = Field(..., min_items=1, max_items=100)


class BulkActionResponse(BaseModel):
    """Response from bulk action."""
    message: str
    successful_count: int
    failed_count: int
```

### 1.3 Update Main Application

#### File: `main.py` (MODIFY)

```python
# Add import at top
from routes_admin import router as admin_router

# Include router with other routers
app.include_router(admin_router)
```

### 1.4 Testing Endpoints

Create test file: `tests/test_admin_instructors.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_instructors_requires_auth():
    """Test that listing instructors requires admin auth."""
    response = client.get("/api/admin/instructors")
    assert response.status_code == 401

def test_list_instructors_with_auth(admin_token):
    """Test listing instructors with valid admin token."""
    response = client.get(
        "/api/admin/instructors",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_search_instructors(admin_token):
    """Test search functionality."""
    response = client.get(
        "/api/admin/instructors?search=john",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

def test_get_instructor_detail(admin_token, test_instructor_id):
    """Test getting instructor details."""
    response = client.get(
        f"/api/admin/instructors/{test_instructor_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "api_keys" in data
    assert "classes" in data

def test_reset_password(admin_token, test_instructor_id):
    """Test password reset returns temporary password."""
    response = client.post(
        f"/api/admin/instructors/{test_instructor_id}/reset-password",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "temporary_password" in data
    assert len(data["temporary_password"]) >= 16

def test_bulk_deactivate(admin_token, test_instructor_ids):
    """Test bulk deactivation."""
    response = client.post(
        "/api/admin/instructors/bulk/deactivate",
        json={"instructor_ids": test_instructor_ids},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["successful_count"] >= 1
```

---

## Phase 2: Tab Navigation Refactor

**Duration:** 2 days
**Goal:** Refactor admin dashboard to use tab-based navigation

### 2.1 Update Admin HTML Template

#### File: `templates/admin.html` (MAJOR REFACTOR)

**Strategy:** Keep existing content, wrap in tabs

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RaiseMyHand - Admin Dashboard</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <style>
        /* Tab Navigation Styles */
        .tab-navigation {
            background: var(--card-bg);
            border-bottom: 2px solid var(--border-color);
            margin-bottom: 30px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow);
        }

        .tab-list {
            display: flex;
            list-style: none;
            margin: 0;
            padding: 0;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }

        .tab-list li {
            flex-shrink: 0;
        }

        .tab-button {
            display: block;
            padding: 15px 25px;
            border: none;
            background: none;
            color: var(--text-secondary);
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            border-bottom: 3px solid transparent;
            white-space: nowrap;
            min-width: 44px; /* Touch target */
            min-height: 44px;
        }

        .tab-button:hover {
            color: var(--primary-color);
            background: rgba(74, 144, 226, 0.05);
        }

        .tab-button:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: -2px;
        }

        .tab-button[aria-selected="true"] {
            color: var(--primary-color);
            border-bottom-color: var(--primary-color);
            font-weight: 600;
        }

        .tab-panel {
            display: none;
            animation: fadeIn 0.3s ease;
        }

        .tab-panel[aria-hidden="false"] {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Mobile: Dropdown style tabs */
        @media (max-width: 768px) {
            .tab-list {
                flex-direction: column;
            }

            .tab-button {
                width: 100%;
                text-align: left;
                padding: 12px 20px;
                border-bottom: 1px solid var(--border-color);
            }

            .tab-button[aria-selected="true"] {
                background: rgba(74, 144, 226, 0.1);
                border-left: 3px solid var(--primary-color);
                border-bottom: 1px solid var(--border-color);
            }
        }

        /* Keep existing styles from original admin.html */
        .stats-grid { /* ... existing ... */ }
        .stat-card { /* ... existing ... */ }
        /* ... all other existing styles ... */
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <div>
                    <h1>🔧 RaiseMyHand - Admin Dashboard</h1>
                    <p class="subtitle">System overview and management</p>
                </div>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- Tab Navigation -->
        <nav class="tab-navigation" role="tablist" aria-label="Admin dashboard sections">
            <ul class="tab-list">
                <li role="presentation">
                    <button
                        role="tab"
                        id="tab-overview"
                        class="tab-button"
                        aria-selected="true"
                        aria-controls="panel-overview"
                        tabindex="0"
                        onclick="switchTab('overview')">
                        📊 Overview
                    </button>
                </li>
                <li role="presentation">
                    <button
                        role="tab"
                        id="tab-instructors"
                        class="tab-button"
                        aria-selected="false"
                        aria-controls="panel-instructors"
                        tabindex="-1"
                        onclick="switchTab('instructors')">
                        👥 Instructors
                    </button>
                </li>
                <li role="presentation">
                    <button
                        role="tab"
                        id="tab-api-keys"
                        class="tab-button"
                        aria-selected="false"
                        aria-controls="panel-api-keys"
                        tabindex="-1"
                        onclick="switchTab('api-keys')">
                        🔑 API Keys
                    </button>
                </li>
                <li role="presentation">
                    <button
                        role="tab"
                        id="tab-sessions"
                        class="tab-button"
                        aria-selected="false"
                        aria-controls="panel-sessions"
                        tabindex="-1"
                        onclick="switchTab('sessions')">
                        📝 Sessions
                    </button>
                </li>
            </ul>
        </nav>

        <!-- Tab Panel: Overview -->
        <div
            role="tabpanel"
            id="panel-overview"
            class="tab-panel"
            aria-labelledby="tab-overview"
            aria-hidden="false">

            <h2>System Statistics</h2>
            <div class="stats-grid" id="stats-grid">
                <!-- Existing stats cards from original admin.html -->
                <div class="stat-card">
                    <div class="stat-label">Total Sessions</div>
                    <div class="stat-value" id="total-sessions">-</div>
                </div>
                <!-- ... rest of existing stats cards ... -->
            </div>
        </div>

        <!-- Tab Panel: Instructors (NEW) -->
        <div
            role="tabpanel"
            id="panel-instructors"
            class="tab-panel"
            aria-labelledby="tab-instructors"
            aria-hidden="true">

            <!-- PLACEHOLDER: Will be filled in Phase 3 -->
            <h2>Instructor Management</h2>
            <p style="text-align: center; padding: 60px 20px; color: #666;">
                Loading instructor management interface...
            </p>
        </div>

        <!-- Tab Panel: API Keys -->
        <div
            role="tabpanel"
            id="panel-api-keys"
            class="tab-panel"
            aria-labelledby="tab-api-keys"
            aria-hidden="true">

            <div class="section-header">
                <h2>Instructor API Keys</h2>
                <button class="btn btn-primary" onclick="showCreateApiKeyModal()">
                    ➕ Create New API Key
                </button>
            </div>

            <!-- Existing API key table from original admin.html -->
            <div class="sessions-table" style="margin-bottom: 40px;">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Key</th>
                            <th>Created</th>
                            <th>Last Used</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="api-keys-tbody">
                        <tr>
                            <td colspan="6" style="text-align: center; padding: 40px;">
                                Loading...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Tab Panel: Sessions -->
        <div
            role="tabpanel"
            id="panel-sessions"
            class="tab-panel"
            aria-labelledby="tab-sessions"
            aria-hidden="true">

            <div class="section-header">
                <h2>All Sessions</h2>
                <div class="filters">
                    <label>
                        <input type="checkbox" id="active-only"> Active only
                    </label>
                    <button class="btn btn-secondary" onclick="refreshSessions()">
                        🔄 Refresh
                    </button>
                </div>
            </div>

            <!-- Existing bulk actions and sessions table -->
            <!-- ... rest of existing sessions content ... -->
        </div>
    </div>

    <!-- Existing modals (API key creation, etc.) -->
    <!-- ... -->

    <script src="/static/js/shared.js"></script>
    <script src="/static/js/admin.js"></script>
    <script>
        // Tab navigation logic
        function switchTab(tabName) {
            // Hide all panels
            document.querySelectorAll('.tab-panel').forEach(panel => {
                panel.setAttribute('aria-hidden', 'true');
            });

            // Deselect all tabs
            document.querySelectorAll('.tab-button').forEach(button => {
                button.setAttribute('aria-selected', 'false');
                button.setAttribute('tabindex', '-1');
            });

            // Show selected panel
            const panel = document.getElementById(`panel-${tabName}`);
            panel.setAttribute('aria-hidden', 'false');

            // Select active tab
            const tab = document.getElementById(`tab-${tabName}`);
            tab.setAttribute('aria-selected', 'true');
            tab.setAttribute('tabindex', '0');
            tab.focus(); // Move focus for screen readers

            // Load data for the selected tab
            if (tabName === 'overview') {
                loadStats();
            } else if (tabName === 'instructors') {
                loadInstructors(); // Will implement in Phase 3
            } else if (tabName === 'api-keys') {
                loadApiKeys();
            } else if (tabName === 'sessions') {
                loadSessions();
            }
        }

        // Keyboard navigation for tabs
        document.addEventListener('keydown', function(e) {
            const tabs = Array.from(document.querySelectorAll('.tab-button'));
            const currentTab = document.activeElement;

            if (!tabs.includes(currentTab)) return;

            const currentIndex = tabs.indexOf(currentTab);
            let nextIndex;

            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                e.preventDefault();
                nextIndex = (currentIndex + 1) % tabs.length;
                tabs[nextIndex].focus();
            } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                e.preventDefault();
                nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
                tabs[nextIndex].focus();
            } else if (e.key === 'Home') {
                e.preventDefault();
                tabs[0].focus();
            } else if (e.key === 'End') {
                e.preventDefault();
                tabs[tabs.length - 1].focus();
            } else if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                currentTab.click();
            }
        });

        // Initialize: Load overview on page load
        window.addEventListener('load', function() {
            switchTab('overview');
        });
    </script>
</body>
</html>
```

### 2.2 Update Admin JS

#### File: `static/js/admin.js` (MODIFY)

Add placeholder function for Phase 3:

```javascript
// Instructor management functions (PLACEHOLDER for Phase 3)
async function loadInstructors() {
    console.log('Loading instructors... (Phase 3)');
    // Will implement in Phase 3
}
```

### 2.3 Accessibility Testing for Tabs

**Checklist:**
- [ ] Tab key navigates through tab buttons
- [ ] Arrow keys navigate between tabs (Left/Right, Up/Down)
- [ ] Home/End keys jump to first/last tab
- [ ] Enter/Space activates focused tab
- [ ] Screen reader announces "X of Y tabs"
- [ ] Screen reader announces tab panel content when switched
- [ ] Focus visible on keyboard navigation
- [ ] Color contrast meets WCAG AA (4.5:1 for text)
- [ ] Touch targets are 44x44px minimum
- [ ] Works without JavaScript (progressive enhancement)

---

## Phase 3: Instructor List + Filtering

**Duration:** 3 days
**Goal:** Build instructor list table with search, filters, and bulk selection

### 3.1 HTML Structure

#### File: `templates/admin.html` (UPDATE `panel-instructors`)

Replace placeholder content with:

```html
<div
    role="tabpanel"
    id="panel-instructors"
    class="tab-panel"
    aria-labelledby="tab-instructors"
    aria-hidden="true">

    <!-- Header -->
    <div class="section-header">
        <h2>Instructor Management</h2>
        <div class="button-group">
            <button
                class="btn btn-secondary"
                onclick="refreshInstructors()"
                aria-label="Refresh instructor list">
                🔄 Refresh
            </button>
        </div>
    </div>

    <!-- Search and Filters -->
    <div class="filters-container" style="background: var(--card-bg); padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: var(--shadow);">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
            <!-- Search -->
            <div class="form-group" style="margin: 0;">
                <label for="instructor-search">Search</label>
                <input
                    type="text"
                    id="instructor-search"
                    placeholder="Username, email, or name..."
                    aria-label="Search instructors by username, email, or name"
                    style="width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 4px;"
                    onkeyup="debouncedSearchInstructors()">
            </div>

            <!-- Status Filter -->
            <div class="form-group" style="margin: 0;">
                <label for="instructor-status-filter">Status</label>
                <select
                    id="instructor-status-filter"
                    aria-label="Filter by instructor status"
                    style="width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 4px;"
                    onchange="filterInstructors()">
                    <option value="">All Statuses</option>
                    <option value="active">Active (Registered)</option>
                    <option value="inactive">Inactive</option>
                    <option value="placeholder">Placeholder (No Login)</option>
                </select>
            </div>

            <!-- Login Filter -->
            <div class="form-group" style="margin: 0;">
                <label for="instructor-login-filter">Login Activity</label>
                <select
                    id="instructor-login-filter"
                    aria-label="Filter by login activity"
                    style="width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 4px;"
                    onchange="filterInstructors()">
                    <option value="">All</option>
                    <option value="7">Last 7 days</option>
                    <option value="30">Last 30 days</option>
                    <option value="90">Last 90 days</option>
                    <option value="never">Never logged in</option>
                </select>
            </div>
        </div>

        <!-- Clear Filters -->
        <div style="margin-top: 15px;">
            <button
                class="btn btn-secondary"
                onclick="clearInstructorFilters()"
                style="padding: 8px 16px; font-size: 0.9rem;">
                Clear Filters
            </button>
            <span id="instructor-count" style="margin-left: 15px; color: var(--text-secondary);">
                Loading...
            </span>
        </div>
    </div>

    <!-- Bulk Actions -->
    <div
        class="bulk-actions"
        style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
        <strong>Bulk Actions:</strong>
        <button
            class="btn btn-success"
            onclick="bulkActivateInstructors()"
            aria-label="Activate selected instructors"
            style="min-width: 44px; min-height: 44px;">
            ✅ Activate Selected
        </button>
        <button
            class="btn btn-secondary"
            onclick="bulkDeactivateInstructors()"
            aria-label="Deactivate selected instructors"
            style="min-width: 44px; min-height: 44px;">
            🚫 Deactivate Selected
        </button>
        <button
            class="btn btn-danger"
            onclick="bulkDeleteInstructors()"
            aria-label="Delete selected instructors"
            style="min-width: 44px; min-height: 44px;">
            🗑️ Delete Selected
        </button>
    </div>

    <!-- Instructors Table -->
    <div class="sessions-table">
        <table role="table" aria-label="Instructors list">
            <thead>
                <tr>
                    <th scope="col">
                        <input
                            type="checkbox"
                            id="select-all-instructors"
                            onchange="toggleSelectAllInstructors()"
                            aria-label="Select all instructors"
                            style="width: 20px; height: 20px; cursor: pointer;">
                    </th>
                    <th scope="col">Name</th>
                    <th scope="col">Status</th>
                    <th scope="col">Classes</th>
                    <th scope="col">Sessions</th>
                    <th scope="col">Last Login</th>
                    <th scope="col">Actions</th>
                </tr>
            </thead>
            <tbody id="instructors-tbody">
                <tr>
                    <td colspan="7" style="text-align: center; padding: 40px;">
                        <div class="spinner" style="margin: 0 auto 10px;"></div>
                        Loading instructors...
                    </td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Pagination (if needed) -->
    <div id="instructor-pagination" style="margin-top: 20px; text-align: center;">
        <!-- Will add pagination if more than 100 instructors -->
    </div>
</div>
```

### 3.2 JavaScript Implementation

#### File: `static/js/admin.js` (ADD)

```javascript
// ============================================================================
// Instructor Management Functions
// ============================================================================

let currentInstructors = []; // Cache for filtering
let searchDebounceTimer = null;

/**
 * Load instructors from API with current filters
 */
async function loadInstructors() {
    const search = document.getElementById('instructor-search')?.value || '';
    const status = document.getElementById('instructor-status-filter')?.value || '';
    const loginFilter = document.getElementById('instructor-login-filter')?.value || '';

    const tbody = document.getElementById('instructors-tbody');

    // Build query parameters
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status) params.append('status', status);

    if (loginFilter === 'never') {
        params.append('has_login', 'false');
    } else if (loginFilter && loginFilter !== 'never') {
        params.append('last_login_days', loginFilter);
    }

    try {
        const response = await fetch(`/api/admin/instructors?${params}`, {
            headers: getAuthHeaders()
        });

        if (handleAuthError(response)) return;
        if (!response.ok) throw new Error('Failed to load instructors');

        const instructors = await response.json();
        currentInstructors = instructors;

        renderInstructorsTable(instructors);
        updateInstructorCount(instructors.length);
    } catch (error) {
        console.error('Error loading instructors:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #dc3545;">
                    Error loading instructors. Please try again.
                </td>
            </tr>
        `;
        showNotification('Failed to load instructors', 'error');
    }
}

/**
 * Render instructors table
 */
function renderInstructorsTable(instructors) {
    const tbody = document.getElementById('instructors-tbody');

    if (instructors.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #666;">
                    No instructors found. Try adjusting your filters.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = instructors.map(instructor => {
        // Format last login
        let lastLoginText = 'Never';
        if (instructor.last_login) {
            const loginDate = new Date(instructor.last_login);
            const daysAgo = Math.floor((new Date() - loginDate) / (1000 * 60 * 60 * 24));
            if (daysAgo === 0) {
                lastLoginText = 'Today';
            } else if (daysAgo === 1) {
                lastLoginText = 'Yesterday';
            } else if (daysAgo < 7) {
                lastLoginText = `${daysAgo} days ago`;
            } else {
                lastLoginText = loginDate.toLocaleDateString();
            }
        }

        // Badge styling based on status
        let badgeClass, badgeText, badgeIcon;
        if (instructor.badge === 'active') {
            badgeClass = 'badge-active';
            badgeText = 'Active';
            badgeIcon = '🟢';
        } else if (instructor.badge === 'inactive') {
            badgeClass = 'badge-ended';
            badgeText = 'Inactive';
            badgeIcon = '🔴';
        } else if (instructor.badge === 'placeholder') {
            badgeClass = 'badge-placeholder';
            badgeText = 'Placeholder';
            badgeIcon = '🟡';
        }

        return `
            <tr>
                <td>
                    <input
                        type="checkbox"
                        class="instructor-checkbox"
                        value="${instructor.id}"
                        aria-label="Select ${escapeHtml(instructor.display_name || instructor.username)}"
                        style="width: 20px; height: 20px; cursor: pointer;">
                </td>
                <td>
                    <div>
                        <strong style="display: block;">${escapeHtml(instructor.display_name || instructor.username)}</strong>
                        <small style="color: #666;">@${escapeHtml(instructor.username)}</small>
                        ${instructor.email ? `<br><small style="color: #666;">${escapeHtml(instructor.email)}</small>` : ''}
                    </div>
                </td>
                <td>
                    <span class="badge ${badgeClass}" role="status">
                        ${badgeIcon} ${badgeText}
                    </span>
                </td>
                <td style="text-align: center;">${instructor.classes_count}</td>
                <td style="text-align: center;">
                    ${instructor.sessions_count}
                    ${instructor.active_sessions_count > 0 ?
                        `<small style="color: var(--success-color);">(${instructor.active_sessions_count} active)</small>`
                        : ''}
                </td>
                <td>${lastLoginText}</td>
                <td>
                    <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                        <button
                            class="btn-view"
                            onclick="showInstructorQuickView(${instructor.id})"
                            aria-label="View details for ${escapeHtml(instructor.display_name || instructor.username)}"
                            style="min-width: 44px; min-height: 44px;">
                            👁️ View
                        </button>
                        ${instructor.is_active ? `
                        <button
                            class="btn-secondary"
                            onclick="deactivateInstructor(${instructor.id}, '${escapeHtml(instructor.username)}')"
                            aria-label="Deactivate ${escapeHtml(instructor.username)}"
                            style="min-width: 44px; min-height: 44px; padding: 6px 12px; font-size: 0.85rem;">
                            🚫 Deactivate
                        </button>
                        ` : `
                        <button
                            class="btn-success"
                            onclick="activateInstructor(${instructor.id}, '${escapeHtml(instructor.username)}')"
                            aria-label="Activate ${escapeHtml(instructor.username)}"
                            style="min-width: 44px; min-height: 44px; padding: 6px 12px; font-size: 0.85rem;">
                            ✅ Activate
                        </button>
                        `}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Update instructor count display
 */
function updateInstructorCount(count) {
    const countEl = document.getElementById('instructor-count');
    if (countEl) {
        countEl.textContent = `Showing ${count} instructor${count !== 1 ? 's' : ''}`;
    }
}

/**
 * Debounced search (wait for user to stop typing)
 */
function debouncedSearchInstructors() {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        loadInstructors();
    }, 500); // Wait 500ms after last keystroke
}

/**
 * Apply filters
 */
function filterInstructors() {
    loadInstructors();
}

/**
 * Clear all filters
 */
function clearInstructorFilters() {
    document.getElementById('instructor-search').value = '';
    document.getElementById('instructor-status-filter').value = '';
    document.getElementById('instructor-login-filter').value = '';
    loadInstructors();
}

/**
 * Refresh instructors list
 */
function refreshInstructors() {
    loadInstructors();
    showNotification('Instructor list refreshed', 'success');
}

/**
 * Toggle select all checkboxes
 */
function toggleSelectAllInstructors() {
    const selectAll = document.getElementById('select-all-instructors');
    const checkboxes = document.querySelectorAll('.instructor-checkbox');
    checkboxes.forEach(cb => cb.checked = selectAll.checked);
}

/**
 * Get selected instructor IDs
 */
function getSelectedInstructorIds() {
    const checkboxes = document.querySelectorAll('.instructor-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

/**
 * Activate single instructor
 */
async function activateInstructor(instructorId, username) {
    if (!confirm(`Activate instructor "${username}"?\n\nThey will be able to login and create sessions.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/instructors/${instructorId}/activate`, {
            method: 'PATCH',
            headers: getAuthHeaders()
        });

        if (!response.ok) throw new Error('Failed to activate instructor');

        showNotification(`Instructor "${username}" activated successfully`, 'success');
        await loadInstructors();
    } catch (error) {
        console.error('Error activating instructor:', error);
        showNotification('Failed to activate instructor', 'error');
    }
}

/**
 * Deactivate single instructor
 */
async function deactivateInstructor(instructorId, username) {
    if (!confirm(`Deactivate instructor "${username}"?\n\nThey will no longer be able to login or create sessions.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/instructors/${instructorId}/deactivate`, {
            method: 'PATCH',
            headers: getAuthHeaders()
        });

        if (!response.ok) throw new Error('Failed to deactivate instructor');

        showNotification(`Instructor "${username}" deactivated successfully`, 'success');
        await loadInstructors();
    } catch (error) {
        console.error('Error deactivating instructor:', error);
        showNotification('Failed to deactivate instructor', 'error');
    }
}

// ============================================================================
// Bulk Operations
// ============================================================================

/**
 * Bulk activate instructors
 */
async function bulkActivateInstructors() {
    const instructorIds = getSelectedInstructorIds();
    if (instructorIds.length === 0) {
        showNotification('Please select at least one instructor', 'error');
        return;
    }

    if (!confirm(`Activate ${instructorIds.length} instructor(s)?`)) {
        return;
    }

    try {
        const response = await fetch('/api/admin/instructors/bulk/activate', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ instructor_ids: instructorIds })
        });

        if (!response.ok) throw new Error('Failed to activate instructors');

        const result = await response.json();
        showNotification(result.message, 'success');
        await loadInstructors();

        // Uncheck select all
        document.getElementById('select-all-instructors').checked = false;
    } catch (error) {
        console.error('Error activating instructors:', error);
        showNotification('Failed to activate instructors', 'error');
    }
}

/**
 * Bulk deactivate instructors
 */
async function bulkDeactivateInstructors() {
    const instructorIds = getSelectedInstructorIds();
    if (instructorIds.length === 0) {
        showNotification('Please select at least one instructor', 'error');
        return;
    }

    if (!confirm(`Deactivate ${instructorIds.length} instructor(s)?\n\nThey will no longer be able to login.`)) {
        return;
    }

    try {
        const response = await fetch('/api/admin/instructors/bulk/deactivate', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ instructor_ids: instructorIds })
        });

        if (!response.ok) throw new Error('Failed to deactivate instructors');

        const result = await response.json();
        showNotification(result.message, 'success');
        await loadInstructors();

        document.getElementById('select-all-instructors').checked = false;
    } catch (error) {
        console.error('Error deactivating instructors:', error);
        showNotification('Failed to deactivate instructors', 'error');
    }
}

/**
 * Bulk delete instructors
 */
async function bulkDeleteInstructors() {
    const instructorIds = getSelectedInstructorIds();
    if (instructorIds.length === 0) {
        showNotification('Please select at least one instructor', 'error');
        return;
    }

    const confirmMsg = `⚠️ DELETE ${instructorIds.length} instructor(s)?\n\n` +
                      `This will PERMANENTLY DELETE:\n` +
                      `- Instructor accounts\n` +
                      `- All their classes\n` +
                      `- All their sessions\n` +
                      `- All questions in those sessions\n\n` +
                      `THIS CANNOT BE UNDONE!\n\n` +
                      `Type "DELETE" to confirm:`;

    const confirmation = prompt(confirmMsg);
    if (confirmation !== 'DELETE') {
        showNotification('Deletion cancelled', 'info');
        return;
    }

    try {
        const response = await fetch('/api/admin/instructors/bulk/delete', {
            method: 'DELETE',
            headers: getAuthHeaders(),
            body: JSON.stringify({ instructor_ids: instructorIds })
        });

        if (!response.ok) throw new Error('Failed to delete instructors');

        const result = await response.json();
        showNotification(result.message, 'success');
        await loadInstructors();

        document.getElementById('select-all-instructors').checked = false;
    } catch (error) {
        console.error('Error deleting instructors:', error);
        showNotification('Failed to delete instructors', 'error');
    }
}

// Add CSS for placeholder badge
const style = document.createElement('style');
style.textContent = `
    .badge-placeholder {
        background: #fff3cd;
        color: #856404;
    }
`;
document.head.appendChild(style);
```

### 3.3 Accessibility Checklist for Instructor List

- [ ] Table has proper ARIA roles and labels
- [ ] Checkboxes have descriptive aria-labels
- [ ] Action buttons have aria-labels
- [ ] Screen reader announces filter changes
- [ ] Keyboard navigation works for all interactive elements
- [ ] Focus visible on all elements
- [ ] Color contrast meets WCAG AA
- [ ] Touch targets are 44x44px minimum
- [ ] Loading state announced to screen readers
- [ ] Error messages announced to screen readers

---

## Phase 4: Quick View Modal

**Duration:** 2 days
**Goal:** Implement modal with essential instructor info and quick actions

### 4.1 HTML Modal Structure

#### File: `templates/admin.html` (ADD before closing `</body>`)

```html
<!-- Instructor Quick View Modal -->
<div class="modal" id="instructor-quick-view-modal" role="dialog" aria-labelledby="quick-view-title" aria-modal="true">
    <div class="modal-content" style="max-width: 700px;">
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2 id="quick-view-title" style="margin: 0;">
                <span id="quick-view-icon">👤</span>
                <span id="quick-view-name">Loading...</span>
            </h2>
            <button
                class="modal-close"
                onclick="hideInstructorQuickViewModal()"
                aria-label="Close quick view modal"
                style="min-width: 44px; min-height: 44px; font-size: 1.5rem; background: none; border: none; cursor: pointer; padding: 10px;">
                ✕
            </button>
        </div>

        <!-- Loading State -->
        <div id="quick-view-loading" style="text-align: center; padding: 40px;">
            <div class="spinner" style="margin: 0 auto 10px;"></div>
            <p>Loading instructor details...</p>
        </div>

        <!-- Content (hidden until loaded) -->
        <div id="quick-view-content" style="display: none;">
            <!-- Badge -->
            <div style="margin-bottom: 20px;">
                <span id="quick-view-badge" class="badge"></span>
            </div>

            <!-- Account Info -->
            <div style="background: var(--bg-color); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="font-size: 1rem; margin-bottom: 10px; color: var(--text-secondary);">Account Information</h3>
                <div style="display: grid; gap: 10px; font-size: 0.95rem;">
                    <div>
                        <strong>Username:</strong>
                        <span id="quick-view-username">-</span>
                    </div>
                    <div>
                        <strong>Email:</strong>
                        <span id="quick-view-email">-</span>
                    </div>
                    <div>
                        <strong>Created:</strong>
                        <span id="quick-view-created">-</span>
                    </div>
                    <div>
                        <strong>Last Login:</strong>
                        <span id="quick-view-last-login">-</span>
                    </div>
                </div>
            </div>

            <!-- Activity Stats (Cards) -->
            <div style="margin-bottom: 20px;">
                <h3 style="font-size: 1rem; margin-bottom: 10px; color: var(--text-secondary);">Activity Statistics</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px;">
                    <div class="stat-card" style="padding: 15px;">
                        <div class="stat-value" style="font-size: 1.8rem;" id="quick-view-classes">-</div>
                        <div class="stat-label">Classes</div>
                    </div>
                    <div class="stat-card" style="padding: 15px;">
                        <div class="stat-value" style="font-size: 1.8rem;" id="quick-view-sessions">-</div>
                        <div class="stat-label">Sessions</div>
                    </div>
                    <div class="stat-card" style="padding: 15px;">
                        <div class="stat-value" style="font-size: 1.8rem;" id="quick-view-questions">-</div>
                        <div class="stat-label">Questions</div>
                    </div>
                    <div class="stat-card" style="padding: 15px;">
                        <div class="stat-value" style="font-size: 1.8rem;" id="quick-view-students">-</div>
                        <div class="stat-label">Students</div>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div style="border-top: 1px solid var(--border-color); padding-top: 20px;">
                <h3 style="font-size: 1rem; margin-bottom: 10px; color: var(--text-secondary);">Quick Actions</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button
                        id="quick-view-action-activate"
                        class="btn btn-success"
                        onclick="quickViewActivate()"
                        style="flex: 1; min-width: 44px; min-height: 44px;">
                        ✅ Activate
                    </button>
                    <button
                        id="quick-view-action-deactivate"
                        class="btn btn-secondary"
                        onclick="quickViewDeactivate()"
                        style="flex: 1; min-width: 44px; min-height: 44px;">
                        🚫 Deactivate
                    </button>
                    <button
                        class="btn btn-primary"
                        onclick="quickViewResetPassword()"
                        style="flex: 1; min-width: 44px; min-height: 44px;">
                        🔑 Reset Password
                    </button>
                </div>
            </div>

            <!-- View Full Details Link -->
            <div style="margin-top: 20px; text-align: center;">
                <a
                    id="quick-view-full-details-link"
                    href="#"
                    class="btn btn-primary"
                    style="display: inline-block; min-width: 44px; min-height: 44px; line-height: 24px;">
                    📋 View Full Details →
                </a>
            </div>
        </div>
    </div>
</div>

<!-- Password Reset Success Modal -->
<div class="modal" id="password-reset-modal" role="dialog" aria-labelledby="password-reset-title" aria-modal="true">
    <div class="modal-content" style="max-width: 600px;">
        <h2 id="password-reset-title" style="color: var(--success-color);">✓ Password Reset</h2>
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">
            A temporary password has been generated. Copy it now and give it to the instructor.
        </p>

        <div style="background: #f8f9fa; border: 2px solid var(--success-color); border-radius: 8px; padding: 1rem; margin: 1.5rem 0;">
            <label style="display: block; font-weight: 600; margin-bottom: 0.5rem;">
                Temporary Password for <span id="password-reset-username"></span>:
            </label>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
                <input
                    type="text"
                    id="temporary-password-value"
                    readonly
                    style="flex: 1; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px; font-family: monospace; font-size: 1.1rem; background: white;">
                <button
                    class="btn btn-primary"
                    onclick="copyTemporaryPassword()"
                    id="copy-password-btn"
                    aria-label="Copy temporary password"
                    style="min-width: 120px; min-height: 44px;">
                    📋 Copy
                </button>
            </div>
        </div>

        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
            <strong style="color: #856404;">⚠️ Important:</strong>
            <ul style="color: #856404; margin: 0.5rem 0 0 1.5rem; font-size: 0.9rem;">
                <li>Give this password to the instructor via secure means (email, SMS, in-person)</li>
                <li>You won't be able to see it again after closing this dialog</li>
                <li>Instructor should change it after first login</li>
            </ul>
        </div>

        <button
            class="btn btn-success"
            onclick="hidePasswordResetModal()"
            style="width: 100%; margin-top: 1rem; min-height: 44px;">
            Done - I've Saved the Password
        </button>
    </div>
</div>
```

### 4.2 JavaScript for Quick View Modal

#### File: `static/js/admin.js` (ADD)

```javascript
// ============================================================================
// Quick View Modal Functions
// ============================================================================

let currentQuickViewInstructor = null;

/**
 * Show instructor quick view modal
 */
async function showInstructorQuickView(instructorId) {
    const modal = document.getElementById('instructor-quick-view-modal');
    const loading = document.getElementById('quick-view-loading');
    const content = document.getElementById('quick-view-content');

    // Show modal with loading state
    modal.classList.add('active');
    loading.style.display = 'block';
    content.style.display = 'none';

    // Focus management
    const previousActiveElement = document.activeElement;
    modal.setAttribute('data-previous-focus', previousActiveElement.id || '');

    try {
        const response = await fetch(`/api/admin/instructors/${instructorId}`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) throw new Error('Failed to load instructor details');

        const instructor = await response.json();
        currentQuickViewInstructor = instructor;

        // Populate modal
        populateQuickViewModal(instructor);

        // Hide loading, show content
        loading.style.display = 'none';
        content.style.display = 'block';

        // Focus first action button for keyboard users
        setTimeout(() => {
            const firstButton = content.querySelector('button');
            if (firstButton) firstButton.focus();
        }, 100);

    } catch (error) {
        console.error('Error loading instructor details:', error);
        loading.innerHTML = `
            <p style="color: var(--danger-color);">Failed to load instructor details.</p>
            <button class="btn btn-secondary" onclick="hideInstructorQuickViewModal()">Close</button>
        `;
        showNotification('Failed to load instructor details', 'error');
    }
}

/**
 * Populate quick view modal with instructor data
 */
function populateQuickViewModal(instructor) {
    // Name and icon
    document.getElementById('quick-view-name').textContent =
        instructor.display_name || instructor.username;

    // Badge
    let badgeClass, badgeText, badgeIcon;
    if (instructor.last_login === null) {
        badgeClass = 'badge-placeholder';
        badgeText = 'Placeholder (No Login)';
        badgeIcon = '🟡';
    } else if (instructor.is_active) {
        badgeClass = 'badge-active';
        badgeText = 'Active';
        badgeIcon = '🟢';
    } else {
        badgeClass = 'badge-ended';
        badgeText = 'Inactive';
        badgeIcon = '🔴';
    }

    const badgeEl = document.getElementById('quick-view-badge');
    badgeEl.className = `badge ${badgeClass}`;
    badgeEl.textContent = `${badgeIcon} ${badgeText}`;

    // Account info
    document.getElementById('quick-view-username').textContent = instructor.username;
    document.getElementById('quick-view-email').textContent = instructor.email || 'Not provided';
    document.getElementById('quick-view-created').textContent =
        new Date(instructor.created_at).toLocaleDateString();
    document.getElementById('quick-view-last-login').textContent =
        instructor.last_login ? new Date(instructor.last_login).toLocaleDateString() : 'Never';

    // Stats
    document.getElementById('quick-view-classes').textContent = instructor.stats.classes_count;
    document.getElementById('quick-view-sessions').textContent = instructor.stats.sessions_count;
    document.getElementById('quick-view-questions').textContent = instructor.stats.questions_count;
    document.getElementById('quick-view-students').textContent = instructor.stats.unique_students_count;

    // Action buttons
    const activateBtn = document.getElementById('quick-view-action-activate');
    const deactivateBtn = document.getElementById('quick-view-action-deactivate');

    if (instructor.is_active) {
        activateBtn.style.display = 'none';
        deactivateBtn.style.display = 'block';
    } else {
        activateBtn.style.display = 'block';
        deactivateBtn.style.display = 'none';
    }

    // Full details link
    document.getElementById('quick-view-full-details-link').href =
        `/admin/instructors/${instructor.id}`;
}

/**
 * Hide quick view modal
 */
function hideInstructorQuickViewModal() {
    const modal = document.getElementById('instructor-quick-view-modal');
    modal.classList.remove('active');
    currentQuickViewInstructor = null;

    // Restore focus
    const previousFocusId = modal.getAttribute('data-previous-focus');
    if (previousFocusId) {
        const element = document.getElementById(previousFocusId);
        if (element) element.focus();
    }
}

/**
 * Quick view activate action
 */
async function quickViewActivate() {
    if (!currentQuickViewInstructor) return;

    await activateInstructor(
        currentQuickViewInstructor.id,
        currentQuickViewInstructor.username
    );

    // Refresh the quick view
    await showInstructorQuickView(currentQuickViewInstructor.id);
}

/**
 * Quick view deactivate action
 */
async function quickViewDeactivate() {
    if (!currentQuickViewInstructor) return;

    await deactivateInstructor(
        currentQuickViewInstructor.id,
        currentQuickViewInstructor.username
    );

    // Refresh the quick view
    await showInstructorQuickView(currentQuickViewInstructor.id);
}

/**
 * Quick view reset password action
 */
async function quickViewResetPassword() {
    if (!currentQuickViewInstructor) return;

    const instructor = currentQuickViewInstructor;

    if (!confirm(`Reset password for "${instructor.username}"?\n\nA temporary password will be generated that you must give to the instructor.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/instructors/${instructor.id}/reset-password`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (!response.ok) throw new Error('Failed to reset password');

        const result = await response.json();

        // Show password reset modal
        document.getElementById('password-reset-username').textContent = instructor.username;
        document.getElementById('temporary-password-value').value = result.temporary_password;
        document.getElementById('password-reset-modal').classList.add('active');

        // Auto-copy password
        await copyToClipboard(result.temporary_password);
        showNotification('Temporary password copied to clipboard', 'success');

        // Hide quick view
        hideInstructorQuickViewModal();

    } catch (error) {
        console.error('Error resetting password:', error);
        showNotification('Failed to reset password', 'error');
    }
}

/**
 * Hide password reset modal
 */
function hidePasswordResetModal() {
    document.getElementById('password-reset-modal').classList.remove('active');
    document.getElementById('temporary-password-value').value = '';
}

/**
 * Copy temporary password
 */
async function copyTemporaryPassword() {
    const input = document.getElementById('temporary-password-value');
    const btn = document.getElementById('copy-password-btn');

    try {
        await navigator.clipboard.writeText(input.value);

        const originalText = btn.innerHTML;
        btn.innerHTML = '✓ Copied!';
        btn.style.background = var(--success-color);

        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.style.background = '';
        }, 2000);

        showNotification('Password copied to clipboard', 'success');
    } catch (error) {
        // Fallback
        input.select();
        document.execCommand('copy');
        showNotification('Password copied (fallback method)', 'success');
    }
}

// Keyboard handling for modals
document.addEventListener('keydown', function(e) {
    // Escape key closes modals
    if (e.key === 'Escape') {
        if (document.getElementById('instructor-quick-view-modal').classList.contains('active')) {
            hideInstructorQuickViewModal();
        }
        if (document.getElementById('password-reset-modal').classList.contains('active')) {
            hidePasswordResetModal();
        }
    }
});
```

### 4.3 Mobile Responsiveness for Modals

#### File: `static/css/styles.css` (ADD)

```css
/* Mobile-optimized modals */
@media (max-width: 768px) {
    .modal-content {
        width: 95vw !important;
        max-width: 95vw !important;
        max-height: 95vh;
        overflow-y: auto;
        margin: 2.5vh auto;
    }

    /* Full-screen modal on very small screens */
    @media (max-width: 480px) {
        .modal-content {
            width: 100vw !important;
            height: 100vh !important;
            max-width: 100vw !important;
            max-height: 100vh !important;
            margin: 0;
            border-radius: 0;
        }
    }

    /* Stack buttons vertically on mobile */
    #quick-view-content > div:last-of-type > div {
        flex-direction: column;
    }

    #quick-view-content button {
        width: 100% !important;
    }

    /* Adjust stat cards for mobile */
    .stat-card {
        min-width: 80px;
    }
}
```

### 4.4 Accessibility Checklist for Quick View Modal

- [ ] Modal has role="dialog" and aria-modal="true"
- [ ] Modal has aria-labelledby pointing to title
- [ ] Focus trapped within modal when open
- [ ] Escape key closes modal
- [ ] Focus returned to trigger element on close
- [ ] Close button has aria-label
- [ ] All interactive elements keyboard accessible
- [ ] Screen reader announces modal content
- [ ] Loading state announced to screen readers
- [ ] Color contrast meets WCAG AA
- [ ] Touch targets 44x44px minimum

---

## Phase 5: Full Details Page

**Duration:** 3 days
**Goal:** Create comprehensive instructor details page with all related data

### 5.1 New Route Handler

#### File: `main.py` (ADD)

```python
@app.get("/admin/instructors/{instructor_id}", response_class=HTMLResponse)
async def admin_instructor_detail_view(request: Request, instructor_id: int):
    """Admin view for instructor details page."""
    return templates.TemplateResponse("admin-instructor-detail.html", {
        "request": request,
        "instructor_id": instructor_id
    })
```

### 5.2 New Template

#### File: `templates/admin-instructor-detail.html` (NEW FILE)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instructor Details - RaiseMyHand Admin</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <style>
        /* Breadcrumb navigation */
        .breadcrumb {
            padding: 15px 0;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .breadcrumb ol {
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0;
            padding: 0;
        }

        .breadcrumb li:not(:last-child)::after {
            content: "›";
            margin-left: 0.5rem;
            color: #999;
        }

        .breadcrumb a {
            color: var(--primary-color);
            text-decoration: none;
        }

        .breadcrumb a:hover {
            text-decoration: underline;
        }

        .breadcrumb [aria-current="page"] {
            color: var(--text-color);
            font-weight: 500;
        }

        /* Page header */
        .page-header {
            background: var(--card-bg);
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: var(--shadow);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }

        .instructor-info {
            flex: 1;
            min-width: 300px;
        }

        .instructor-name {
            font-size: 2rem;
            color: var(--text-color);
            margin-bottom: 10px;
        }

        .instructor-meta {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        /* Stats grid */
        .stats-section {
            margin-bottom: 40px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
        }

        /* Data tables */
        .data-section {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: var(--shadow);
        }

        .data-section h3 {
            margin-bottom: 15px;
            color: var(--primary-color);
        }

        /* Mobile adjustments */
        @media (max-width: 768px) {
            .page-header {
                flex-direction: column;
                align-items: flex-start;
            }

            .instructor-name {
                font-size: 1.5rem;
            }

            .stats-grid {
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <div>
                    <h1>🔧 RaiseMyHand - Admin Dashboard</h1>
                    <p class="subtitle">Instructor Details</p>
                </div>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- Breadcrumb Navigation -->
        <nav class="breadcrumb" aria-label="Breadcrumb">
            <ol>
                <li><a href="/admin">Admin Dashboard</a></li>
                <li><a href="/admin#instructors" onclick="navigateToInstructorsTab(event)">Instructors</a></li>
                <li aria-current="page" id="breadcrumb-instructor-name">Loading...</li>
            </ol>
        </nav>

        <!-- Loading State -->
        <div id="loading-state" style="text-align: center; padding: 60px 20px;">
            <div class="spinner" style="margin: 0 auto 20px;"></div>
            <p>Loading instructor details...</p>
        </div>

        <!-- Content (hidden until loaded) -->
        <div id="instructor-detail-content" style="display: none;">
            <!-- Page Header -->
            <div class="page-header">
                <div class="instructor-info">
                    <div class="instructor-name" id="instructor-name">
                        <span id="instructor-icon">👤</span>
                        <span id="instructor-display-name">Loading...</span>
                    </div>
                    <div class="instructor-meta">
                        <div style="margin-bottom: 10px;">
                            <span id="instructor-badge" class="badge"></span>
                        </div>
                        <div>
                            <strong>Username:</strong> <span id="instructor-username">-</span>
                        </div>
                        <div>
                            <strong>Email:</strong> <span id="instructor-email">-</span>
                        </div>
                        <div>
                            <strong>Created:</strong> <span id="instructor-created">-</span>
                        </div>
                        <div>
                            <strong>Last Login:</strong> <span id="instructor-last-login">-</span>
                        </div>
                    </div>
                </div>

                <!-- Actions -->
                <div class="button-group">
                    <button
                        id="action-activate"
                        class="btn btn-success"
                        onclick="activateInstructorDetail()"
                        style="min-width: 44px; min-height: 44px;">
                        ✅ Activate
                    </button>
                    <button
                        id="action-deactivate"
                        class="btn btn-secondary"
                        onclick="deactivateInstructorDetail()"
                        style="min-width: 44px; min-height: 44px;">
                        🚫 Deactivate
                    </button>
                    <button
                        class="btn btn-primary"
                        onclick="resetPasswordDetail()"
                        style="min-width: 44px; min-height: 44px;">
                        🔑 Reset Password
                    </button>
                    <button
                        class="btn btn-danger"
                        onclick="deleteInstructorDetail()"
                        style="min-width: 44px; min-height: 44px;">
                        🗑️ Delete Instructor
                    </button>
                </div>
            </div>

            <!-- Statistics Section -->
            <div class="stats-section">
                <h2>Activity Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Classes</div>
                        <div class="stat-value" id="stat-classes">-</div>
                        <div class="stat-label" style="font-size: 0.8rem; margin-top: 5px;">
                            <span id="stat-archived-classes">-</span> archived
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Sessions</div>
                        <div class="stat-value" id="stat-sessions">-</div>
                        <div class="stat-label" style="font-size: 0.8rem; margin-top: 5px;">
                            <span id="stat-active-sessions">-</span> active
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Questions</div>
                        <div class="stat-value" id="stat-questions">-</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total Upvotes</div>
                        <div class="stat-value" id="stat-upvotes">-</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Unique Students</div>
                        <div class="stat-value" id="stat-students">-</div>
                    </div>
                </div>
            </div>

            <!-- API Keys Section -->
            <div class="data-section">
                <h3>API Keys (<span id="api-keys-count">0</span>)</h3>
                <div class="sessions-table">
                    <table role="table" aria-label="Instructor API keys">
                        <thead>
                            <tr>
                                <th scope="col">Name</th>
                                <th scope="col">Key</th>
                                <th scope="col">Created</th>
                                <th scope="col">Last Used</th>
                                <th scope="col">Status</th>
                            </tr>
                        </thead>
                        <tbody id="api-keys-table-body">
                            <tr>
                                <td colspan="5" style="text-align: center; padding: 20px; color: #666;">
                                    No API keys
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Classes Section -->
            <div class="data-section">
                <h3>Classes (<span id="classes-count">0</span>)</h3>
                <div class="sessions-table">
                    <table role="table" aria-label="Instructor classes">
                        <thead>
                            <tr>
                                <th scope="col">Class Name</th>
                                <th scope="col">Description</th>
                                <th scope="col">Meetings</th>
                                <th scope="col">Created</th>
                                <th scope="col">Status</th>
                            </tr>
                        </thead>
                        <tbody id="classes-table-body">
                            <tr>
                                <td colspan="5" style="text-align: center; padding: 20px; color: #666;">
                                    No classes
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Recent Sessions Section -->
            <div class="data-section">
                <h3>Recent Sessions (Last 10)</h3>
                <div class="sessions-table">
                    <table role="table" aria-label="Recent sessions">
                        <thead>
                            <tr>
                                <th scope="col">Title</th>
                                <th scope="col">Created</th>
                                <th scope="col">Status</th>
                                <th scope="col">Questions</th>
                                <th scope="col">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="sessions-table-body">
                            <tr>
                                <td colspan="5" style="text-align: center; padding: 20px; color: #666;">
                                    No sessions
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Back to List Button -->
            <div style="margin-top: 40px; text-align: center;">
                <a href="/admin#instructors" onclick="navigateToInstructorsTab(event)" class="btn btn-secondary">
                    ← Back to Instructor List
                </a>
            </div>
        </div>
    </div>

    <!-- Password Reset Modal (reuse from admin.html) -->
    <div class="modal" id="password-reset-modal" role="dialog" aria-labelledby="password-reset-title" aria-modal="true">
        <!-- Same content as Phase 4 -->
    </div>

    <script src="/static/js/shared.js"></script>
    <script src="/static/js/admin.js"></script>
    <script>
        // Get instructor ID from URL
        const pathParts = window.location.pathname.split('/');
        const instructorId = parseInt(pathParts[pathParts.length - 1]);

        let currentInstructor = null;

        // Load instructor details on page load
        window.addEventListener('load', loadInstructorDetails);

        async function loadInstructorDetails() {
            try {
                const response = await fetch(`/api/admin/instructors/${instructorId}`, {
                    headers: getAuthHeaders()
                });

                if (handleAuthError(response)) return;
                if (!response.ok) throw new Error('Failed to load instructor');

                const instructor = await response.json();
                currentInstructor = instructor;

                populateInstructorDetails(instructor);

                // Hide loading, show content
                document.getElementById('loading-state').style.display = 'none';
                document.getElementById('instructor-detail-content').style.display = 'block';

            } catch (error) {
                console.error('Error loading instructor:', error);
                document.getElementById('loading-state').innerHTML = `
                    <p style="color: var(--danger-color);">Failed to load instructor details.</p>
                    <a href="/admin#instructors" class="btn btn-secondary">← Back to List</a>
                `;
            }
        }

        function populateInstructorDetails(instructor) {
            // Breadcrumb
            document.getElementById('breadcrumb-instructor-name').textContent =
                instructor.display_name || instructor.username;

            // Header
            document.getElementById('instructor-display-name').textContent =
                instructor.display_name || instructor.username;
            document.getElementById('instructor-username').textContent = instructor.username;
            document.getElementById('instructor-email').textContent = instructor.email || 'Not provided';
            document.getElementById('instructor-created').textContent =
                new Date(instructor.created_at).toLocaleDateString();
            document.getElementById('instructor-last-login').textContent =
                instructor.last_login ? new Date(instructor.last_login).toLocaleDateString() : 'Never';

            // Badge
            let badgeClass, badgeText, badgeIcon;
            if (instructor.last_login === null) {
                badgeClass = 'badge-placeholder';
                badgeText = 'Placeholder (No Login)';
                badgeIcon = '🟡';
            } else if (instructor.is_active) {
                badgeClass = 'badge-active';
                badgeText = 'Active';
                badgeIcon = '🟢';
            } else {
                badgeClass = 'badge-ended';
                badgeText = 'Inactive';
                badgeIcon = '🔴';
            }
            const badgeEl = document.getElementById('instructor-badge');
            badgeEl.className = `badge ${badgeClass}`;
            badgeEl.textContent = `${badgeIcon} ${badgeText}`;

            // Action buttons
            if (instructor.is_active) {
                document.getElementById('action-activate').style.display = 'none';
                document.getElementById('action-deactivate').style.display = 'block';
            } else {
                document.getElementById('action-activate').style.display = 'block';
                document.getElementById('action-deactivate').style.display = 'none';
            }

            // Stats
            document.getElementById('stat-classes').textContent = instructor.stats.classes_count;
            document.getElementById('stat-archived-classes').textContent = instructor.stats.archived_classes_count;
            document.getElementById('stat-sessions').textContent = instructor.stats.sessions_count;
            document.getElementById('stat-active-sessions').textContent = instructor.stats.active_sessions_count;
            document.getElementById('stat-questions').textContent = instructor.stats.questions_count;
            document.getElementById('stat-upvotes').textContent = instructor.stats.upvotes_count;
            document.getElementById('stat-students').textContent = instructor.stats.unique_students_count;

            // API Keys
            populateApiKeysTable(instructor.api_keys);

            // Classes
            populateClassesTable(instructor.classes);

            // Recent Sessions
            populateSessionsTable(instructor.recent_sessions);
        }

        function populateApiKeysTable(apiKeys) {
            document.getElementById('api-keys-count').textContent = apiKeys.length;
            const tbody = document.getElementById('api-keys-table-body');

            if (apiKeys.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 20px; color: #666;">
                            No API keys
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = apiKeys.map(key => {
                const createdDate = new Date(key.created_at).toLocaleDateString();
                const lastUsed = key.last_used ? new Date(key.last_used).toLocaleDateString() : 'Never';
                const statusBadge = key.is_active
                    ? '<span class="badge badge-active">Active</span>'
                    : '<span class="badge badge-ended">Inactive</span>';

                return `
                    <tr>
                        <td><strong>${escapeHtml(key.name)}</strong></td>
                        <td><code style="font-size: 0.85rem;">${escapeHtml(key.key)}</code></td>
                        <td>${createdDate}</td>
                        <td>${lastUsed}</td>
                        <td>${statusBadge}</td>
                    </tr>
                `;
            }).join('');
        }

        function populateClassesTable(classes) {
            document.getElementById('classes-count').textContent = classes.length;
            const tbody = document.getElementById('classes-table-body');

            if (classes.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 20px; color: #666;">
                            No classes
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = classes.map(cls => {
                const createdDate = new Date(cls.created_at).toLocaleDateString();
                const statusBadge = cls.is_archived
                    ? '<span class="badge badge-ended">Archived</span>'
                    : '<span class="badge badge-active">Active</span>';

                return `
                    <tr>
                        <td><strong>${escapeHtml(cls.name)}</strong></td>
                        <td>${escapeHtml(cls.description || '-')}</td>
                        <td style="text-align: center;">${cls.meeting_count}</td>
                        <td>${createdDate}</td>
                        <td>${statusBadge}</td>
                    </tr>
                `;
            }).join('');
        }

        function populateSessionsTable(sessions) {
            const tbody = document.getElementById('sessions-table-body');

            if (sessions.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 20px; color: #666;">
                            No sessions
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = sessions.map(session => {
                const createdDate = new Date(session.created_at).toLocaleDateString();
                const statusBadge = session.is_active
                    ? '<span class="badge badge-active">Active</span>'
                    : '<span class="badge badge-ended">Ended</span>';
                const instructorUrl = `${window.location.origin}/instructor?code=${session.instructor_code}`;

                return `
                    <tr>
                        <td><strong>${escapeHtml(session.title)}</strong></td>
                        <td>${createdDate}</td>
                        <td>${statusBadge}</td>
                        <td style="text-align: center;">${session.question_count}</td>
                        <td>
                            <button
                                class="btn-view"
                                onclick="window.open('${instructorUrl}', '_blank')"
                                style="min-width: 44px; min-height: 44px;">
                                👁️ View
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        // Action functions
        async function activateInstructorDetail() {
            await activateInstructor(currentInstructor.id, currentInstructor.username);
            await loadInstructorDetails(); // Reload
        }

        async function deactivateInstructorDetail() {
            await deactivateInstructor(currentInstructor.id, currentInstructor.username);
            await loadInstructorDetails(); // Reload
        }

        async function resetPasswordDetail() {
            // Reuse logic from Phase 4
            const instructor = currentInstructor;

            if (!confirm(`Reset password for "${instructor.username}"?\n\nA temporary password will be generated.`)) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/instructors/${instructor.id}/reset-password`, {
                    method: 'POST',
                    headers: getAuthHeaders()
                });

                if (!response.ok) throw new Error('Failed to reset password');

                const result = await response.json();

                // Show password reset modal
                document.getElementById('password-reset-username').textContent = instructor.username;
                document.getElementById('temporary-password-value').value = result.temporary_password;
                document.getElementById('password-reset-modal').classList.add('active');

                // Auto-copy
                await copyToClipboard(result.temporary_password);
                showNotification('Temporary password copied to clipboard', 'success');

            } catch (error) {
                console.error('Error resetting password:', error);
                showNotification('Failed to reset password', 'error');
            }
        }

        async function deleteInstructorDetail() {
            const confirmMsg = `⚠️ DELETE instructor "${currentInstructor.username}"?\n\n` +
                              `This will PERMANENTLY DELETE:\n` +
                              `- Instructor account\n` +
                              `- All their classes\n` +
                              `- All their sessions\n` +
                              `- All questions in those sessions\n\n` +
                              `THIS CANNOT BE UNDONE!\n\n` +
                              `Type "DELETE" to confirm:`;

            const confirmation = prompt(confirmMsg);
            if (confirmation !== 'DELETE') {
                return;
            }

            try {
                const response = await fetch(`/api/admin/instructors/bulk/delete`, {
                    method: 'DELETE',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({ instructor_ids: [currentInstructor.id] })
                });

                if (!response.ok) throw new Error('Failed to delete instructor');

                showNotification('Instructor deleted successfully', 'success');

                // Redirect back to list
                setTimeout(() => {
                    window.location.href = '/admin#instructors';
                }, 1500);

            } catch (error) {
                console.error('Error deleting instructor:', error);
                showNotification('Failed to delete instructor', 'error');
            }
        }

        function navigateToInstructorsTab(e) {
            e.preventDefault();
            window.location.href = '/admin#instructors';
        }

        function hidePasswordResetModal() {
            document.getElementById('password-reset-modal').classList.remove('active');
        }

        function logout() {
            if (confirm('Are you sure you want to logout?')) {
                localStorage.removeItem('admin_token');
                window.location.href = '/admin-login';
            }
        }

        // Keyboard: Escape closes modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && document.getElementById('password-reset-modal').classList.contains('active')) {
                hidePasswordResetModal();
            }
        });
    </script>
</body>
</html>
```

### 5.3 Accessibility Checklist for Detail Page

- [ ] Breadcrumb navigation with proper ARIA
- [ ] All interactive elements keyboard accessible
- [ ] Focus visible on all elements
- [ ] Page title describes current page
- [ ] Screen reader announces page content
- [ ] Tables have proper headers and captions
- [ ] Color contrast meets WCAG AA
- [ ] Touch targets 44x44px minimum
- [ ] Works without JavaScript for critical content
- [ ] Loading state announced to screen readers

---

## Phase 6: Bulk Actions

**Duration:** 2 days (ALREADY IMPLEMENTED in Phase 3!)

The bulk actions were implemented as part of Phase 3. This phase is for:
- Additional testing
- Error handling improvements
- Partial failure scenarios

### 6.1 Enhanced Bulk Action Error Handling

#### File: `static/js/admin.js` (ENHANCE existing bulk functions)

Add better error messages and partial failure handling:

```javascript
// Enhanced bulk action with partial failure handling
async function enhancedBulkAction(action, instructorIds, actionName) {
    if (instructorIds.length === 0) {
        showNotification('Please select at least one instructor', 'error');
        return false;
    }

    try {
        const response = await fetch(`/api/admin/instructors/bulk/${action}`, {
            method: action === 'delete' ? 'DELETE' : 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ instructor_ids: instructorIds })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Failed to ${actionName} instructors`);
        }

        const result = await response.json();

        // Handle partial failures
        if (result.failed_count > 0) {
            showNotification(
                `${actionName} completed with ${result.successful_count} success(es) and ${result.failed_count} failure(s)`,
                'warning'
            );
        } else {
            showNotification(result.message, 'success');
        }

        return true;

    } catch (error) {
        console.error(`Error during bulk ${actionName}:`, error);
        showNotification(error.message || `Failed to ${actionName} instructors`, 'error');
        return false;
    }
}
```

### 6.2 Testing Checklist for Bulk Actions

- [ ] Bulk activate works with 1, 5, 50 instructors
- [ ] Bulk deactivate works with 1, 5, 50 instructors
- [ ] Bulk delete requires "DELETE" confirmation
- [ ] Partial failures handled gracefully
- [ ] Network errors handled gracefully
- [ ] Auth errors handled gracefully
- [ ] UI updates after bulk operation
- [ ] Select all checkbox unchecked after operation
- [ ] Loading states during bulk operation
- [ ] Screen reader announces results

---

## Phase 7: Accessibility Polish

**Duration:** 2-3 days
**Goal:** Comprehensive accessibility audit and fixes

### 7.1 Accessibility Audit Checklist

#### Keyboard Navigation
- [ ] All interactive elements focusable via Tab
- [ ] Tab order is logical (left-to-right, top-to-bottom)
- [ ] Focus visible with 2px outline
- [ ] Escape closes modals
- [ ] Enter/Space activates buttons
- [ ] Arrow keys navigate tabs
- [ ] Home/End keys in tab lists
- [ ] No keyboard traps

#### Screen Reader Support
- [ ] All images have alt text
- [ ] All form inputs have labels
- [ ] All buttons have accessible names
- [ ] ARIA roles used correctly
- [ ] ARIA live regions for dynamic content
- [ ] ARIA labels for icon-only buttons
- [ ] ARIA-describedby for help text
- [ ] Landmarks (nav, main, aside, etc.)

#### Color Contrast (WCAG AA)
- [ ] Normal text: 4.5:1 minimum
- [ ] Large text (18pt+): 3:1 minimum
- [ ] UI components: 3:1 minimum
- [ ] Focus indicators: 3:1 minimum
- [ ] Test with Colorblind simulators

#### Touch Targets (Mobile)
- [ ] All buttons 44x44px minimum
- [ ] Adequate spacing between targets (8px+)
- [ ] No overlapping touch areas
- [ ] Works with single-finger touch
- [ ] Swipe gestures have alternatives

#### Forms & Inputs
- [ ] Labels associated with inputs
- [ ] Required fields indicated
- [ ] Error messages clear and specific
- [ ] Success messages announced
- [ ] Field constraints explained
- [ ] Inline validation accessible

#### Tables
- [ ] Use <table> element (not divs)
- [ ] <th> elements with scope attribute
- [ ] <caption> or aria-label
- [ ] Complex tables use header IDs
- [ ] Sortable columns indicated

### 7.2 Color Contrast Audit

#### File: `static/css/styles.css` (AUDIT AND FIX)

```css
/* Audit results and fixes */

/* BEFORE: Text secondary color fails contrast */
--text-secondary: #7f8c8d; /* 3.8:1 on white - FAILS */

/* AFTER: Fixed to meet 4.5:1 */
--text-secondary: #5a6c7d; /* 4.52:1 on white - PASSES */

/* BEFORE: Disabled button text too light */
.btn:disabled {
    color: #aaa; /* Fails */
}

/* AFTER: Improved */
.btn:disabled {
    color: #666; /* 5.7:1 - PASSES */
    opacity: 0.7; /* Visual indicator */
}

/* BEFORE: Badge text */
.badge-placeholder {
    background: #fff3cd;
    color: #856404; /* 4.6:1 - borderline */
}

/* AFTER: Improved */
.badge-placeholder {
    background: #ffe69c; /* Darker background */
    color: #664d03; /* Darker text, 7:1 */
    border: 1px solid #ffcd39; /* Additional definition */
}

/* Focus indicators - ensure 3:1 contrast with background */
*:focus {
    outline: 3px solid #0066cc; /* High contrast */
    outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    :root {
        --text-color: #000;
        --bg-color: #fff;
        --border-color: #000;
    }

    .btn {
        border: 2px solid currentColor;
    }
}
```

### 7.3 Screen Reader Testing Script

Create manual testing checklist:

#### File: `docs/ACCESSIBILITY_TEST_CHECKLIST.md` (NEW)

```markdown
# Accessibility Testing Checklist

## Screen Reader Tests

### NVDA (Windows) / JAWS
1. Navigate to admin dashboard
2. Verify header announces correctly
3. Tab through all navigation elements
4. Verify tab list announces "X of Y tabs"
5. Navigate instructors table
6. Verify table structure announced
7. Activate "View" button on instructor
8. Verify modal announced as dialog
9. Navigate modal with Tab
10. Close modal with Escape
11. Verify focus returns to trigger

### VoiceOver (macOS/iOS)
1. Same tests as above
2. Verify rotor navigation works
3. Test touch gestures on iOS

### ChromeVox (Chrome)
1. Same tests as NVDA
2. Verify works in Chromebook environment

## Keyboard Navigation Tests

1. Tab through all UI (no elements skipped)
2. Shift+Tab goes backward
3. Enter activates buttons/links
4. Space activates buttons
5. Escape closes modals
6. Arrow keys navigate tabs
7. Arrow keys navigate select dropdowns
8. Home/End keys work in appropriate contexts

## Color Contrast Tests

Use tools:
- WebAIM Contrast Checker
- Chrome DevTools Lighthouse
- axe DevTools

Check:
- All text meets 4.5:1 (normal size)
- All text meets 3:1 (large size >18pt)
- All UI components meet 3:1
- Focus indicators meet 3:1

## Mobile Touch Tests

Test on:
- iPhone (Safari)
- Android (Chrome)
- iPad

Check:
- All buttons 44x44px minimum
- Can tap without zooming
- No accidental taps
- Swipe gestures work
```

### 7.4 Automated Testing

#### File: `tests/test_accessibility.py` (NEW)

```python
"""
Automated accessibility tests using axe-core via playwright
"""
import pytest
from playwright.sync_api import sync_playwright

def test_admin_dashboard_accessibility():
    """Test admin dashboard for accessibility violations."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Login
        page.goto('http://localhost:8000/admin-login')
        page.fill('#username', 'admin')
        page.fill('#password', 'test_password')
        page.click('button[type="submit"]')

        # Wait for dashboard
        page.wait_for_selector('.tab-navigation')

        # Inject axe-core
        page.add_script_tag(url='https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js')

        # Run axe
        results = page.evaluate('axe.run()')

        # Assert no violations
        violations = results['violations']
        assert len(violations) == 0, f"Accessibility violations found: {violations}"

        browser.close()

def test_instructor_list_accessibility():
    """Test instructor list tab."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Login and navigate to instructors tab
        # ... (similar to above)

        page.click('#tab-instructors')
        page.wait_for_selector('#panel-instructors[aria-hidden="false"]')

        # Run axe on instructors panel
        results = page.evaluate('axe.run("#panel-instructors")')

        violations = results['violations']
        assert len(violations) == 0, f"Violations: {violations}"

        browser.close()
```

---

## Testing Strategy

### Unit Tests
- API endpoint tests (Phase 1)
- Schema validation tests
- Database query tests

### Integration Tests
- Full workflow tests (list → view → edit → delete)
- Authentication tests
- Permission tests (admin-only access)

### UI Tests
- Tab navigation
- Modal interactions
- Form submissions
- Bulk actions

### Accessibility Tests
- Automated (axe-core, pa11y)
- Manual (screen readers)
- Keyboard navigation
- Color contrast

### Performance Tests
- List 1000+ instructors
- Bulk operations on 100+ instructors
- Modal open/close speed
- Tab switching speed

---

## Deployment Checklist

### Pre-Deployment
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Accessibility audit complete (no critical issues)
- [ ] Code review completed
- [ ] Database migration tested
- [ ] Rollback plan documented

### Deployment Steps
1. **Backup database**
2. **Run alembic migration** (if needed)
3. **Deploy backend** (routes_admin.py, schemas_v2.py, main.py)
4. **Deploy frontend** (admin.html, admin.js, styles.css)
5. **Deploy new template** (admin-instructor-detail.html)
6. **Verify deployment**
7. **Monitor logs** for errors

### Post-Deployment
- [ ] Smoke test: Login as admin
- [ ] Smoke test: View instructors list
- [ ] Smoke test: View instructor detail
- [ ] Smoke test: Reset password
- [ ] Monitor error rates
- [ ] Monitor performance metrics
- [ ] Gather user feedback

### Rollback Plan
If issues found:
1. Revert frontend files (admin.html, admin.js)
2. Disable new routes in main.py
3. Roll back database migration (if needed)
4. Notify users of maintenance

---

## Success Metrics

### Functionality
- Admin can view all instructors (registered + placeholder)
- Admin can search and filter instructors
- Admin can activate/deactivate accounts
- Admin can reset passwords
- Admin can view comprehensive stats
- Bulk operations work correctly

### Performance
- List page loads in <2 seconds (100 instructors)
- Detail page loads in <1 second
- Modal opens in <300ms
- Tab switches in <200ms

### Accessibility
- WCAG AA compliant (Level 2)
- Lighthouse accessibility score >95
- axe-core: 0 critical violations
- Screen reader tested and working
- Keyboard navigation 100% functional

### Usability
- Admin finds instructor in <30 seconds
- Password reset completes in <60 seconds
- No user-reported bugs after 1 week
- Positive feedback from admin users

---

## Future Enhancements

### Phase 8 (Optional)
- Email service integration for password resets
- 2FA for instructors
- Audit log UI (view admin actions)
- Advanced filtering (created date range, etc.)
- Export instructors to CSV
- Import instructors from CSV
- Instructor analytics dashboard

### Phase 9 (Optional)
- LDAP/SSO integration
- Multi-admin support with roles
- Instructor groups/departments
- Scheduled reports
- API webhooks for instructor events

---

## Conclusion

This implementation plan provides a comprehensive roadmap for adding admin instructor management to RaiseMyHand. The phased approach ensures steady progress with testable milestones. The focus on accessibility ensures the feature is usable by all admins, including those using assistive technologies.

**Estimated Total Time: 17-21 days (2.5-3 weeks)**

**Ready to begin implementation!** 🚀
