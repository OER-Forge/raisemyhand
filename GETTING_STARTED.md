# 🚀 Getting Started with RaiseMyHand

This guide walks you through setting up and using RaiseMyHand from start to finish.

---

## 📋 Table of Contents

1. [Installation](#-installation)
2. [Getting Your API Key](#-getting-your-api-key)
3. [Creating Your First Session](#-creating-your-first-session)
4. [Running a Live Session](#-running-a-live-session)
5. [Managing Sessions](#-managing-sessions)
6. [Troubleshooting](#-troubleshooting)

---

## 📦 Installation

### Option 1: Local Development (Individual Instructor)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/raisemyhand.git
cd raisemyhand

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Or use your preferred editor
```

**Edit your `.env` file:**
```bash
# Required: Set a secure admin password
ADMIN_PASSWORD=YourSecurePassword123!

# Optional: Customize your setup
PORT=8000
BASE_URL=http://localhost:8000
TIMEZONE=America/New_York
```

```bash
# 5. Start the server
python main.py
```

Your server is now running at **http://localhost:8000** 🎉

### Option 2: Docker (Department/College Server)

```bash
# 1. Clone and configure
git clone https://github.com/your-org/raisemyhand.git
cd raisemyhand
cp .env.example .env

# 2. Set admin password (Docker secrets)
mkdir -p secrets
echo "YourSecurePassword123!" > secrets/admin_password.txt

# 3. Edit .env for your environment
nano .env
```

**Edit your `.env` file:**
```bash
ENV=production
BASE_URL=https://questions.yourschool.edu
TIMEZONE=America/New_York
DEBUG=false
```

```bash
# 4. Start with Docker
docker compose up -d

# 5. Check logs
docker compose logs -f
```

Your server is running! See [DOCKER.md](DOCKER.md) for production deployment with nginx/SSL.

---

## 🔑 Getting Your API Key

API keys are required for instructors to create and manage sessions. Here's how to get yours:

### Step 1: Access the Admin Panel

1. Open your browser and go to the admin login page:
   - Local: **http://localhost:8000/admin-login**
   - Server: **https://your-server/admin-login**

2. Login with:
   - **Username:** `admin`
   - **Password:** (the password you set in `.env` or `secrets/admin_password.txt`)

### Step 2: Create an API Key

1. Once logged in, you'll see the **Admin Dashboard**
2. Navigate to the **"API Keys"** section
3. Click **"Create New API Key"**
4. Enter a descriptive name for your key:
   - Example: "Prof. Smith - Physics 101"
   - Example: "Dr. Johnson - Fall 2025"
   - Example: "Teaching Assistant - Lab Sessions"

5. Click **"Generate Key"**

### Step 3: Save Your API Key Securely

⚠️ **IMPORTANT:** Your API key will only be shown **once** after creation!

```
Your API Key: rmh_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**Do one of the following:**

✅ **Option A - Copy to Clipboard:**
- Click the "Copy to Clipboard" button
- Paste it into a secure password manager (1Password, LastPass, Bitwarden)

✅ **Option B - Save to File:**
- Save to a text file on your computer: `~/Documents/raisemyhand-api-key.txt`
- **Never commit this file to git!**

✅ **Option C - Write it Down:**
- Write it on paper and store it securely
- Keep it in your office or locked drawer

❌ **Never:**
- Share your API key with students
- Post it publicly (GitHub, Slack, email)
- Store it in unencrypted cloud storage

### Step 4: Test Your API Key

1. Go to the home page: **http://localhost:8000**
2. You should see two sections:
   - **Students:** Join an existing session
   - **Instructors:** Create a new session

3. Under "Instructors", you'll see an **"Instructor Login"** button
4. Click it - you should be taken to the instructor login page
5. Enter your API key to verify it works (we'll create a session next!)

---

## 🎓 Creating Your First Session

Now that you have your API key, let's create a session for your class.

### Method 1: Via Web Interface (Recommended)

1. **Go to Instructor Login:**
   - Navigate to **http://localhost:8000/instructor-login**
   - Or click "Instructor Login" from the home page

2. **Enter Your API Key:**
   - Paste your API key: `rmh_a1b2c3d4e5f6...`
   - Click **"Login"**

3. **Create a Session:**
   - Click **"Create New Session"**
   - Enter session details:
     - **Title:** "Quantum Mechanics - Lecture 12"
     - **Password:** (optional - leave blank for public sessions)
   - Click **"Create Session"**

4. **Success!** You'll be redirected to your **Instructor Dashboard** where you can:
   - See your unique session URLs
   - Display a QR code for students
   - Monitor incoming questions in real-time

### Method 2: Via API (Programmatic)

If you want to automate session creation (e.g., from a script):

```bash
# Replace YOUR_API_KEY with your actual key
curl -X POST "http://localhost:8000/api/sessions?api_key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $(curl -s http://localhost:8000/api/csrf-token | jq -r .csrf_token)" \
  -d '{
    "title": "Physics 101 - Week 5",
    "password": "optional_password"
  }'
```

**Response:**
```json
{
  "id": 42,
  "session_code": "abc123xyz",
  "instructor_code": "def456uvw",
  "title": "Physics 101 - Week 5",
  "student_url": "http://localhost:8000/student?code=abc123xyz",
  "instructor_url": "http://localhost:8000/instructor?code=def456uvw",
  "created_at": "2025-12-03T10:30:00Z",
  "is_active": true
}
```

See [API Documentation](#api-documentation) for more endpoints.

---

## 🎤 Running a Live Session

### Before Class: Setup

1. **Create your session** (see above)
2. **Test the student URL** by opening it in a private/incognito window
3. **Prepare to share** the session with students (see options below)

### Sharing with Students

You have **three options** for giving students access:

#### Option A: QR Code (Easiest - Recommended for In-Person Classes)

1. On your **Instructor Dashboard**, click **"Show QR Code"**
2. A large QR code appears with the student URL embedded
3. **Display it on your projector/screen**
4. Students scan with their phone camera (no app needed!)
5. They're instantly taken to the session

**Tip:** Keep the QR code visible for the first 5 minutes of class so latecomers can join.

#### Option B: Share URL (Best for Online/Hybrid Classes)

1. Copy the **Student URL** from your dashboard:
   ```
   http://localhost:8000/student?code=abc123xyz
   ```

2. Share it via:
   - **Learning Management System (LMS):** Post in Canvas/Moodle/Blackboard
   - **Chat:** Paste in Zoom/Teams/Slack
   - **Email:** Send to your class mailing list
   - **Course Website:** Add to your syllabus page

#### Option C: Direct Code Entry (For Tech-Savvy Students)

Students can:
1. Go to **http://localhost:8000**
2. Enter session code manually: `abc123xyz`
3. Click "Join Session"

### During Class: Monitor Questions

Your **Instructor Dashboard** shows:

```
╔════════════════════════════════════════════════════════════╗
║  Quantum Mechanics - Lecture 12                            ║
║  📊 3 questions  •  ⬆️ 12 total votes  •  🟢 Active        ║
╚════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────┐
│ Q1  ⬆️ 8  What's the difference between ψ and ψ*?         │
│     [Mark as Answered]                                     │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ Q2  ⬆️ 3  Can you explain the uncertainty principle?      │
│     [Mark as Answered]                                     │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ Q3  ⬆️ 1  Is the exam open book?                          │
│     [Mark as Answered]                                     │
└────────────────────────────────────────────────────────────┘

[Toggle Voting]  [End Session]  [Download Report]
```

**Features:**
- ✅ **Real-time Updates** - Questions appear instantly as students submit them
- ✅ **Auto-Sorting** - Most upvoted questions appear at the top
- ✅ **Question Numbers** - Permanent Q1, Q2, Q3... for easy reference
- ✅ **Mark as Answered** - Click to mark questions you've addressed
- ✅ **Toggle Voting** - Disable voting to freeze the order (e.g., when answering)

### Best Practices During Class

1. **Keep Dashboard Visible:** Have it open on your laptop/tablet while teaching

2. **Check Periodically:** Glance at new questions every 5-10 minutes

3. **Address Popular Questions:** Prioritize questions with the most upvotes

4. **Use Question Numbers:** Say "I'll answer Q3 now" so students know you're responding

5. **Mark Questions as Answered:** Click the checkmark when you've addressed a question

6. **Toggle Voting When Needed:**
   - Turn OFF voting when you start answering questions (prevents order changes mid-explanation)
   - Turn ON voting when asking "What should I address next?"

### After Class: End Session

1. Click **"End Session"** on your dashboard
2. Students can no longer submit new questions or vote
3. You can:
   - **View Statistics:** Public stats page shows engagement metrics
   - **Download Report:** Export questions as JSON or CSV
   - **Restart Session:** If you ended by accident, click "Restart Session"

---

## 📊 Managing Sessions

### View All Your Sessions

1. Go to **http://localhost:8000/instructor-login**
2. Enter your API key
3. Click **"My Sessions"**

You'll see a list of all sessions you've created:

```
╔══════════════════════════════════════════════════════════╗
║  My Sessions                                             ║
╚══════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────┐
│ 🟢 Active Session                                        │
│ Quantum Mechanics - Lecture 12                           │
│ 3 questions • 12 votes • Started 23 minutes ago          │
│ [View Dashboard]  [End Session]                          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 🔴 Ended Session                                         │
│ Quantum Mechanics - Lecture 11                           │
│ 15 questions • 45 votes • Ended 2 days ago               │
│ [View Statistics]  [Download Report]  [Restart]          │
└──────────────────────────────────────────────────────────┘
```

### Download Session Reports

Reports contain all questions, votes, timestamps, and answer status.

**Via Dashboard:**
1. Go to "My Sessions"
2. Click **"Download Report"** on any session
3. Choose format: **JSON** or **CSV**

**Via API:**
```bash
curl "http://localhost:8000/api/sessions/YOUR_INSTRUCTOR_CODE/report?format=csv&api_key=YOUR_API_KEY" \
  -o session_report.csv
```

**CSV Format:**
```csv
Question Number,Question Text,Upvotes,Is Answered,Created At,Answered At
1,"What's the difference between ψ and ψ*?",8,true,2025-12-03T10:35:22Z,2025-12-03T10:42:15Z
2,"Can you explain the uncertainty principle?",3,true,2025-12-03T10:37:45Z,2025-12-03T10:50:30Z
3,"Is the exam open book?",1,false,2025-12-03T10:40:12Z,
```

**JSON Format:**
```json
{
  "session": {
    "title": "Quantum Mechanics - Lecture 12",
    "created_at": "2025-12-03T10:30:00Z",
    "ended_at": "2025-12-03T11:45:00Z"
  },
  "statistics": {
    "total_questions": 3,
    "total_upvotes": 12,
    "answered_questions": 2
  },
  "questions": [
    {
      "number": 1,
      "text": "What's the difference between ψ and ψ*?",
      "upvotes": 8,
      "is_answered": true,
      "created_at": "2025-12-03T10:35:22Z",
      "answered_at": "2025-12-03T10:42:15Z"
    }
  ]
}
```

### Restart an Ended Session

If you accidentally ended a session or want to reopen it:

1. Go to **"My Sessions"**
2. Find the ended session
3. Click **"Restart Session"**
4. Session becomes active again - students can submit questions and vote

---

## ❓ Troubleshooting

### "Invalid or missing CSRF token"

**Problem:** Getting CSRF error when creating sessions.

**Solution:**
1. Clear your browser cache and cookies
2. Refresh the page
3. Try in an incognito/private window
4. Check that `static/js/shared.js` is loading (check browser console)

### "API key not found or inactive"

**Problem:** Your API key isn't working.

**Causes:**
1. **Typo in API key** - Double-check you copied it correctly
2. **Key was deactivated** - Admin may have disabled it
3. **Key doesn't exist** - You may need to create a new one

**Solution:**
1. Go to Admin Panel → API Keys
2. Check if your key is listed and marked as "Active"
3. If missing, create a new API key
4. If inactive, reactivate it or create a new one

### "Session not found"

**Problem:** Students can't access the session.

**Causes:**
1. **Wrong session code** - Check for typos
2. **Session was ended** - Instructor ended the session
3. **Session was deleted** - Admin deleted it from database

**Solution:**
1. Verify the session code is correct
2. Check "My Sessions" to see if session is active
3. Restart the session if it was accidentally ended
4. Create a new session if necessary

### WebSocket Connection Failed

**Problem:** Real-time updates aren't working. Dashboard doesn't show new questions.

**Causes:**
1. **Firewall blocking WebSocket** - Corporate/school firewall
2. **Proxy server** - Nginx/Apache misconfigured
3. **Browser extension** - Ad blocker interfering

**Solution:**
1. Check browser console for WebSocket errors (F12 → Console)
2. Test in incognito mode (disables extensions)
3. If using nginx, ensure WebSocket proxy is configured:
   ```nginx
   location /ws/ {
       proxy_pass http://localhost:8000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```
4. Check firewall allows WebSocket connections

### Students Can't See QR Code

**Problem:** QR code isn't displaying on instructor dashboard.

**Causes:**
1. **JavaScript disabled** - Browser settings
2. **QR library not loading** - Network issue
3. **Pop-up blocker** - QR code in modal

**Solution:**
1. Check browser console for errors
2. Enable JavaScript in browser settings
3. Disable pop-up blocker for the site
4. Alternative: Use the student URL directly instead

### Can't Access Admin Panel

**Problem:** "Invalid credentials" when logging into admin.

**Causes:**
1. **Wrong password** - Check `.env` or `secrets/admin_password.txt`
2. **Password not set** - `ADMIN_PASSWORD` is blank
3. **Docker secret issue** - Secret file not mounted

**Solution:**

**For local development:**
```bash
# Check your .env file
cat .env | grep ADMIN_PASSWORD

# If blank, set it:
echo "ADMIN_PASSWORD=YourSecurePassword123!" >> .env

# Restart server
python main.py
```

**For Docker:**
```bash
# Check secret file
cat secrets/admin_password.txt

# If missing, create it:
echo "YourSecurePassword123!" > secrets/admin_password.txt

# Restart container
docker compose down
docker compose up -d
```

---

## 📚 Next Steps

Now that you're set up, explore more features:

- **[SECURITY.md](SECURITY.md)** - Security best practices
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deploy to production (AWS, Heroku, DigitalOcean)
- **[DOCKER.md](DOCKER.md)** - Docker deployment with nginx and SSL
- **[URL_CONFIGURATION.md](URL_CONFIGURATION.md)** - Configure URLs and timezones
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation (Swagger UI)

---

## 💬 Need Help?

- 📖 **Documentation:** See `/docs` directory
- 🐛 **Bug Reports:** Open an issue on GitHub
- 💡 **Feature Requests:** Open an issue with `enhancement` label
- 🔒 **Security Issues:** Email maintainers directly (never public)

---

**Happy teaching! 🎓**

Made with ❤️ for education
