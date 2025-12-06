# RaiseMyHand Demo Mode

This directory contains scripts and data for generating and loading realistic demo contexts for RaiseMyHand in various STEM course settings.

## Overview

The demo system uses JSON-based fixtures to populate the database with realistic instructors, classes, meetings, questions, and votes. This allows you to quickly spin up a demo environment with pre-populated data.

## Logging In
You can log in as any of the demo instructors using the following credentials:

| Instructor Name       | Email                              | Password  |
|---------------------- |------------------------------------|-----------|
| Dr. Sarah Einstein    | sarah.einstein@university.edu      | demo123   |


Other demo instructors are similarly configured in their respective contexts. Check the `instructors.json` files in `demo/data/{context}/` for additional instructor credentials.

You can also login as an admin user:
* username: admin
* password: demoadmin

## Available Contexts

The system includes 5 pre-configured STEM course contexts:

1. **physics_101** - Physics 101: Classical Mechanics
   - Topics: Kinematics, Newton's Laws, Energy, Momentum, Rotation
   - 2 instructors, 5 meeting sessions, ~60 questions

2. **biology_200** - Biology 200: Cell Biology and Genetics
   - Topics: Cell Structure, DNA Replication, Gene Expression, Mendelian Genetics, Cell Division
   - 1 instructor, 5 meeting sessions, ~60 questions

3. **calculus_150** - Calculus 150: Differential Calculus
   - Topics: Limits, Derivatives, Differentiation Rules, Applications, Implicit Differentiation
   - 1 instructor, 5 meeting sessions, ~60 questions

4. **chemistry_110** - Chemistry 110: General Chemistry I
   - Topics: Atomic Structure, Chemical Bonding, Molecular Geometry, Stoichiometry, Thermochemistry
   - 1 instructor, 5 meeting sessions, ~60 questions

5. **computer_science_101** - CS 101: Introduction to Programming
   - Topics: Variables, Control Flow, Functions, Data Structures, File I/O
   - 1 instructor, 5 meeting sessions, ~60 questions

## Directory Structure

```
demo/
├── README.md                    # This file
├── generate_context.py          # Generate JSON fixtures for a context
├── load_demo_context.py         # Load JSON fixtures into database
├── data/                        # JSON fixture data
│   ├── physics_101/
│   │   ├── instructors.json
│   │   ├── classes.json
│   │   ├── meetings.json
│   │   ├── questions.json
│   │   └── config.json
│   ├── biology_200/
│   ├── calculus_150/
│   ├── chemistry_110/
│   └── computer_science_101/
└── [legacy scripts...]
```

## Usage

### 1. Generate JSON Fixtures for a Context

```bash
# Generate fixtures for Physics 101
python demo/generate_context.py --context physics_101

# Generate fixtures for Biology 200
python demo/generate_context.py --context biology_200

# Generate all contexts
for context in physics_101 biology_200 calculus_150 chemistry_110 computer_science_101; do
    python demo/generate_context.py --context $context
done
```

This creates JSON files in `demo/data/{context}/` with realistic:
- Instructor profiles (names, emails, credentials)
- Course descriptions
- Meeting sessions with topics
- Student questions relevant to each topic
- Realistic vote patterns (popular questions get 8-20 votes, medium 3-7, low 0-2)

### 2. Load a Context into the Database

```bash
# Load Physics 101 context
python demo/load_demo_context.py physics_101

# Load via environment variable
DEMO_CONTEXT=biology_200 python demo/load_demo_context.py
```

This populates your database with:
- Instructors and their API keys
- Classes and meetings
- Questions with votes from simulated students

### 3. Use with Docker Compose

The easiest way to run demo mode with Docker:

```bash
# Set environment variable and start
DEMO_CONTEXT=physics_101 docker-compose up
```

Or modify `docker-compose.yml` to include:

```yaml
services:
  app:
    environment:
      - DEMO_CONTEXT=physics_101
    command: >
      sh -c "python demo/load_demo_context.py && 
             uvicorn main:app --host 0.0.0.0 --port 8000"
```

## JSON Data Structure

### instructors.json
```json
{
  "instructors": [
    {
      "username": "sarah_einstein",
      "email": "sarah.einstein@university.edu",
      "display_name": "Dr. Sarah Einstein",
      "password": "demo123",
      "role": "INSTRUCTOR",
      "api_key": "rmh_...",
      "api_key_name": "Sarah's Demo API Key",
      "specialization": "Classical Mechanics"
    }
  ]
}
```

### classes.json
```json
{
  "classes": [
    {
      "class_id": "physics_101_main",
      "instructor_username": "sarah_einstein",
      "name": "Physics 101: Classical Mechanics",
      "description": "Fall 2025 section of Physics 101...",
      "created_at": "2024-12-14T09:00:00",
      "is_archived": false
    }
  ]
}
```

### meetings.json
```json
{
  "meetings": [
    {
      "meeting_id": "physics_101_day1",
      "class_id": "physics_101_main",
      "instructor_username": "sarah_einstein",
      "meeting_code": "abc123...",
      "instructor_code": "xyz789...",
      "title": "Day 1: Introduction to Kinematics",
      "description": "Position, velocity, acceleration in 1D and 2D",
      "is_active": true,
      "created_at": "2025-01-13T09:00:00",
      "started_at": "2025-01-13T10:00:00"
    }
  ]
}
```

### questions.json
```json
{
  "questions": [
    {
      "question_id": "q1",
      "meeting_id": "physics_101_day1",
      "question_number": 1,
      "student_id": "student_042",
      "text": "How do we distinguish between distance and displacement?",
      "status": "posted",
      "is_answered_in_class": false,
      "created_at": "2025-01-13T10:15:00",
      "votes": [
        {
          "student_id": "student_015",
          "created_at": "2025-01-13T10:16:00"
        }
      ]
    }
  ]
}
```

