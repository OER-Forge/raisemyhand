"""
Pydantic schemas for RaiseMyHand v2.0 API
Request/response validation for hierarchical architecture
"""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List


# ============================================================================
# Instructor Schemas
# ============================================================================

class InstructorRegister(BaseModel):
    """Register a new instructor."""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class InstructorLogin(BaseModel):
    """Login with username and password."""
    username: str
    password: str


class InstructorUpdate(BaseModel):
    """Update instructor profile."""
    display_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None  # Required if changing password
    new_password: Optional[str] = Field(None, min_length=8, max_length=100)  # New password


class InstructorResponse(BaseModel):
    """Public instructor information."""
    id: int
    username: str
    email: Optional[str]
    display_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# API Key Schemas
# ============================================================================

class PasswordConfirmation(BaseModel):
    """Password confirmation for sensitive operations."""
    password: str = Field(..., min_length=1)


class APIKeyCreate(BaseModel):
    """Create a new API key."""
    name: str = Field(..., min_length=1, max_length=100)


class APIKeyRevocationRequest(BaseModel):
    """Request to revoke an API key."""
    reason: str = Field(..., min_length=1, max_length=500)


class APIKeyResponse(BaseModel):
    """API key with metadata."""
    id: int
    instructor_id: int
    key: str
    name: str
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

    @staticmethod
    def mask_key(full_key: str) -> str:
        """Mask an API key for display (show first 7 + last 4 chars)."""
        if len(full_key) <= 11:
            return "****"
        return f"{full_key[:7]}...{full_key[-4:]}"

    def get_masked_key(self) -> str:
        """Get the masked version of this key."""
        return self.mask_key(self.key)

    def get_preview(self) -> str:
        """Get a preview of the key (masked version)."""
        return self.get_masked_key()


class APIKeyMaskedResponse(BaseModel):
    """API key with masked key for listing (sensitive data hidden by default)."""
    id: int
    instructor_id: int
    key_masked: str  # Masked version like "rmh_abc...xyz"
    key_preview: str  # Same as key_masked for backwards compatibility
    name: str
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool
    instructor_username: Optional[str] = None  # For admin UI display
    instructor_display_name: Optional[str] = None  # For admin UI display

    class Config:
        from_attributes = False  # We build this manually

    @classmethod
    def from_api_key(cls, api_key, instructor=None):
        """Create a masked response from an APIKey model.

        Args:
            api_key: The APIKey database model
            instructor: Optional Instructor model for including instructor details
        """
        masked = APIKeyResponse.mask_key(api_key.key)
        return cls(
            id=api_key.id,
            instructor_id=api_key.instructor_id,
            key_masked=masked,
            key_preview=masked,
            name=api_key.name,
            created_at=api_key.created_at,
            last_used=api_key.last_used,
            is_active=api_key.is_active,
            instructor_username=instructor.username if instructor else None,
            instructor_display_name=instructor.display_name if instructor else None
        )


class InstructorAuth(BaseModel):
    """Authenticate with API key."""
    api_key: str


# ============================================================================
# Class Schemas
# ============================================================================

class ClassCreate(BaseModel):
    """Create a new class."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class ClassUpdate(BaseModel):
    """Update class information."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class ClassResponse(BaseModel):
    """Class with metadata."""
    id: int
    instructor_id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    meeting_count: Optional[int] = None  # Computed field

    class Config:
        from_attributes = True


# ============================================================================
# Class Meeting Schemas (replaces Session)
# ============================================================================

class ClassMeetingCreate(BaseModel):
    """Create a new class meeting."""
    title: str = Field(..., min_length=1, max_length=200)
    password: Optional[str] = Field(None, min_length=4, max_length=50)


class ClassMeetingResponse(BaseModel):
    """Class meeting with codes."""
    id: int
    class_id: int
    api_key_id: Optional[int]
    meeting_code: str
    instructor_code: str
    title: str
    has_password: bool
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    is_active: bool
    question_count: Optional[int] = None  # Computed field
    student_url: Optional[str] = None  # Computed field
    instructor_url: Optional[str] = None  # Computed field
    class_name: Optional[str] = None  # Computed field

    class Config:
        from_attributes = True


# ============================================================================
# Question Schemas
# ============================================================================

class QuestionCreate(BaseModel):
    """Submit a new question."""
    text: str = Field(..., min_length=1, max_length=1000)


class QuestionUpdate(BaseModel):
    """Update question status (instructor only)."""
    status: Optional[str] = Field(None, pattern="^(pending|approved|rejected|flagged)$")
    is_answered_in_class: Optional[bool] = None


