# RaiseMyHand v2.0 Schema Migration Guide

## Overview

This document outlines the database schema changes for RaiseMyHand v2.0, which introduces a hierarchical architecture and new features like content moderation and written answers.

---

## 🎯 Goals

1. **Persistent Instructor Identity** - Instructors have accounts, not just API keys
2. **Hierarchical Organization** - Instructor → Class → ClassMeeting → Question
3. **Content Moderation** - Profanity filtering and approval workflow
4. **Written Answers** - Instructors can provide markdown answers after class
5. **Vote Tracking** - Prevent duplicate votes with QuestionVote table

---

## 📊 Schema Changes

### New Tables

#### `instructors`
Persistent instructor accounts with login credentials.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | VARCHAR | Unique username (3-50 chars) |
| email | VARCHAR | Optional email (unique) |
| display_name | VARCHAR | Optional display name |
| password_hash | VARCHAR | Bcrypt hashed password |
| created_at | DATETIME | Account creation timestamp |
| last_login | DATETIME | Last login timestamp |
| is_active | BOOLEAN | Account status |

**Relationships:**
- One-to-many: API keys, classes, answers

#### `classes`
Course/class entities (e.g., "CS 101 - Fall 2024").

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| instructor_id | INTEGER | Foreign key → instructors.id |
| name | VARCHAR | Class name (e.g., "CS 101 - Fall 2024") |
| description | TEXT | Optional description |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |
| is_archived | BOOLEAN | Soft delete flag |

**Relationships:**
- Many-to-one: Instructor
- One-to-many: Class meetings

#### `class_meetings`
Individual class sessions (replaces `sessions` table).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| class_id | INTEGER | Foreign key → classes.id |
| api_key_id | INTEGER | Foreign key → api_keys.id (nullable) |
| meeting_code | VARCHAR | Unique code for students |
| instructor_code | VARCHAR | Unique code for instructor |
| title | VARCHAR | Meeting title (e.g., "Lecture 5") |
| password_hash | VARCHAR | Optional session password |
| created_at | DATETIME | Creation timestamp |
| started_at | DATETIME | When meeting started |
| ended_at | DATETIME | When meeting ended |
| is_active | BOOLEAN | Meeting status |

**Relationships:**
- Many-to-one: Class, API key
- One-to-many: Questions

#### `answers`
Written answers from instructors to questions.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| question_id | INTEGER | Foreign key → questions.id (unique) |
| instructor_id | INTEGER | Foreign key → instructors.id |
| answer_text | TEXT | Markdown-formatted answer |
| is_approved | BOOLEAN | Published to students |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**Relationships:**
- One-to-one: Question
- Many-to-one: Instructor

#### `question_votes`
Tracks individual votes to prevent duplicates.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| question_id | INTEGER | Foreign key → questions.id |
| student_id | VARCHAR | Anonymous UUID |
| created_at | DATETIME | Vote timestamp |

**Unique constraint:** (question_id, student_id)

**Relationships:**
- Many-to-one: Question

### Updated Tables

#### `api_keys` (modified)
Now tied to instructor accounts.

**Added columns:**
- `instructor_id` (INTEGER, FK → instructors.id, NOT NULL)

**Migration note:** Existing API keys will need to be associated with an instructor. Options:
1. Create a default "legacy" instructor for existing keys
2. Require re-creation of API keys after instructor registration

#### `questions` (modified)
Enhanced with moderation and tracking features.

**Added columns:**
- `meeting_id` (INTEGER, FK → class_meetings.id) - replaces `session_id`
- `student_id` (VARCHAR) - anonymous UUID for tracking
- `sanitized_text` (TEXT) - profanity-redacted version
- `status` (VARCHAR) - pending/approved/rejected/flagged
- `flagged_reason` (VARCHAR) - profanity/spam/inappropriate
- `is_answered_in_class` (BOOLEAN) - answered verbally
- `has_written_answer` (BOOLEAN) - has written answer
- `reviewed_at` (DATETIME) - when reviewed by instructor

**Removed columns:**
- `session_id` - replaced by `meeting_id`
- `is_answered` - split into `is_answered_in_class` + `has_written_answer`
- `answered_at` - removed (use Answer.created_at instead)

