# 🙋 RaiseMyHand - Student Question System

A real-time web application for collecting and managing student questions during live classes. Students submit questions anonymously, vote on popular questions, and view instructor responses in real-time.

[![Python](https://img.shields.io/badge/python-3.9+-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688)]()
[![Production Ready](https://img.shields.io/badge/production-ready-brightgreen)]()

---

## ✨ What This System Does

### **Core Features**

- **Anonymous Question Submission** - Students submit questions without revealing identity
- **Real-time Upvoting** - Questions with more votes appear higher in the list
- **WebSocket Updates** - New questions and votes appear instantly for everyone
- **QR Code Access** - Students scan QR codes to join sessions quickly
- **Session Management** - Instructors create, start, pause, and end question sessions
- **Content Moderation** - Three-state profanity filtering (approved/flagged/rejected)
- **Markdown Support** - Rich text formatting in instructor answers with WYSIWYG editor
- **Presentation Mode** - Full-screen view optimized for classroom projection
- **Multi-monitor Support** - Pop-out windows for QR codes and presentation view
- **Written Answers** - Instructors can write detailed responses with markdown formatting
- **Session Statistics** - Public stats page showing question activity
- **Data Export** - Download session data as JSON or CSV
- **API Key Authentication** - Secure instructor access via API keys

### **User Interface**

- **Student View** - Clean question submission and voting interface
- **Instructor Dashboard** - Real-time question monitoring with moderation tools
- **Admin Panel** - User management and API key creation
- **Stats Page** - Large-text presentation view for classroom displays
- **Responsive Design** - Works on desktop, tablet, and mobile devices

### **Security & Moderation**

- **Profanity Filter** - Automatic detection using `better-profanity` library
- **Three-state Moderation** - Clean (auto-approved), Flagged (needs review), Rejected (hidden)
- **Server-side Filtering** - Security enforcement at the API level
- **Rate Limiting** - DDoS protection and submission throttling
- **CSRF Protection** - Cross-site request forgery prevention
- **JWT Authentication** - Secure admin authentication with bcrypt password hashing

---

## 🚀 Quick Setup

### **Option 1: Docker (Recommended)**

```bash
# Clone the repository
git clone <your-repo-url>
cd raisemyhand

# Configure environment
cp .env.example .env
echo "YourSecureAdminPassword" > secrets/admin_password.txt

# Build and start
docker compose up --build -d
```

The application will be available at **http://localhost:8000**

### **Option 2: Local Python Development**

```bash
# Clone and setup virtual environment
git clone <your-repo-url>
cd raisemyhand
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env file and set ADMIN_PASSWORD=YourSecurePassword

# Initialize database and start server
python main.py
```

The application will be available at **http://localhost:8000**

---

## 📖 Getting Started

See [GETTING_STARTED.md](GETTING_STARTED.md) for a complete step-by-step walkthrough.

### **1. Admin Setup (First Time Only)**

1. Go to **http://localhost:8000/admin-login**
2. Login with username `admin` and your password from .env or secrets file
3. Create an API key for instructors in the admin dashboard

### **2. Instructor Workflow**

1. **Create Session**: Enter your API key and session title at home page
2. **Share Access**: Display QR code or share the generated student URL
3. **Monitor Questions**: Watch questions appear in real-time, sorted by votes
4. **Moderate Content**: Review flagged questions, approve or reject as needed
5. **Answer Questions**: Mark questions as answered or write detailed responses
6. **Manage Session**: Toggle voting, end session, download reports

### **3. Student Experience**

1. **Join Session**: Scan QR code or visit shared URL
2. **Submit Questions**: Type questions and submit anonymously
3. **Vote on Questions**: Upvote questions you want answered
4. **Real-time Updates**: See new questions and instructor responses instantly

---

## 🏗️ Architecture

**Backend (Python/FastAPI):**
- FastAPI web framework with automatic OpenAPI documentation
- SQLAlchemy ORM with SQLite database (PostgreSQL-ready)
- WebSocket connections for real-time updates
- Pydantic data validation and serialization
- bcrypt password hashing and JWT authentication
- SlowAPI rate limiting and CSRF protection

**Frontend (Vanilla JavaScript):**
- WebSocket client for real-time communication
- EasyMDE markdown editor for instructor answers
- Marked.js and DOMPurify for safe markdown rendering
- Responsive CSS design without framework dependencies
- QR code generation and display

**Database Schema:**
- `class_meetings` - Session information and settings
- `questions` - Student questions with moderation status
- `answers` - Instructor written responses with markdown
- `question_votes` - Upvote tracking per student
- `api_keys` - Instructor authentication tokens

**Dependencies:**
- `better-profanity` - Content moderation
- `qrcode[pil]` - QR code generation
- `python-jose[cryptography]` - JWT tokens
- `passlib[bcrypt]` - Password hashing
- CDN libraries: EasyMDE, Marked.js, DOMPurify

---

## ⚙️ Configuration

### **Environment Variables (.env file)**

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
BASE_URL=http://localhost:8000

# Database
DATABASE_URL=sqlite:///./data/raisemyhand.db

# Admin Authentication (choose one)
ADMIN_PASSWORD=YourSecurePassword    # For development
# OR use Docker secrets: secrets/admin_password.txt

# Optional Settings
TIMEZONE=America/New_York
CREATE_DEFAULT_API_KEY=false
```

### **Production Deployment**

For production, set `BASE_URL` to your actual domain and use Docker secrets:

```bash
# Production example
BASE_URL=https://questions.university.edu
echo "ProductionPassword123!" > secrets/admin_password.txt
docker compose up -d
```

### **Database Migration (PostgreSQL)**

To switch from SQLite to PostgreSQL:

```bash
# Update .env
DATABASE_URL=postgresql://user:password@host:5432/database

# Install driver
pip install psycopg2-binary

# Run normally - tables auto-created
python main.py
```

---

## 🔒 Security Features

- **Content Moderation**: Server-side profanity detection with three-state system
- **Authentication**: JWT tokens for admin, API keys for instructors
- **Rate Limiting**: Prevents spam and DDoS attacks
- **CSRF Protection**: Secure state-changing operations
- **XSS Prevention**: HTML sanitization with DOMPurify
- **Password Security**: bcrypt hashing with salt
- **Session Isolation**: Students only see approved content

---

## 📊 API Documentation

Interactive API documentation is available at **http://localhost:8000/docs** when the server is running.

### **Key Endpoints**

**Session Management:**
- `POST /api/meetings` - Create new session (requires API key)
- `GET /api/meetings/{meeting_code}` - Get session details and questions
- `POST /api/meetings/{instructor_code}/end` - End session
- `GET /api/meetings/{instructor_code}/flagged-questions` - Review flagged content

**Question Operations:**
- `POST /api/meetings/{meeting_code}/questions` - Submit question
- `POST /api/questions/{question_id}/vote` - Toggle upvote
- `POST /api/questions/{question_id}/approve` - Approve flagged question
- `POST /api/questions/{question_id}/reject` - Reject flagged question

**Answer Management:**
- `POST /api/questions/{question_id}/answer` - Create/update written answer
- `POST /api/questions/{question_id}/answer/publish` - Make answer public

**Real-time:**
- `WS /ws/{meeting_code}` - WebSocket for live updates

---

## 🐳 Docker Details

The included `docker-compose.yml` sets up:
- FastAPI application container
- Volume mounting for persistent data
- Environment variable configuration
- Docker secrets support for production

**Container Structure:**
```
/app/
├── main.py (application entry point)
├── data/ (SQLite database storage)
├── static/ (CSS/JS assets)
├── templates/ (HTML templates)
└── secrets/ (password files)
```

---

## 📁 Project Structure

```
raisemyhand/
├── main.py                    # Application entry point
├── models_v2.py               # Database models (SQLAlchemy)
├── schemas_v2.py              # API schemas (Pydantic)
├── routes_classes.py          # Session management routes
├── routes_questions.py        # Question handling routes
├── routes_answers.py          # Answer management routes
├── database.py                # Database configuration
├── logging_config.py          # Logging setup
├── static/
│   ├── css/styles.css         # Application styles
│   └── js/
│       ├── shared.js          # Common utilities
│       ├── student.js         # Student interface
│       ├── instructor.js      # Instructor dashboard
│       └── admin.js           # Admin panel
├── templates/
│   ├── student.html           # Student question interface
│   ├── instructor.html        # Instructor dashboard
│   ├── stats.html             # Presentation view
│   ├── admin.html             # Admin panel
│   └── *.html                 # Other UI templates
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Container orchestration
└── .env.example               # Configuration template
```

---

## 🧪 Testing & Development

### **Local Testing**

```bash
# Start the server
python main.py

# Test workflow:
# 1. Create admin account at /admin-login
# 2. Create API key in admin dashboard
# 3. Start new session at home page
# 4. Open student URL in different browser/tab
# 5. Submit questions and test voting
# 6. Try content moderation with test profanity
```

### **Multi-user Testing**

Open multiple browser tabs/windows:
- **Tab 1**: Instructor dashboard (with API key)
- **Tab 2+**: Student views (different browsers to simulate multiple students)
- Test real-time updates by submitting questions and votes

### **Content Moderation Testing**

Submit questions with profanity to test the three-state moderation system:
- Clean questions → Auto-approved and visible
- Flagged questions → Require instructor review
- Rejected questions → Hidden from students

---

## 📈 Monitoring & Logs

The application logs all operations including:
- Database operations (CREATE, UPDATE, DELETE)
- WebSocket connections and disconnections
- Security events (authentication, rate limiting)
- Content moderation actions

Logs are structured for production monitoring and include timestamps, operation types, and success/failure status.

---

## 🔧 Troubleshooting

**Common Issues:**

1. **Port already in use**: Change `PORT` in .env file
2. **Database errors**: Check write permissions in `data/` directory
3. **WebSocket connection failed**: Verify `BASE_URL` matches actual domain
4. **QR code not loading**: Check network connectivity and BASE_URL configuration
5. **Markdown not rendering**: Ensure CDN libraries load (check browser console)

**Development Issues:**

1. **Changes not visible**: Clear browser cache or hard refresh (Ctrl+Shift+R)
2. **API key authentication fails**: Verify API key was created in admin panel
3. **Real-time updates not working**: Check WebSocket connection in browser dev tools

---

## 🤝 Contributing

This is educational software built for classroom use. The codebase follows professional standards with comprehensive error handling, security measures, and clean architecture.

**Development Guidelines:**
- Follow existing code structure and naming conventions
- Add tests for new features
- Update documentation for any changes
- Ensure mobile responsiveness for UI changes

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🏫 Use Cases

**Physics Classes**: Students ask questions about complex topics during lectures
**Computer Science**: Debugging help and concept clarification during coding sessions  
**Mathematics**: Step-by-step explanations and problem-solving guidance
**General Education**: Any classroom where anonymous question collection improves participation

The presentation mode and QR code features are specifically designed for classroom projection systems and student mobile device access.

---

<div align="center">

**[Visit GitHub Repository](#) • [Report Issues](#) • [Documentation](#)**

Built for education with ❤️

</div>
