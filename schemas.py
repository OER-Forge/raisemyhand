from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class InstructorAuth(BaseModel):
    api_key: str


class SessionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    password: Optional[str] = Field(None, min_length=4, max_length=50)


class SessionResponse(BaseModel):
    id: int
    session_code: str
    instructor_code: str
    title: str
    has_password: bool  # Don't expose actual password
    created_at: datetime
    ended_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class QuestionResponse(BaseModel):
    id: int
    session_id: int
    question_number: int
    text: str
    upvotes: int
    is_answered: bool
    created_at: datetime
    answered_at: Optional[datetime]

    class Config:
        from_attributes = True


class SessionWithQuestions(SessionResponse):
    questions: list[QuestionResponse] = []

    class Config:
        from_attributes = True


# Authentication Schemas
class AdminLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionPasswordVerify(BaseModel):
    password: str