**Migration note:** Questions from v1 cannot be migrated directly due to missing `meeting_id`. Fresh start recommended.

### Removed Tables

#### `sessions` (removed)
Replaced by `class_meetings` table with additional hierarchy.

---

## 🔄 Migration Path

### Option A: Fresh Start (Recommended)

Since this is a development project without production data:

1. **Backup existing data** (if any)
   ```bash
   cp data/raisemyhand.db data/raisemyhand_v1_backup.db
   ```

2. **Create new database** with v2 schema
   ```bash
   # Delete old database
   rm data/raisemyhand.db

   # Run v2 migration
   alembic upgrade head
   ```

3. **Create admin instructor** (via API or script)

4. **Existing API keys** become invalid - instructors must:
   - Register for an account
   - Create new API keys

### Option B: Data Migration (If Needed)

If you need to preserve existing sessions/questions:

1. **Create migration script** (`scripts/migrate_v1_to_v2.py`):
   - Create default instructor account
   - Migrate API keys → associate with default instructor
   - Create default class ("Migrated Sessions")
   - Migrate sessions → class_meetings
   - Migrate questions (with synthetic student_id UUIDs)

2. **Run migration**
   ```bash
   python scripts/migrate_v1_to_v2.py
   ```

---

## 📝 Pydantic Schema Changes

### New Schemas (`schemas_v2.py`)

- `InstructorRegister`, `InstructorLogin`, `InstructorResponse`
- `ClassCreate`, `ClassUpdate`, `ClassResponse`, `ClassWithMeetings`
- `ClassMeetingCreate`, `ClassMeetingResponse`, `ClassMeetingWithQuestions`
- `AnswerCreate`, `AnswerUpdate`, `AnswerResponse`
- `QuestionVoteCreate`, `QuestionVoteResponse`

### Updated Schemas

- `QuestionResponse` - added moderation fields
- `QuestionWithAnswer` - includes answer
- `APIKeyResponse` - added `instructor_id`

---

## 🛠️ Required Code Changes

### 1. Update Imports

```python
# Old
from models import Session, Question, APIKey
from schemas import SessionCreate, QuestionResponse

# New
from models_v2 import ClassMeeting, Question, APIKey, Instructor, Class
from schemas_v2 import ClassMeetingCreate, QuestionResponse, InstructorRegister
```

### 2. New API Endpoints

Must implement:

**Instructor Management:**
- `POST /api/instructors/register` - Register new instructor
- `POST /api/instructors/login` - Login with username/password
- `GET /api/instructors/profile` - View profile
- `PUT /api/instructors/profile` - Update profile

**Class Management:**
- `POST /api/classes` - Create class
- `GET /api/classes` - List instructor's classes
- `GET /api/classes/{id}` - View class details
- `PUT /api/classes/{id}` - Update class
- `DELETE /api/classes/{id}` - Archive class

**Class Meetings:** (replaces session endpoints)
- `POST /api/classes/{class_id}/meetings` - Create meeting
- `GET /api/classes/{class_id}/meetings` - List meetings
- `GET /api/meetings/{meeting_code}` - Get meeting (for students)
- `POST /api/meetings/{id}/end` - End meeting

**Answers:**
- `POST /api/questions/{id}/answer` - Create answer
- `PUT /api/questions/{id}/answer` - Update answer
- `DELETE /api/questions/{id}/answer` - Delete answer
- `POST /api/questions/{id}/answer/publish` - Publish answer

**Question Moderation:**
- `POST /api/questions/{id}/review` - Approve/reject question
- `GET /api/meetings/{id}/flagged-questions` - List flagged questions

### 3. Update Frontend

**Major changes:**
- Replace "Create Session" → "Create Meeting" (requires class selection)
- Add "My Classes" dashboard
- Add instructor registration/login flow
- Add answer creation UI (markdown editor)
- Add question moderation panel
- Update WebSocket to use `meeting_code` instead of `session_code`

---

## 🔒 Security Considerations

### Instructor Authentication

**Two authentication methods:**

1. **Username/Password** (for web UI)
   - POST `/api/instructors/login` → JWT token
   - Store JWT in localStorage or cookie
   - Include in `Authorization: Bearer <token>` header

