#!/usr/bin/env python3
"""
Generate realistic questions for class meetings with randomized upvotes.
Creates questions relevant to each class/day topic.
"""

import sqlite3
import random
from datetime import datetime, timedelta

# Question templates for each meeting
QUESTIONS_BY_MEETING = {
    1: {  # Day 01 - Introduction to Jupyter Notebooks (CMSE 201)
        "title": "CMSE 201: Introduction to Jupyter Notebooks",
        "questions": [
            "How do I export a Jupyter notebook to PDF format?",
            "Can I use Jupyter notebooks for collaborative work with others in real-time?",
            "What's the difference between running code in a cell vs the entire notebook?",
            "How do I install and manage packages within Jupyter?",
            "Can Jupyter run code in languages other than Python?",
            "How do I create and organize cells effectively in a large notebook?",
            "What's the best way to document code using markdown in Jupyter?",
            "How do I debug errors in Jupyter more effectively?",
            "Can I execute shell commands directly in Jupyter notebooks?",
            "What are some best practices for notebook organization and structure?",
            "How do I share Jupyter notebooks with people who don't have Jupyter installed?",
            "Can I add interactive widgets to my Jupyter notebook?",
        ]
    },
    2: {  # Day 02 - Doing Math with Numpy and Arrays (CMSE 201)
        "title": "CMSE 201: Doing Math with Numpy and Arrays",
        "questions": [
            "How do I perform element-wise operations on numpy arrays?",
            "What's the difference between numpy arrays and Python lists?",
            "How do I reshape or flatten a multi-dimensional array?",
            "Can I perform matrix multiplication with numpy?",
            "How do I slice and index multi-dimensional arrays efficiently?",
            "What's broadcasting in numpy and how does it work?",
            "How do I compute statistical functions like mean, median, std on arrays?",
            "Can I use numpy for linear algebra operations?",
            "How do I save and load numpy arrays?",
            "What's the most efficient way to handle large arrays in memory?",
            "How do I vectorize operations for better performance?",
            "Can I use numpy for generating random numbers with specific distributions?",
        ]
    },
    3: {  # Day 01 - What is Data? (CMSE 101)
        "title": "CMSE 101: What is Data?",
        "questions": [
            "What counts as 'big data' and how does that affect analysis?",
            "How do we ensure data quality and accuracy?",
            "What's the difference between structured and unstructured data?",
            "How do you handle missing values in a dataset?",
            "What are the ethical considerations when collecting data?",
            "How do we protect privacy while working with personal data?",
            "What are common data formats and when should I use each?",
            "How do I identify and handle outliers in my data?",
            "What's the importance of data documentation and metadata?",
            "How do I validate that my dataset is representative?",
            "What biases can exist in collected data and how do we identify them?",
            "How do I clean and preprocess data for analysis?",
        ]
    },
    4: {  # Day 02 - What is Machine Learning? (CMSE 101)
        "title": "CMSE 101: What is Machine Learning?",
        "questions": [
            "What's the difference between supervised and unsupervised learning?",
            "How do I know which machine learning algorithm to use for my problem?",
            "What is overfitting and how do I prevent it?",
            "How do I evaluate if my model is performing well?",
            "What's the importance of training vs test datasets?",
            "Can machine learning models be biased, and how?",
            "What's the difference between classification and regression?",
            "How do I handle imbalanced classes in my dataset?",
            "What role does feature engineering play in machine learning?",
            "How do I interpret machine learning model predictions?",
            "What are common pitfalls when applying machine learning?",
            "How do I validate that my model will work on new data?",
        ]
    }
}

def generate_demo_data():
    """Generate realistic questions and upvotes for each class meeting."""
    db_path = '/Users/caballero/repos/software/raisemyhand/data/raisemyhand.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear existing questions for a fresh start
    print("Clearing existing questions...")
    cursor.execute("DELETE FROM question_votes")
    cursor.execute("DELETE FROM questions")
    conn.commit()

    # Get all meetings
    cursor.execute("""
        SELECT cm.id, cm.meeting_code, c.id, c.name, cm.created_at 
        FROM class_meetings cm 
        JOIN classes c ON cm.class_id = c.id 
        ORDER BY cm.id
    """)
    meetings = cursor.fetchall()

    total_questions = 0
    total_upvotes = 0

    for meeting_id, meeting_code, class_id, class_name, created_at_str in meetings:
        print(f"\nProcessing Meeting {meeting_id}: {class_name}")
        
        if meeting_id not in QUESTIONS_BY_MEETING:
            print(f"  ⚠ No questions defined for meeting {meeting_id}")
            continue
        
        # Parse the datetime string
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        
        meeting_config = QUESTIONS_BY_MEETING[meeting_id]
        questions_list = meeting_config["questions"]
        
        # Shuffle questions and select 8-12 for this meeting
        num_questions = random.randint(8, 12)
        selected_questions = random.sample(questions_list, min(num_questions, len(questions_list)))
        
        for q_idx, question_text in enumerate(selected_questions, 1):
            # Insert question with upvotes count (will be calculated from votes table)
            question_time = created_at + timedelta(minutes=random.randint(0, 120))
            cursor.execute("""
                INSERT INTO questions 
                (meeting_id, student_id, question_number, text, status, upvotes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting_id,
                f"student_{random.randint(1, 150):03d}",  # Simulate 150 students
                q_idx,
                question_text,
                "posted",  # status: posted, answered, duplicate, etc.
                0,  # Will be updated when votes are added
                question_time.isoformat()
            ))
            question_id = cursor.lastrowid
            
            # Add upvotes with realistic distribution
            # Some questions get many upvotes, most get a few, some get none
            # Realistic distribution: 15% no votes, 20% 1 vote, 20% 2 votes, etc.
            upvote_count = random.choices(
                [0, 1, 2, 3, 5, 8, 12, 18],
                weights=[15, 20, 20, 15, 15, 10, 4, 1],
                k=1
            )[0]
            
            # Track unique students who vote (simulate class of 150 students)
            voted_students = set()
            
            for _ in range(upvote_count):
                # Get a unique student to vote (no duplicates)
                while True:
                    student_id = f"student_{random.randint(1, 150):03d}"
                    if student_id not in voted_students:
                        voted_students.add(student_id)
                        break
                
                vote_time = question_time + timedelta(minutes=random.randint(1, 60))
                cursor.execute("""
                    INSERT INTO question_votes (question_id, student_id, created_at)
                    VALUES (?, ?, ?)
                """, (
                    question_id,
                    student_id,
                    vote_time.isoformat()
                ))
            
            # Update the upvotes count
            cursor.execute("UPDATE questions SET upvotes = ? WHERE id = ?", (upvote_count, question_id))
            
            print(f"  ✓ Q{q_idx}: {question_text[:60]}... ({upvote_count} upvotes)")
            total_questions += 1
            total_upvotes += upvote_count
        
        conn.commit()

    conn.close()
    
    print("\n" + "="*60)
    print(f"✓ Generated {total_questions} questions with {total_upvotes} total upvotes")
    print(f"✓ Average upvotes per question: {total_upvotes/total_questions:.1f}")
    print("="*60)

if __name__ == "__main__":
    generate_demo_data()
