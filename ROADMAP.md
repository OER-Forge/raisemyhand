# RaiseMyHand Development Roadmap

**Last Updated:** 2025-12-04
**Current Status:** Phase 5 Complete (Navigation & UX)
**Commits Ahead:** 5 commits ready to push to origin/main

---

## 📊 Current State

### ✅ Completed Phases

**Phase 1-2: Security & Code Quality** (Complete)
- JWT authentication, CSRF protection, rate limiting
- Bcrypt password hashing, API key management
- Centralized logging system
- Code quality: 9.7/10

**Phase 3: v2 API Migration** (Complete)
- Hierarchical data model: Instructor → Class → Meeting → Question → Vote
- All v1 endpoints removed
- Database schema v2 fully implemented

**Phase 5: UX & Navigation** (Complete)
- ✅ Mobile-friendly hamburger menu navigation (Issue #28)
- ✅ Consistent navigation across all pages with ARIA labels
- ✅ Answered question indicators in student view
- ✅ Archive/unarchive class functionality
- ✅ Class meeting filter by class_id
- ✅ Stats endpoint v2 compatibility

**Phase 6: Mobile & Breadcrumbs** (Complete)
- ✅ Mobile responsiveness (Issue #25)
- ✅ Breadcrumb navigation (Issue #24)

### 📋 Test Results
- API Tests: 100% (18/18 passing)
- Navigation Tests: 100% (3/3 passing)
- WebSocket Tests: Passing

---

## 🗺️ Remaining Work

### **PHASE 4: Content Moderation** (2 issues)

#### Issue #19: Implement Profanity Filter
**Priority:** Medium
**Effort:** 4 hours
**Status:** Open

**Description:**
Add client-side and server-side profanity filtering for question submissions.

**Implementation Plan:**

1. **Choose Library**
   - Option A: `bad-words` (npm) - Simple, lightweight
   - Option B: `profanity-check` (Python) - More accurate
   - Recommendation: Use both for defense-in-depth

2. **Backend (Python) - routes_questions.py:19**
   ```python
   from profanity_check import predict

   @router.post("/api/meetings/{meeting_code}/questions")
   def create_question(...):
       # Add after line 53
       if predict([question.text])[0] == 1:  # Contains profanity
           db_question.status = "flagged"
           db_question.flagged_reason = "profanity"
       else:
           db_question.status = "approved"
   ```

3. **Frontend (JavaScript) - static/js/student.js:258**
   ```javascript
   // Add before fetch call
   import Filter from 'bad-words';
   const filter = new Filter();

   if (filter.isProfane(text)) {
       showNotification('Your question contains inappropriate language', 'error');
       return;
   }
   ```

4. **Database Schema (Already Ready)**
   - `models_v2.py:138` - Question.status can be "approved", "flagged", "rejected"
   - `models_v2.py:140` - Question.flagged_reason for tracking

5. **Testing**
   - Test with known profanity words
   - Verify flagged questions still submit but marked
   - Test false positives (e.g., "Scunthorpe problem")

**Files to Modify:**
- `routes_questions.py` - Add profanity check logic
- `static/js/student.js` - Add client-side filter
- `requirements.txt` - Add `profanity-check==1.0.0`
- `package.json` - Add `bad-words` (create if doesn't exist)

**Acceptance Criteria:**
- [ ] Questions with profanity are flagged, not rejected
- [ ] Instructor can see flagged questions in review panel
- [ ] Client-side warning before submission
- [ ] Server-side validation as backup
- [ ] False positives are minimized

---

#### Issue #20: Create Instructor Review Panel for Flagged Questions
**Priority:** Medium
**Effort:** 6 hours
**Status:** Open
**Depends On:** Issue #19

**Description:**
Build instructor interface to review, approve, or reject flagged questions.

**Implementation Plan:**

1. **Backend API Endpoints (routes_questions.py)**
   ```python
   @router.get("/api/meetings/{meeting_code}/flagged-questions")
   def get_flagged_questions(meeting_code: str, api_key: str, ...):
       """Get all flagged questions for a meeting"""
       # Return questions where status = "flagged"

   @router.post("/api/questions/{question_id}/approve")
   def approve_question(question_id: int, api_key: str, ...):
       """Approve a flagged question"""
       question.status = "approved"

   @router.post("/api/questions/{question_id}/reject")
   def reject_question(question_id: int, api_key: str, ...):
       """Reject a flagged question (hide from students)"""
       question.status = "rejected"
   ```

2. **Frontend UI (templates/instructor.html)**
   - Add "Flagged Questions" tab/section
   - Show flagged questions with reason
   - "Approve" and "Reject" buttons
   - Real-time updates via WebSocket

3. **WebSocket Integration**
   - Broadcast when question is flagged
   - Update instructor dashboard in real-time

4. **Testing**
   - Submit profane question as student
   - Verify appears in instructor review panel
   - Test approve/reject actions
   - Verify rejected questions hidden from students

**Files to Create/Modify:**
- `routes_questions.py` - Add review endpoints
- `templates/instructor.html` - Add flagged questions UI
- `static/js/instructor.js` - Add review panel logic
- `static/css/styles.css` - Style flagged questions section

**Acceptance Criteria:**
- [ ] Instructor can see all flagged questions
- [ ] Approve/reject actions work correctly
- [ ] Rejected questions hidden from student view
- [ ] Approved questions appear normally
- [ ] Real-time updates when questions are flagged

---

### **PHASE 5: Enhanced Answers** (1 issue)

#### Issue #23: Add Markdown Editor and Renderer
**Priority:** High (Last Phase 5 task)
**Effort:** 6 hours
**Status:** Open

**Description:**
Support rich text formatting for instructor answers using Markdown.

**Current State:**
- Backend API already supports written answers (routes in place)
- `models_v2.py:148` - Question.written_answer field exists
- Basic textarea in instructor.html (line 154)

**Implementation Plan:**

1. **Install Libraries**
   ```bash
   # Add to static/js/ or use CDN
   npm install easymde marked dompurify
   # Or use CDN in templates
   ```

2. **Instructor Editor (templates/instructor.html:154)**
   ```html
   <!-- Replace textarea with EasyMDE -->
   <link rel="stylesheet" href="https://unpkg.com/easymde/dist/easymde.min.css">
   <script src="https://unpkg.com/easymde/dist/easymde.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

   <textarea id="answer-text"></textarea>
   <div id="markdown-preview" style="display:none;"></div>
   ```

3. **Initialize Editor (static/js/instructor.js)**
   ```javascript
   let easyMDE;

   function openAnswerDialog(questionId) {
       // Initialize EasyMDE
       easyMDE = new EasyMDE({
           element: document.getElementById('answer-text'),
           spellChecker: false,
           toolbar: ["bold", "italic", "heading", "|",
                     "quote", "unordered-list", "ordered-list", "|",
                     "link", "image", "|", "preview", "guide"],
           previewRender: (plainText) => {
               return marked.parse(plainText);
           }
       });
   }
   ```

4. **Student Renderer (static/js/student.js)**
   ```html
   <!-- Add to student.html -->
   <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js"></script>
   ```

   ```javascript
   // In renderQuestions()
   if (question.written_answer) {
       const rawHtml = marked.parse(question.written_answer);
       const cleanHtml = DOMPurify.sanitize(rawHtml);
       html += `<div class="written-answer">${cleanHtml}</div>`;
   }
   ```

5. **Security (XSS Prevention)**
   - Always use DOMPurify.sanitize() before rendering
   - Configure DOMPurify to allow only safe HTML tags
   - Test with XSS payloads

6. **Styling (static/css/styles.css)**
   ```css
   .written-answer {
       background: #f9f9f9;
       padding: 15px;
       border-radius: 8px;
       border-left: 4px solid var(--primary-color);
       margin-top: 10px;
   }

   .written-answer code {
       background: #f0f0f0;
       padding: 2px 4px;
       border-radius: 3px;
   }

   .written-answer pre {
       background: #2d2d2d;
       color: #f8f8f8;
       padding: 10px;
       border-radius: 4px;
       overflow-x: auto;
   }
   ```

**Files to Modify:**
- `templates/instructor.html` - Add EasyMDE editor
- `templates/student.html` - Add marked.js and DOMPurify
- `static/js/instructor.js` - Initialize editor, handle save
- `static/js/student.js` - Render markdown safely
- `static/css/styles.css` - Style markdown content

**Testing Checklist:**
- [ ] Editor loads with toolbar
- [ ] Preview works in real-time
- [ ] Markdown saves to database
- [ ] Students see rendered HTML (not markdown)
- [ ] XSS prevention works (test with `<script>alert('XSS')</script>`)
- [ ] Code blocks syntax highlighted
- [ ] Links and images work
- [ ] Bold, italic, lists render correctly

**Acceptance Criteria:**
- [ ] Instructor has rich text editor with live preview
- [ ] Markdown is rendered as formatted HTML for students
- [ ] XSS attacks are prevented (DOMPurify)
- [ ] Mobile-friendly editor
- [ ] Syntax highlighting for code blocks

---

### **PHASE 7: Admin Dashboard** (1 issue)

#### Issue #26: Add Admin Dashboard
**Priority:** Low
**Effort:** 8 hours
**Status:** Open

**Description:**
Create comprehensive admin interface for managing instructors, classes, and meetings.

**Current State:**
- Basic admin login exists (`templates/admin-login.html`)
- Admin authentication works (JWT)
- No admin dashboard UI yet

**Implementation Plan:**

1. **Admin Dashboard Page (templates/admin.html)**
   ```html
   <!-- Create new admin dashboard -->
   - Overview stats (total instructors, classes, meetings)
   - Instructor management (create, edit, deactivate)
   - Class overview (all classes across all instructors)
   - Meeting monitoring (active meetings, question counts)
   - System health metrics
   ```

2. **Backend Admin Endpoints (create routes_admin.py)**
   ```python
   @router.get("/api/admin/instructors")
   def list_instructors(...):
       """List all instructors with stats"""

   @router.post("/api/admin/instructors")
   def create_instructor(...):
       """Create new instructor account"""

   @router.get("/api/admin/system-stats")
   def get_system_stats(...):
       """Get system-wide statistics"""

   @router.post("/api/admin/instructors/{id}/deactivate")
   def deactivate_instructor(...):
       """Deactivate instructor account"""
   ```

3. **Features to Implement:**
   - Create instructor accounts (generate API keys)
   - View all classes across all instructors
   - Monitor active meetings system-wide
   - View aggregate statistics
   - Deactivate/reactivate instructors
   - System health dashboard

4. **Security:**
   - Require admin JWT token for all endpoints
   - Verify `is_admin` flag on user
   - Audit log all admin actions

**Files to Create/Modify:**
- `routes_admin.py` - New file for admin endpoints
- `templates/admin.html` - Admin dashboard UI
- `static/js/admin.js` - Admin dashboard logic
- `main.py` - Include admin router

**Acceptance Criteria:**
- [ ] Admin can create instructor accounts
- [ ] Admin can view system-wide statistics
- [ ] Admin can monitor all active meetings
- [ ] Admin can deactivate instructors
- [ ] All admin actions are logged
- [ ] Admin interface is secure (JWT + is_admin check)

---

### **PHASE 8: Documentation** (1 issue)

#### Issue #27: Write Instructor Documentation
**Priority:** Medium
**Effort:** 4 hours
**Status:** Open

**Description:**
Create comprehensive documentation for instructors using RaiseMyHand.

**Implementation Plan:**

1. **Create Documentation Files:**
   ```
   docs/
   ├── INSTRUCTOR_QUICKSTART.md
   ├── INSTRUCTOR_FAQ.md
   ├── INSTRUCTOR_TUTORIAL.md
   └── TROUBLESHOOTING.md
   ```

2. **Quick Start Guide (INSTRUCTOR_QUICKSTART.md)**
   - How to get an API key
   - Creating your first class
   - Starting a meeting
   - Sharing the meeting with students (URL + QR code)
   - Managing questions (answer, mark as answered)
   - Ending a meeting and downloading reports

3. **FAQ (INSTRUCTOR_FAQ.md)**
   - How do students join?
   - Can I reuse a meeting code?
   - What happens when I end a meeting?
   - How do I export question data?
   - Can students see who asked questions?
   - How do I handle inappropriate questions?

4. **Tutorial (INSTRUCTOR_TUTORIAL.md)**
   - Step-by-step walkthrough with screenshots
   - Creating a class for "Physics 101"
   - Starting a live meeting
   - Demonstrating Q&A flow
   - Using the archive feature
   - Best practices for classroom use

5. **Troubleshooting (TROUBLESHOOTING.md)**
   - Students can't access meeting (check password, meeting ended)
   - Questions not updating (WebSocket issues)
   - API key not working
   - Meeting code not found

**Files to Create:**
- `docs/INSTRUCTOR_QUICKSTART.md`
- `docs/INSTRUCTOR_FAQ.md`
- `docs/INSTRUCTOR_TUTORIAL.md`
- `docs/TROUBLESHOOTING.md`

**Acceptance Criteria:**
- [ ] Quick start guide covers basic workflow
- [ ] FAQ answers common questions
- [ ] Tutorial includes screenshots/examples
- [ ] Troubleshooting covers common issues
- [ ] Documentation is accessible from main README

---

## 🔧 Technical Context

### Key Files & Their Purpose

**Backend:**
- `main.py` (1058 lines) - FastAPI app, includes all routers, WebSocket handling
- `routes_classes.py` (504 lines) - Class and meeting CRUD, QR codes, reports
- `routes_questions.py` (193 lines) - Question submission, voting, answering
- `models_v2.py` (185 lines) - SQLAlchemy ORM models for v2 schema
- `schemas_v2.py` (147 lines) - Pydantic validation schemas
- `database.py` - SQLAlchemy session management
- `config.py` - Settings with Pydantic
- `logging_config.py` - Centralized logging system

**Frontend:**
- `static/js/shared.js` (490 lines) - Shared utilities, hamburger menu
- `static/js/student.js` (285 lines) - Student question submission
- `static/js/instructor.js` - Instructor dashboard
- `static/js/classes-dashboard.js` - Class management
- `static/js/sessions-dashboard.js` - Meeting management
- `static/css/styles.css` (850+ lines) - All styles including navigation

**Templates:**
- `templates/student.html` - Student question view
- `templates/instructor.html` - Instructor meeting dashboard
- `templates/classes.html` - Class management page
- `templates/sessions.html` - Meeting management page

### Database Schema (v2)

```
Instructor (id, email, name)
  └─> APIKey (id, instructor_id, key, name, is_active)
        └─> Class (id, instructor_id, name, description, is_archived)
              └─> ClassMeeting (id, class_id, api_key_id, meeting_code, instructor_code, title, password_hash, is_active)
                    └─> Question (id, meeting_id, student_id, question_number, text, upvotes, status, flagged_reason, is_answered_in_class, written_answer)
                          └─> QuestionVote (id, question_id, student_id)
```

### API Authentication

**Instructor Endpoints:**
- Require `api_key` query parameter
- Verified via `verify_api_key_v2()` in routes_classes.py:30
- Returns APIKeyV2 object with instructor_id

**Admin Endpoints:**
- Require JWT token in Authorization header
- Admin login at `/api/admin/login`
- JWT secret in config.py

**Student Endpoints:**
- No authentication required (anonymous)
- Student ID tracked in localStorage (UUID)

### WebSocket Structure

**Connection:** `ws://localhost:8000/ws/{meeting_code}`

**Message Types:**
```python
{
    "type": "new_question",
    "question": { ... }
}

{
    "type": "vote_update",
    "question_id": 123,
    "upvotes": 5
}

{
    "type": "answer",
    "question_id": 123,
    "is_answered_in_class": true
}
```

### Testing

**Run API Tests:**
```bash
source .venv/bin/activate
python test_comprehensive.py
```

**Run Navigation Tests:**
```bash
node test_navigation.js
```

**Manual Testing:**
1. Start server: `python main.py`
2. Get API key from admin panel (http://localhost:8000/admin-login)
3. Create class at http://localhost:8000/classes
4. Start meeting
5. Test as student using meeting code

---

## 📦 Dependencies to Add

**Phase 4 (Profanity Filter):**
```bash
pip install profanity-check==1.0.0
npm install bad-words  # If using npm
```

**Phase 5 (Markdown):**
```html
<!-- Use CDN, no install needed -->
<script src="https://unpkg.com/easymde/dist/easymde.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js"></script>
```

---

## 🚀 Getting Started (for next developer)

1. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

2. **Check current branch status:**
   ```bash
   git log --oneline -5
   # Should see commits about navigation and UX improvements
   ```

3. **Set up environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env: Set ADMIN_PASSWORD
   ```

5. **Initialize database:**
   ```bash
   python init_db_v2.py
   ```

6. **Run server:**
   ```bash
   python main.py
   # Server at http://localhost:8000
   ```

7. **Run tests:**
   ```bash
   python test_comprehensive.py  # API tests
   node test_navigation.js       # Navigation tests
   ```

8. **Pick an issue and start coding!**

---

## 📝 Notes for Future Development

### Code Style Guidelines
- Use descriptive variable names
- Add docstrings to all functions
- Follow existing patterns (see routes_classes.py for examples)
- Always use ARIA labels for accessibility
- Mobile-first CSS (breakpoint at 768px)
- Use centralized logging: `log_database_operation(logger, "CREATE", "table", id, success=True)`

### Security Checklist
- [ ] Always validate API keys for instructor endpoints
- [ ] Sanitize user input (especially for markdown/HTML)
- [ ] Use parameterized SQL queries (SQLAlchemy handles this)
- [ ] Add CSRF tokens for state-changing operations
- [ ] Implement rate limiting for new endpoints
- [ ] Log all admin actions

### Testing Checklist
- [ ] Write API tests for new endpoints
- [ ] Test WebSocket updates
- [ ] Test on mobile (responsive design)
- [ ] Test keyboard navigation (accessibility)
- [ ] Test with screen reader (ARIA labels)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

### Git Workflow
1. Create feature branch: `git checkout -b feature/issue-XX`
2. Make changes and commit frequently
3. Run tests before committing
4. Use conventional commit messages:
   - `✨ feat:` for new features
   - `🐛 fix:` for bug fixes
   - `📝 docs:` for documentation
   - `♻️ refactor:` for code refactoring
5. Add co-author: `Co-Authored-By: Claude <noreply@anthropic.com>`
6. Create PR and reference issue number

---

## 🎯 Recommended Order

1. **Issue #23** - Markdown Editor (completes Phase 5)
2. **Issue #19** - Profanity Filter (start Phase 4)
3. **Issue #20** - Review Panel (finish Phase 4)
4. **Issue #27** - Documentation (always valuable)
5. **Issue #26** - Admin Dashboard (nice-to-have)

**Reasoning:**
- Markdown editor is high-value and relatively isolated
- Profanity filter + review panel work together (do in sequence)
- Documentation helps onboard new users
- Admin dashboard is polish (do last)

---

## 📞 Support

- GitHub Issues: https://github.com/OER-Forge/raisemyhand/issues
- Documentation: See `/docs` directory
- Logging: Check `logs/` directory for errors

**Good luck! 🚀**
