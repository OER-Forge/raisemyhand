#!/usr/bin/env python3
"""
Generate demo data for CMSE 101 Day 01
- Creates 10 student questions
- Generates 100 students randomly upvoting questions
"""

import requests
import random
import string
from typing import List

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "rmh_H9uxP7igW-8VcIaefzpsjIM1Z5T7sMUdiKYn4Sr7qTc"
MEETING_CODE = "b66mfp3BfNxrHRXAHR082GJ8iDI3W9qK"

# Sample questions for CMSE 101 Day 01 - What is Data?
QUESTIONS = [
    "What are the different types of data we'll be working with?",
    "How do we distinguish between structured and unstructured data?",
    "Can you give examples of real-world data sources?",
    "What's the difference between qualitative and quantitative data?",
    "How do we measure data quality?",
    "What are common data formats and their pros/cons?",
    "How does data volume affect our analysis approach?",
    "What are the ethical considerations when collecting data?",
    "How do we handle missing or incomplete data?",
    "What tools are best for exploring data initially?",
]

def generate_student_id() -> str:
    """Generate a random student ID"""
    return "student_" + ''.join(random.choices(string.ascii_letters + string.digits, k=12))

def post_question(student_name: str, question_text: str) -> dict:
    """Post a question to the API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "student_name": student_name,
        "text": question_text
    }
    
    response = requests.post(
        f"{BASE_URL}/api/meetings/{MEETING_CODE}/questions",
        headers=headers,
        json=data
    )
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Error posting question: {response.status_code} - {response.text}")
        return None

def upvote_question(student_id: str, question_id: int) -> bool:
    """Upvote a question"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }
    
    response = requests.post(
        f"{BASE_URL}/api/questions/{question_id}/vote",
        headers=headers,
        params={"student_id": student_id}
    )
    
    return response.status_code in [200, 201]

def main():
    print("=" * 60)
    print("Generating Demo Data for CMSE 101 Day 01")
    print("=" * 60)
    
    # Step 1: Post all 10 questions
    print("\nStep 1: Creating 10 student questions...")
    question_ids = []
    
    for i, question_text in enumerate(QUESTIONS, 1):
        student_name = f"Student_{i}"
        result = post_question(student_name, question_text)
        
        if result:
            question_id = result.get('id')
            question_ids.append(question_id)
            print(f"  ✓ Question {i}: '{question_text}' (ID: {question_id})")
        else:
            print(f"  ✗ Failed to post question {i}")
    
    print(f"\nSuccessfully created {len(question_ids)} questions")
    
    # Step 2: Generate 100 students with random upvotes
    print("\nStep 2: Generating 100 students with random upvotes...")
    
    total_votes = 0
    for student_num in range(1, 101):
        student_id = generate_student_id()
        
        # Each student randomly votes on 2-7 questions
        num_votes = random.randint(2, 7)
        voted_questions = random.sample(question_ids, min(num_votes, len(question_ids)))
        
        for question_id in voted_questions:
            if upvote_question(student_id, question_id):
                total_votes += 1
        
        if student_num % 10 == 0:
            print(f"  ✓ Created student {student_num}/100 with upvotes")
    
    print(f"\nSuccessfully generated {total_votes} upvotes from 100 students")
    
    # Step 3: Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  - Questions created: {len(question_ids)}")
    print(f"  - Students generated: 100")
    print(f"  - Total upvotes: {total_votes}")
    print(f"  - Meeting code: {MEETING_CODE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
