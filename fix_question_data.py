#!/usr/bin/env python3
"""
Fix existing question records with missing data.
"""
import sqlite3

def fix_data():
    conn = sqlite3.connect('raisemyhand.db')
    cursor = conn.cursor()
    
    # Find questions with missing session_id
    cursor.execute("SELECT id, text FROM questions WHERE session_id IS NULL")
    broken_questions = cursor.fetchall()
    
    if broken_questions:
        print(f"Found {len(broken_questions)} questions with missing session_id")
        print("These questions will be deleted as they cannot be linked to a session:")
        for qid, text in broken_questions:
            print(f"  - Question {qid}: {text[:50]}...")
        
        # Delete these broken questions
        cursor.execute("DELETE FROM questions WHERE session_id IS NULL")
        print(f"Deleted {cursor.rowcount} broken questions")
    
    # Set default values for is_answered
    cursor.execute("UPDATE questions SET is_answered = 0 WHERE is_answered IS NULL")
    if cursor.rowcount > 0:
        print(f"Fixed {cursor.rowcount} questions with NULL is_answered")
    
    conn.commit()
    conn.close()
    print("Data fix completed!")

if __name__ == "__main__":
    fix_data()
