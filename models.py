from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets

Base = declarative_base()


class APIKey(Base):
    """API keys for instructor authentication."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)  # Human-readable name for the key
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    @staticmethod
    def generate_key():
        """Generate a secure API key."""
        return f"rmh_{secrets.token_urlsafe(32)}"


class Session(Base):
    """A Q&A session for a class."""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_code = Column(String, unique=True, index=True, nullable=False)
    instructor_code = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)  # Optional session password
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan")

    @staticmethod
    def generate_code(length=32):
        """Generate a random alphanumeric code."""
        return secrets.token_urlsafe(length)[:length]


class Question(Base):
    """A question submitted by a student."""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    question_number = Column(Integer, nullable=False)  # Permanent display number (e.g., Q1, Q2, Q3)
    text = Column(Text, nullable=False)
    upvotes = Column(Integer, default=0)
    is_answered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)

    session = relationship("Session", back_populates="questions")
