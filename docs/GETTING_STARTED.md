# Getting Started with RaiseMyHand

This guide walks you through setting up and using RaiseMyHand for the first time.

## Table of Contents

1. [Installation](#installation)
2. [First-Time Setup](#first-time-setup)
3. [Creating Your First Session](#creating-your-first-session)
4. [Student Workflow](#student-workflow)
5. [Instructor Workflow](#instructor-workflow)
6. [Next Steps](#next-steps)

---

## Installation

### Option 1: Demo Mode (Quickest Start)

Try RaiseMyHand with pre-loaded demo data:

```bash
docker compose -f docker-compose.demo.yml up -d
```

- **URL:** http://localhost:8000
- **Login:** `admin` / `demo123`
- **Data:** Resets on container restart

### Option 2: Development Mode (For Classroom Use)

Set up for actual classroom use with persistent data:

```bash
# 1. Configure environment
cp .env.example .env

# 2. Set admin password
mkdir -p secrets
echo "YourSecurePassword" > secrets/admin_password.txt

# 3. Start the application
docker compose -f docker-compose.dev.yml up -d
```

- **URL:** http://localhost:8001
- **Login:** `admin` / (your password)
- **Data:** Persists between restarts

### Option 3: Local Development

For Python developers who want to run without Docker:

```bash
# Clone and setup
git clone <your-repo-url>
cd raisemyhand
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and set ADMIN_PASSWORD=YourSecurePassword

# Run
python main.py
```

- **URL:** http://localhost:8000

---

## First-Time Setup

### Step 1: Access Admin Panel

1. Visit http://localhost:8000/admin-login (or :8001 for dev mode)
2. Login with username `admin` and your password
3. You should see the admin dashboard

### Step 2: Create an API Key for Instructors

API keys allow instructors to create and manage sessions without admin privileges.

1. In the admin panel, click **"API Keys"** in the navigation
2. Click **"Create New API Key"**
3. Enter a description (e.g., "Dr. Smith - Physics 101")
4. Click **"Create"**
5. **IMPORTANT:** Copy the API key immediately - it won't be shown again
6. The API key looks like: `rmh_abc123def456...`

### Step 3: (Optional) Create Additional Instructors

If you want separate instructor accounts:

1. In the admin panel, click **"Instructors"** in the navigation
2. Click **"Create New Instructor"**
3. Fill in the details (name, email, password)
4. Choose role: INSTRUCTOR (standard) or ADMIN (can manage others)
5. Click **"Create"**
6. The instructor can now login at http://localhost:8000/instructor-login

---

## Creating Your First Session

### As an Instructor (Using API Key)

1. Visit the home page: http://localhost:8000
2. Enter your API key in the **"Instructor Access"** section
3. Enter a session title (e.g., "Physics 101 - Lecture 5")
4. Click **"Create Session"**
5. You'll be redirected to the instructor dashboard

### As a Logged-In Instructor

1. Login at http://localhost:8000/instructor-login
2. Go to **"Sessions"** page
3. Click **"Create New Session"**
4. Fill in session details
5. Click **"Start Session"**

---

## Student Workflow

### How Students Join

Students have three ways to join:

1. **QR Code:** Scan the QR code displayed in the instructor dashboard
2. **Direct URL:** Visit the student URL shared by the instructor
3. **Manual Entry:** Go to home page and enter the meeting code

### How Students Ask Questions

1. Type their question in the text box
2. Click **"Submit Question"**
3. The question appears immediately in the list
4. They can upvote other questions by clicking the arrow icon
5. Questions with more votes appear higher in the list

### How Students See Answers

- Answered questions show a checkmark
- Published written answers appear below the question
- Real-time updates show new questions and votes automatically

---

## Instructor Workflow

### Managing Questions

**Instructor Dashboard View:**
- Questions sorted by vote count (highest first)
- Real-time updates as students submit and vote
- Color-coded status: green (approved), yellow (flagged), red (rejected)

**Actions:**
- **Mark as Answered:** Click checkmark icon
- **Write Answer:** Click "Answer" button, write response in markdown, publish
- **Approve Flagged:** Review and approve questions with potential profanity
- **Reject:** Hide inappropriate questions from students
- **Delete:** Permanently remove questions

### Session Controls

**Voting Toggle:**
- Turn voting on/off to prevent vote manipulation
- Useful when discussing specific questions

**End Session:**
- Click "End Session" to close the meeting
- Students can no longer submit questions
- You can still view and export data

**Presentation Mode:**
- Click "Open Presentation View" for full-screen stats
- Shows total questions, votes, and participation metrics
- Perfect for classroom projection

### Data Export

1. Click **"Export Data"** in the instructor dashboard
2. Choose format: **JSON** (detailed) or **CSV** (spreadsheet)
3. Download includes all questions, votes, answers, and timestamps

---

## Next Steps

### For Instructors

- Read the [Instructor Guide](INSTRUCTOR_GUIDE.md) for advanced features
- Learn about [Content Moderation](FAQ.md#content-moderation)
- Set up [Presentation Mode](INSTRUCTOR_GUIDE.md#presentation-mode)
- Explore [Markdown Answers](INSTRUCTOR_GUIDE.md#written-answers)

### For Admins

- Read the [Admin Guide](ADMIN_GUIDE.md) for user management
- Learn about [API Key Management](ADMIN_GUIDE.md#api-key-management)
- Configure [Production Deployment](DEPLOYMENT.md)
- Set up [Auto-Reset for Demo](../scripts/setup-demo-cron.md)

### For Students

- Read the [Student Guide](STUDENT_GUIDE.md) for tips
- Learn about [Anonymous Voting](FAQ.md#is-voting-really-anonymous)

### For Developers

- Read the [API Documentation](API.md)
- Explore the [Project Structure](README.md#project-structure)
- Review [Troubleshooting Guide](TROUBLESHOOTING.md)

---

## Common First-Time Issues

### "Port already in use"

If port 8000 or 8001 is already taken:

```bash
# Stop conflicting containers
docker compose -f docker-compose.demo.yml down
docker compose -f docker-compose.dev.yml down

# Or change the port in docker-compose.*.yml
ports:
  - "8002:8000"  # Change 8001 to 8002
```

### "Cannot connect to Docker daemon"

Make sure Docker Desktop is running:

```bash
# Check Docker status
docker ps

# Start Docker Desktop if needed
```

### "Database initialization failed"

Check file permissions:

```bash
# Ensure data directory is writable
mkdir -p data
chmod 755 data

# Restart the container
docker compose -f docker-compose.*.yml restart
```

### QR Code Not Loading

Verify BASE_URL is correct:

```bash
# For local use
BASE_URL=http://localhost:8000

# For network access (use your computer's IP)
BASE_URL=http://192.168.1.100:8000

# For production
BASE_URL=https://questions.university.edu
```

---

## Quick Reference

### URLs

- **Home Page:** http://localhost:8000
- **Admin Login:** http://localhost:8000/admin-login
- **Instructor Login:** http://localhost:8000/instructor-login
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Default Credentials

**Demo Mode:**
- Username: `admin`
- Password: `demo123`

**Dev Mode:**
- Username: `admin`
- Password: (from secrets/admin_password.txt)

### Useful Commands

```bash
# Start demo
docker compose -f docker-compose.demo.yml up -d

# Start dev
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.*.yml logs -f

# Stop and remove data
docker compose -f docker-compose.*.yml down -v

# Restart
docker compose -f docker-compose.*.yml restart
```

---

## Getting Help

- **FAQ:** [docs/FAQ.md](FAQ.md)
- **Troubleshooting:** [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **GitHub Issues:** Report bugs and request features
- **Documentation:** [docs/README.md](README.md)

---

**Ready to go?** Head back to the [main README](../README.md) or dive into the [Instructor Guide](INSTRUCTOR_GUIDE.md) to learn advanced features!