class QuestionResponse(BaseModel):
    """Question with metadata."""
    id: int
    meeting_id: int
    student_id: str
    question_number: int
    text: str  # Sanitized for students, original for instructor
    sanitized_text: Optional[str] = None  # Censored version for display to instructors
    upvotes: int
    status: str
    flagged_reason: Optional[str]
    is_answered_in_class: bool
    has_written_answer: bool
    created_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuestionWithAnswer(QuestionResponse):
    """Question with answer included."""
    answer: Optional['AnswerResponse'] = None

    class Config:
        from_attributes = True


# ============================================================================
# Answer Schemas
# ============================================================================

class AnswerCreate(BaseModel):
    """Create a written answer."""
    answer_text: str = Field(..., min_length=1, max_length=10000)
    is_approved: bool = False


class AnswerUpdate(BaseModel):
    """Update answer text or approval status."""
    answer_text: Optional[str] = Field(None, min_length=1, max_length=10000)
    is_approved: Optional[bool] = None


class AnswerResponse(BaseModel):
    """Answer with metadata."""
    id: int
    question_id: int
    instructor_id: int
    answer_text: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Question Vote Schemas
# ============================================================================

class QuestionVoteCreate(BaseModel):
    """Record a vote (internal, not exposed via API)."""
    student_id: str
    question_id: int


class QuestionVoteResponse(BaseModel):
    """Vote metadata."""
    id: int
    question_id: int
    student_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Composite Schemas
# ============================================================================

class ClassMeetingWithQuestions(ClassMeetingResponse):
    """Class meeting with questions included (with answers for approved ones)."""
    questions: List[QuestionWithAnswer] = []

    class Config:
        from_attributes = True


class ClassWithMeetings(ClassResponse):
    """Class with meetings included."""
    meetings: List[ClassMeetingResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# Authentication Schemas
# ============================================================================

class AdminLogin(BaseModel):
    """Admin login credentials."""
    username: str
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class SessionPasswordVerify(BaseModel):
    """Verify session password."""
    password: str


# ============================================================================
# Report/Export Schemas
# ============================================================================

class MeetingReport(BaseModel):
    """Full meeting report with statistics."""
    meeting: ClassMeetingResponse
    statistics: dict  # {total_questions, answered_in_class, written_answers, etc.}
    questions: List[QuestionWithAnswer]

    class Config:
        from_attributes = True


class ClassReport(BaseModel):
    """Full class report with all meetings."""
    class_info: ClassResponse
    meetings: List[MeetingReport]
    statistics: dict  # Aggregate stats across all meetings

    class Config:
        from_attributes = True


# ============================================================================
# Admin Instructor Management Schemas
# ============================================================================

class AdminInstructorListResponse(BaseModel):
    """Instructor list item for admin view."""
    id: int
    username: str
    email: Optional[str]
    display_name: Optional[str]
    role: str  # INSTRUCTOR, ADMIN, SUPER_ADMIN, INACTIVE
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
    role: str  # INSTRUCTOR, ADMIN, SUPER_ADMIN, INACTIVE
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


class BulkPasswordResetResult(BaseModel):
    """Single instructor password reset result."""
    instructor_id: int
    username: str
    display_name: Optional[str]
    temporary_password: str


class BulkPasswordResetResponse(BaseModel):
    """Response from bulk password reset."""
    message: str
    successful_count: int
    failed_count: int
    reset_results: List[BulkPasswordResetResult]


class InstructorExportStats(BaseModel):
    """Statistics for instructor export."""
    classes_count: int
    sessions_count: int
    questions_count: int
    upvotes_count: int
    unique_students_count: int


class InstructorExportData(BaseModel):
    """Instructor data for export."""
    id: int
    username: str
    email: Optional[str]
    display_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    badge: str
    stats: Optional[InstructorExportStats]

    class Config:
        from_attributes = True


class BulkInstructorActionRequest(BaseModel):
    """Request to perform bulk action on instructors."""
    instructor_ids: List[int] = Field(..., min_items=1, max_items=100)


class BulkActionResponse(BaseModel):
    """Response from bulk action."""
    message: str
    successful_count: int
    failed_count: int


# ============================================================================
# System Configuration Schemas
# ============================================================================

class ConfigUpdateRequest(BaseModel):
    """Request to update a system configuration value."""
    value: str
    description: Optional[str] = None


class ConfigResponse(BaseModel):
    """System configuration setting."""
    key: str
    value: str
    value_type: str
    parsed_value: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    updated_by: str

    class Config:
        from_attributes = True


class RegistrationToggleRequest(BaseModel):
    """Request to toggle instructor registration."""
    enabled: bool
    reason: Optional[str] = None