2. **API Key** (for programmatic access)
   - Include in query param: `?api_key=rmh_...`
   - Or header: `X-API-Key: rmh_...`

### Access Control

**Enforce ownership:**
- Instructors can only access their own classes/meetings
- Use `instructor_id` from JWT to filter queries
- Return 403 Forbidden for unauthorized access

**Example:**
```python
@app.get("/api/classes")
def list_classes(instructor_id: int = Depends(get_current_instructor)):
    return db.query(Class).filter(Class.instructor_id == instructor_id).all()
```

---

## 📋 Testing Checklist

### Database Migration

- [ ] Fresh database created with `alembic upgrade head`
- [ ] All tables exist with correct columns
- [ ] Foreign keys correctly defined
- [ ] Indexes created properly
- [ ] Unique constraints work (try duplicates)

### API Endpoints

- [ ] Instructor registration works
- [ ] Instructor login returns JWT
- [ ] Can create class
- [ ] Can create meeting within class
- [ ] Questions posted to meeting
- [ ] Answer CRUD operations work
- [ ] Voting creates QuestionVote records
- [ ] Duplicate votes prevented

### Frontend

- [ ] Registration/login flow works
- [ ] "My Classes" displays classes
- [ ] "Create Meeting" requires class selection
- [ ] Student join with meeting_code
- [ ] Questions display correctly
- [ ] Answer UI functional
- [ ] WebSocket updates work

---

## 🚀 Deployment Steps

### 1. Update Environment Variables

```bash
# .env
DATABASE_URL=sqlite:///./data/raisemyhand_v2.db  # New database
ENV=development
DEBUG=true

# Production
DATABASE_URL=postgresql://user:pass@host/raisemyhand_v2
ENV=production
DEBUG=false
```

### 2. Run Migration

```bash
# Development
alembic upgrade head

# Production (with Docker)
docker compose exec app alembic upgrade head
```

### 3. Create Admin Instructor

```bash
# Via API or script
curl -X POST http://localhost:8000/api/instructors/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password",
    "email": "admin@example.com",
    "display_name": "System Administrator"
  }'
```

### 4. Update Docker Compose

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/raisemyhand
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: raisemyhand
      POSTGRES_PASSWORD: password
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

---

## 📚 Additional Resources

- **ROADMAP.md** - Full v2.0 implementation roadmap
- **models_v2.py** - New database models
- **schemas_v2.py** - New Pydantic schemas
- **alembic/versions/** - Migration scripts

---

## ⚠️ Breaking Changes

### API Endpoints (v1 → v2)

| v1 Endpoint | v2 Endpoint | Notes |
|-------------|-------------|-------|
| POST /api/sessions | POST /api/classes/{id}/meetings | Requires class_id |
| GET /api/sessions/my-sessions | GET /api/classes | Returns classes, not sessions |
| GET /api/sessions/{code} | GET /api/meetings/{code} | Renamed table |
| POST /api/sessions/{code}/questions | POST /api/meetings/{code}/questions | Renamed |
| POST /api/questions/{id}/answer | POST /api/questions/{id}/mark-answered-in-class | Split functionality |
| N/A | POST /api/questions/{id}/answer | New: written answers |

### Database

- **sessions** table removed → use **class_meetings**
- **Question.session_id** → **Question.meeting_id**
- **Question.is_answered** → **Question.is_answered_in_class** + **Question.has_written_answer**

### Frontend

- Must update all API calls
- Must update WebSocket path (`/ws/{session_code}` → `/ws/{meeting_code}`)
- Must add class selection UI

---

## 🎓 Migration Timeline

**Estimated Effort:** 4-6 hours

1. **Database Migration** (30 min)
   - Run Alembic migration
   - Verify schema

2. **Backend API Updates** (2-3 hours)
   - Implement new endpoints
   - Update existing endpoints
   - Test with Postman/curl

3. **Frontend Updates** (1-2 hours)
   - Update JavaScript API calls
   - Add new UI components
   - Test in browser

4. **Testing & Bug Fixes** (1 hour)
   - End-to-end testing
   - Fix issues

---

**Questions?** See [ROADMAP.md](ROADMAP.md) for detailed implementation phases.
