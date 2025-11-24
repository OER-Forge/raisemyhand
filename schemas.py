from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SessionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class SessionResponse(BaseModel):
    id: int
    session_code: str
    instructor_code: str
    title: str
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
