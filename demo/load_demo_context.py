#!/usr/bin/env python3
"""
Load demo context from JSON files into database.
Usage: python demo/load_demo_context.py [context_name]
If no context specified, uses DEMO_CONTEXT environment variable or 'physics_101' default.
"""
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models_v2 import Base, Instructor, Class, ClassMeeting, APIKey, Question, QuestionVote
from models_config import SystemConfig  # Import at top for table creation
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class DemoContextLoader:
    """Load demo context from JSON files."""
    
    def __init__(self, context_name: str):
        self.context_name = context_name
        self.context_dir = Path(__file__).parent / "data" / context_name
        
        if not self.context_dir.exists():
            raise ValueError(f"Context directory not found: {self.context_dir}")
        
        # Map to store references by name for relationship resolution
        self.instructor_map = {}
        self.class_map = {}
        self.meeting_map = {}
        self.api_key_map = {}
    
    def load_json(self, filename: str) -> dict:
        """Load JSON file from context directory."""
        filepath = self.context_dir / filename
        if not filepath.exists():
            return {}
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def load_instructors(self, db):
        """Load instructors from instructors.json."""
        data = self.load_json("instructors.json")
        if not data or "instructors" not in data:
            return
        
        print(f"\n📚 Loading {len(data['instructors'])} instructors...")
        
        for inst_data in data["instructors"]:
            # Check if instructor already exists
            existing = db.query(Instructor).filter(
                Instructor.username == inst_data["username"]
            ).first()
            
            if existing:
                print(f"  ⚠ Instructor '{inst_data['username']}' already exists, skipping")
                self.instructor_map[inst_data["username"]] = existing
                continue
            
            instructor = Instructor(
                username=inst_data["username"],
                email=inst_data.get("email"),
                display_name=inst_data.get("display_name"),
                password_hash=pwd_context.hash(inst_data.get("password", "demo123")),
                created_at=datetime.fromisoformat(inst_data.get("created_at", datetime.utcnow().isoformat())),
                is_active=inst_data.get("is_active", True),
                role=inst_data.get("role", "INSTRUCTOR")
            )
            db.add(instructor)
            db.flush()  # Get ID without committing
            
            self.instructor_map[inst_data["username"]] = instructor
            print(f"  ✓ Created instructor: {instructor.display_name} (@{instructor.username})")
        
        db.commit()
    
    def load_api_keys(self, db):
        """Load API keys from instructors.json."""
        data = self.load_json("instructors.json")
        if not data or "instructors" not in data:
            return
        
        print(f"\n🔑 Loading API keys...")
        
        for inst_data in data["instructors"]:
            instructor = self.instructor_map.get(inst_data["username"])
            if not instructor:
                continue
            
            # Check if this instructor already has API keys
            existing_key = db.query(APIKey).filter(
                APIKey.instructor_id == instructor.id
            ).first()
            
            if existing_key:
                print(f"  ⚠ API key for '{inst_data['username']}' already exists")
                self.api_key_map[inst_data["username"]] = existing_key
                continue
            
            # Create API key
            api_key = APIKey(
                instructor_id=instructor.id,
                key=inst_data.get("api_key", APIKey.generate_key()),
                name=inst_data.get("api_key_name", f"{instructor.display_name}'s API Key"),
                created_at=datetime.utcnow(),
                is_active=True
            )
            db.add(api_key)
            db.flush()
            
            self.api_key_map[inst_data["username"]] = api_key
            print(f"  ✓ Created API key for {instructor.display_name}: {api_key.key}")
        
        db.commit()
    
    def load_classes(self, db):
        """Load classes from classes.json."""
        data = self.load_json("classes.json")
        if not data or "classes" not in data:
            return
        
        print(f"\n📖 Loading {len(data['classes'])} classes...")
        
        for class_data in data["classes"]:
            instructor = self.instructor_map.get(class_data["instructor_username"])
            if not instructor:
                print(f"  ⚠ Instructor '{class_data['instructor_username']}' not found, skipping class")
                continue
            
            # Check if class already exists
            existing = db.query(Class).filter(
                Class.instructor_id == instructor.id,
                Class.name == class_data["name"]
            ).first()
            
            if existing:
                print(f"  ⚠ Class '{class_data['name']}' already exists, skipping")
                self.class_map[class_data["class_id"]] = existing
                continue
            
            class_obj = Class(
                instructor_id=instructor.id,
                name=class_data["name"],
                description=class_data.get("description", ""),
                created_at=datetime.fromisoformat(class_data.get("created_at", datetime.utcnow().isoformat())),
                updated_at=datetime.utcnow(),
                is_archived=class_data.get("is_archived", False)
            )
            db.add(class_obj)
            db.flush()
            
            self.class_map[class_data["class_id"]] = class_obj
            print(f"  ✓ Created class: {class_obj.name}")
        
        db.commit()
    
    def load_meetings(self, db):
        """Load meetings from meetings.json."""
        data = self.load_json("meetings.json")
        if not data or "meetings" not in data:
            return
        
        print(f"\n🎓 Loading {len(data['meetings'])} class meetings...")
        
        for meeting_data in data["meetings"]:
            class_obj = self.class_map.get(meeting_data["class_id"])
            if not class_obj:
                print(f"  ⚠ Class ID '{meeting_data['class_id']}' not found, skipping meeting")
                continue
            
            # Get API key for instructor
            instructor_username = meeting_data.get("instructor_username")
            api_key = self.api_key_map.get(instructor_username)
            
            # Check if meeting already exists
            existing = db.query(ClassMeeting).filter(
                ClassMeeting.meeting_code == meeting_data["meeting_code"]
            ).first()
            
            if existing:
                print(f"  ⚠ Meeting '{meeting_data['title']}' already exists, skipping")
                self.meeting_map[meeting_data["meeting_id"]] = existing
                continue
            
            meeting = ClassMeeting(
                class_id=class_obj.id,
                api_key_id=api_key.id if api_key else None,
                meeting_code=meeting_data["meeting_code"],
                instructor_code=meeting_data["instructor_code"],
                title=meeting_data["title"],
                password_hash=pwd_context.hash(meeting_data["password"]) if meeting_data.get("password") else None,
                created_at=datetime.fromisoformat(meeting_data.get("created_at", datetime.utcnow().isoformat())),
                started_at=datetime.fromisoformat(meeting_data.get("started_at", datetime.utcnow().isoformat())),
                is_active=meeting_data.get("is_active", True)
            )
            db.add(meeting)
            db.flush()
            
            self.meeting_map[meeting_data["meeting_id"]] = meeting
            print(f"  ✓ Created meeting: {meeting.title} (code: {meeting.meeting_code})")
        
        db.commit()
    
    def load_questions(self, db):
        """Load questions from questions.json."""
        data = self.load_json("questions.json")
        if not data or "questions" not in data:
            return
        
        print(f"\n❓ Loading {len(data['questions'])} questions...")
        
        question_map = {}
        for q_data in data["questions"]:
            meeting = self.meeting_map.get(q_data["meeting_id"])
            if not meeting:
                print(f"  ⚠ Meeting ID '{q_data['meeting_id']}' not found, skipping question")
                continue
            
            # Check if question already exists
            existing = db.query(Question).filter(
                Question.meeting_id == meeting.id,
                Question.question_number == q_data["question_number"]
            ).first()
            
            if existing:
                question_map[q_data.get("question_id", f"{q_data['meeting_id']}_q{q_data['question_number']}")] = existing
                continue
            
            question = Question(
                meeting_id=meeting.id,
                student_id=q_data.get("student_id", f"student_{q_data['question_number']:03d}"),
                question_number=q_data["question_number"],
                text=q_data["text"],
                sanitized_text=q_data["text"],  # Same as text for demo (no profanity)
                status="approved",  # Demo questions are pre-approved
                upvotes=0,  # Will be calculated from votes
                created_at=datetime.fromisoformat(q_data.get("created_at", datetime.utcnow().isoformat())),
                is_answered_in_class=q_data.get("is_answered_in_class", False)
            )
            db.add(question)
            db.flush()
            
            question_map[q_data.get("question_id", f"{q_data['meeting_id']}_q{q_data['question_number']}")] = question
            
            # Add votes if specified
            if "votes" in q_data:
                for vote_data in q_data["votes"]:
                    vote = QuestionVote(
                        question_id=question.id,
                        student_id=vote_data["student_id"],
                        created_at=datetime.fromisoformat(vote_data.get("created_at", datetime.utcnow().isoformat()))
                    )
                    db.add(vote)
                
                # Update upvotes count
                question.upvotes = len(q_data["votes"])
            
            if q_data["question_number"] % 5 == 0:
                print(f"  ✓ Loaded {q_data['question_number']} questions...")
        
        print(f"  ✓ Loaded all {len(data['questions'])} questions")
        db.commit()
    
    def load_system_config(self, db):
        """Load system configuration overrides from config.json."""
        data = self.load_json("config.json")
        if not data or "config" not in data:
            return
        
        print(f"\n⚙️  Loading system configuration...")
        
        for config_data in data["config"]:
            SystemConfig.set_value(
                db,
                key=config_data["key"],
                value=config_data["value"],
                value_type=config_data.get("value_type", "string"),
                description=config_data.get("description", ""),
                updated_by="demo_loader"
            )
            print(f"  ✓ Set config: {config_data['key']} = {config_data['value']}")
    
    def load_all(self):
        """Load entire demo context."""
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            print("="*70)
            print(f"🎯 Loading Demo Context: {self.context_name}")
            print("="*70)
            
            self.load_instructors(db)
            self.load_api_keys(db)
            self.load_classes(db)
            self.load_meetings(db)
            self.load_questions(db)
            self.load_system_config(db)
            
            print("\n" + "="*70)
            print("✅ Demo context loaded successfully!")
            print("="*70)
            
            # Print summary
            print(f"\n📊 Summary:")
            print(f"  Instructors: {len(self.instructor_map)}")
            print(f"  API Keys: {len(self.api_key_map)}")
            print(f"  Classes: {len(self.class_map)}")
            print(f"  Meetings: {len(self.meeting_map)}")
            
            if self.api_key_map:
                print(f"\n🔑 API Keys:")
                for username, api_key in self.api_key_map.items():
                    instructor = self.instructor_map[username]
                    print(f"  {instructor.display_name}: {api_key.key}")
            
            if self.meeting_map:
                print(f"\n🎓 Meeting Access:")
                for meeting_id, meeting in self.meeting_map.items():
                    print(f"  {meeting.title}")
                    print(f"    Student URL: {settings.base_url}/student?code={meeting.meeting_code}")
                    print(f"    Instructor URL: {settings.base_url}/instructor?code={meeting.instructor_code}")
            
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error loading demo context: {e}")
            db.rollback()
            raise
        finally:
            db.close()


def main():
    """Main entry point."""
    context_name = None
    
    # Check command line argument
    if len(sys.argv) > 1:
        context_name = sys.argv[1]
    
    # Check environment variable
    if not context_name:
        context_name = os.getenv("DEMO_CONTEXT")
    
    # Default
    if not context_name:
        context_name = "physics_101"
    
    print(f"Loading demo context: {context_name}")
    
    loader = DemoContextLoader(context_name)
    loader.load_all()


if __name__ == "__main__":
    main()