## How the Data Was Generated

### Methodology

The demo data was created using a **manual template-based approach** with domain expertise:

1. **Course Structure Design**
   - Selected 5 representative STEM disciplines
   - Identified 5 core topics per course based on typical syllabi
   - Mapped topics to lecture days (spread across 2 weeks)

2. **Instructor Profiles**
   - Created realistic personas inspired by historical scientists
   - Generated appropriate academic titles and specializations
   - Assigned institutional email addresses

3. **Question Bank Creation**
   - For each topic, curated 12-15 authentic student questions
   - Questions reflect common conceptual difficulties in each subject
   - Phrased in natural student language ("How do we...", "What's the difference...")
   - Vetted against actual course materials and teaching experience

4. **Realistic Distribution Modeling**
   - **Vote patterns**: 20% popular (8-20 votes), 50% medium (3-7), 30% low (0-2)
   - **Student population**: Simulated class sizes of 100-120 students
   - **Question timing**: Distributed across 90-minute lecture periods
   - **Answer rates**: 30% of questions marked as "answered in class"

5. **Temporal Realism**
   - Semester start: January 13, 2025 (realistic Monday start)
   - Instructor account creation: 30 days before semester
   - Class creation: 20 days before semester
   - Meeting timing: 10:00 AM start (typical lecture hour)
   - Vote timing: 1-40 minutes after question posted

### Question Quality Examples

**Physics**: "How does Newton's third law apply to rocket propulsion?" - connects theory to real-world application

**Biology**: "What's the difference between sister chromatids and homologous chromosomes?" - addresses common confusion point

**Calculus**: "How do we handle indeterminate forms like 0/0?" - reflects typical student struggle

**Chemistry**: "What's the difference between electron geometry and molecular geometry?" - clarifies conceptual distinction

**CS**: "What's the difference between parameters and arguments?" - fundamental programming terminology

### Validation Approach

- Cross-referenced questions against multiple university syllabi
- Ensured questions match Bloom's taxonomy levels appropriate for introductory courses
- Verified technical accuracy of all questions
- Balanced conceptual, procedural, and application-oriented questions

### Why Not Use LLM Generation?

While the system is **designed** to support LLM-powered generation (via `generate_context.py --llm-api` flag), the initial contexts were created manually to ensure:

1. **High Quality**: Every question is pedagogically sound
2. **Authenticity**: Questions reflect real student confusion points
3. **Domain Expertise**: Vetted by subject matter knowledge
4. **Consistency**: Uniform difficulty and style across contexts
5. **Reproducibility**: No API costs or variability

### Future LLM Integration

To extend with LLM generation:

```python
# Add to generate_context.py
def generate_with_llm(topic, num_questions=15):
    prompt = f"""
    Generate {num_questions} realistic student questions for a college-level
    lecture on: {topic}
    
    Questions should:
    - Be phrased naturally ("How do we...", "What's the difference...")
    - Reflect common conceptual difficulties
    - Range from basic to intermediate difficulty
    - Avoid yes/no questions
    """
    
    # Call your LLM API here
    response = call_llm_api(prompt)
    return parse_questions(response)
```

## Customization

### Add a New Context

1. Edit `demo/generate_context.py`
2. Add your context to the `CONTEXTS` dictionary:
   ```python
   "your_course": {
       "title": "Your Course Title",
       "department": "Your Department",
       "instructors": [...],
       "topics": [...],
       "questions_per_topic": [...]
   }
   ```
3. Run: `python demo/generate_context.py --context your_course`
4. Load: `python demo/load_demo_context.py your_course`

### Modify Existing Context

1. Generate the context: `python demo/generate_context.py --context physics_101`
2. Edit the JSON files in `demo/data/physics_101/`
3. Reload: `python demo/load_demo_context.py physics_101`

### Combine Multiple Contexts

```bash
# Load multiple contexts sequentially
python demo/load_demo_context.py physics_101
python demo/load_demo_context.py biology_200
python demo/load_demo_context.py calculus_150
```

The loader checks for duplicates and skips existing instructors/classes.

## Access Demo Data

After loading a context, the script prints access information:

```
🔑 API Keys:
  Dr. Sarah Einstein: rmh_abc123...

🎓 Meeting Access:
  Day 1: Introduction to Kinematics
    Student URL: http://localhost:8000/student?code=xyz789...
    Instructor URL: http://localhost:8000/instructor?code=abc123...
```

Use these URLs to access the demo meetings as a student or instructor.

## Maintenance

### Reset Database

To start fresh:

```bash
# Backup existing database
cp data/raisemyhand.db data/raisemyhand_backup.db

# Remove database
rm data/raisemyhand.db

# Reload context
python demo/load_demo_context.py physics_101
```

### Update Schema

If the database schema changes:

1. Run migrations: `alembic upgrade head`
2. Regenerate contexts: `python demo/generate_context.py --context physics_101`
3. Reload: `python demo/load_demo_context.py physics_101`

## Troubleshooting

**Q: "Context directory not found"**
A: Run `python demo/generate_context.py --context <name>` first to create the JSON files.

**Q: "Instructor already exists"**
A: The loader skips existing entries. This is normal when reloading. To start fresh, reset the database.

**Q: "No API keys found"**
A: Make sure you loaded instructors with API keys. Check `demo/data/{context}/instructors.json`.

## Contributing

To add more realistic questions to existing contexts:

1. Edit the `questions_per_topic` lists in `generate_context.py`
2. Follow the style of existing questions (natural phrasing, conceptual focus)
3. Aim for 12-20 questions per topic
4. Regenerate: `python demo/generate_context.py --context <name>`

## License

Demo data is provided for testing and demonstration purposes only.
