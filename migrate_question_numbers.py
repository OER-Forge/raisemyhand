"""
Migration script to add question_number field to questions table.
This ensures each question gets a permanent sequential number within its session.
"""

import sqlite3
import sys
from pathlib import Path

def migrate():
    # Get database path from environment or use default
    db_path = Path("data/raisemyhand.db")
    
    if not db_path.exists():
        print(f"✓ Database not found at {db_path}, skipping migration")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if question_number column already exists
        cursor.execute("PRAGMA table_info(questions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        column_exists = 'question_number' in columns
        
        if not column_exists:
            print("Adding question_number column to questions table...")
            # Add the question_number column
            cursor.execute("ALTER TABLE questions ADD COLUMN question_number INTEGER")
        else:
            print("question_number column already exists")
        
        # Check if there are any NULL question_numbers (from existing questions)
        cursor.execute("SELECT COUNT(*) FROM questions WHERE question_number IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print("✓ All questions already have question numbers")
            return
        
        print(f"Assigning question numbers to {null_count} existing question(s)...")
        
        # Get all sessions and assign question numbers
        cursor.execute("SELECT DISTINCT session_id FROM questions ORDER BY session_id")
        sessions = cursor.fetchall()
        
        for (session_id,) in sessions:
            # Get all questions for this session ordered by creation time
            cursor.execute("""
                SELECT id FROM questions 
                WHERE session_id = ? 
                ORDER BY created_at ASC
            """, (session_id,))
            
            questions = cursor.fetchall()
            
            # Assign sequential question numbers
            for idx, (question_id,) in enumerate(questions, start=1):
                cursor.execute("""
                    UPDATE questions 
                    SET question_number = ? 
                    WHERE id = ?
                """, (idx, question_id))
        
        conn.commit()
        print(f"✓ Migration completed successfully!")
        print(f"  Processed {len(sessions)} session(s)")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
