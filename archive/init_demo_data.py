#!/usr/bin/env python3
"""Initialize database with demo data for testing."""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_v2 import Base, Instructor, Class, ClassMeeting, APIKey
from passlib.context import CryptContext
from datetime import datetime
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_demo_data():
    """Initialize database with demo instructor, class, and meeting."""
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if demo instructor already exists
        existing = db.query(Instructor).filter(Instructor.username == "demo").first()
        if existing:
            print("✓ Demo instructor already exists")
            instructor = existing
        else:
            # Create demo instructor
            instructor = Instructor(
                username="demo",
                email="demo@example.com",
                display_name="Demo Instructor",
                password_hash=pwd_context.hash("demo123"),
                created_at=datetime.utcnow(),
                is_active=True
            )
            db.add(instructor)
            db.commit()
            db.refresh(instructor)
            print(f"✓ Created demo instructor (username: demo, password: demo123)")
        
        # Create API key
        existing_key = db.query(APIKey).filter(APIKey.instructor_id == instructor.id).first()
        if existing_key:
            print(f"✓ API key already exists: {existing_key.key}")
            api_key = existing_key
        else:
            api_key = APIKey(
                instructor_id=instructor.id,
                key=APIKey.generate_key(),
                name="Demo API Key",
                created_at=datetime.utcnow(),
                is_active=True
            )
            db.add(api_key)
            db.commit()
            db.refresh(api_key)
            print(f"✓ Created API key: {api_key.key}")
        
        # Create demo class
        existing_class = db.query(Class).filter(Class.instructor_id == instructor.id).first()
        if existing_class:
            print(f"✓ Demo class already exists: {existing_class.name}")
            demo_class = existing_class
        else:
            demo_class = Class(
                instructor_id=instructor.id,
                name="Introduction to Computer Science",
                description="CS 101 - Demo Course",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_archived=False
            )
            db.add(demo_class)
            db.commit()
            db.refresh(demo_class)
            print(f"✓ Created demo class: {demo_class.name}")
        
        # Create demo meeting
        existing_meeting = db.query(ClassMeeting).filter(ClassMeeting.meeting_code == "DEMO2025").first()
        if existing_meeting:
            print(f"✓ Demo meeting already exists")
            meeting = existing_meeting
        else:
            meeting = ClassMeeting(
                class_id=demo_class.id,
                api_key_id=api_key.id,
                meeting_code="DEMO2025",
                instructor_code="INSTRUCTOR2025",
                title="Demo Meeting - No Password",
                password_hash=None,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                is_active=True
            )
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            print(f"✓ Created demo meeting")
        
        print("\n" + "="*70)
        print("🎉 Demo data initialized successfully!")
        print("="*70)
        print(f"\n📚 Instructor Login:")
        print(f"   Username: demo")
        print(f"   Password: demo123")
        print(f"\n🔑 API Key:")
        print(f"   {api_key.key}")
        print(f"\n👨‍🎓 Student URL:")
        print(f"   http://localhost:8000/student?code=DEMO2025")
        print(f"\n👩‍🏫 Instructor URL:")
        print(f"   http://localhost:8000/instructor?code=INSTRUCTOR2025")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    init_demo_data()
