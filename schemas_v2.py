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

class APIKeyCreate(BaseModel):
    """Create a new API key."""
    name: str = Field(..., min_length=1, max_length=100)


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
    """Class meeting with questions included."""
    questions: List[QuestionResponse] = []

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
