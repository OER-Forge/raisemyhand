# Getting Started with RaiseMyHand

This guide walks you through setting up and using RaiseMyHand for the first time.

---

## 🎯 Overview

**RaiseMyHand** is a real-time question collection system for classrooms. Students submit anonymous questions, vote on popular questions, and view instructor responses. Instructors moderate content, answer questions, and manage the session flow.

### **What You'll Accomplish**
1. Set up the application (5 minutes)
2. Create your first instructor session (2 minutes)  
3. Test the student experience (3 minutes)
4. Learn advanced features (10 minutes)

---

## 🚀 Quick Setup

### **Option A: Docker (Recommended)**

Perfect for production use or if you want to avoid Python setup.

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd raisemyhand

# 2. Configure environment
cp .env.example .env

# 3. Set admin password
echo "MySecurePassword123" > secrets/admin_password.txt

# 4. Start the application
docker compose up --build -d
```

✅ **Ready!** The application is now running at **http://localhost:8000**

### **Option B: Local Python Setup**

Best for development or customization.

```bash
# 1. Clone and setup environment
git clone <your-repo-url>
cd raisemyhand
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set: ADMIN_PASSWORD=MySecurePassword123

# 4. Start the application
python main.py
```

✅ **Ready!** The application is now running at **http://localhost:8000**

---

## 👥 First Time Setup

### **Step 1: Create Admin Account**

1. Open **http://localhost:8000/admin-login**
2. Login with:
   - **Username**: `admin`
   - **Password**: (the password you set above)

### **Step 2: Create API Key**

1. In the admin dashboard, click **"Create New API Key"**
2. Enter a name like "My Teaching Key"
3. Click **Create** and copy the generated API key
4. **Save this key** - you'll need it to create sessions

---

## 🎓 Your First Session

### **Step 1: Create Session**

1. Go to **http://localhost:8000** (home page)
2. Enter your API key from the previous step
3. Add a session title: `"Getting Started Test"`
4. Click **"Create Session"**

You'll be redirected to the instructor dashboard.

### **Step 2: Share with Students**

Two ways to share access:

**Option A: QR Code (Recommended for classrooms)**
1. Click **"📱 QR Code (For Students)"**
2. A pop-up window opens with a QR code
3. Students scan with phone cameras to join

**Option B: Direct URL**
1. Copy the **Student URL** from the dashboard
2. Share via email, chat, or LMS

### **Step 3: Test Student Experience**

1. **Open a new browser tab** (or use your phone)
2. Visit the Student URL or scan the QR code
3. Submit a test question: `"How does the voting system work?"`
4. **Switch back to instructor dashboard** - see the question appear!

### **Step 4: Test Voting**

1. In the student tab, submit another question: `"This is a popular question"`
2. Click the ⬆️ button to upvote it
3. Submit a third question: `"Less popular question"`
4. **Notice**: Questions are sorted by vote count (highest first)

---

## 📊 Presentation Mode

RaiseMyHand includes a presentation view optimized for classroom projection.

### **Testing Presentation View**

1. In the instructor dashboard, click **"🎬 Presentation View"**
2. A full-screen window opens with large text
3. Questions appear in horizontal bars: **Q1** | Question text | Vote count
4. **Perfect for projectors!** Move this window to your second monitor

### **Key Features**

- **Large Text**: 2.4rem font size for back-row visibility
- **Auto-refresh**: Updates every 5 seconds
- **QR Code**: Integrated in header for easy student access
- **Minimal Design**: No distracting UI elements

---

## 🛡️ Content Moderation

RaiseMyHand automatically filters inappropriate content using a three-state system.

### **Testing Moderation**

1. **Submit a clean question** (student tab): `"This is appropriate"`
   - ✅ **Result**: Appears immediately for everyone

2. **Submit a flagged question** (use a mild profanity like "damn")
   - ⚠️ **Result**: Requires instructor review before appearing

3. **Review flagged content** (instructor dashboard):
   - Click **"🚩 Flagged for Review"** tab
   - See original text vs. censored version
   - Click **"✓ Approve & Show"** or **"✗ Reject & Hide"**

### **How It Works**

- **Auto-approved**: Clean questions appear immediately
- **Flagged**: Questions with profanity require instructor review
- **Server-side**: Security enforced at API level (students can't bypass)
- **Sanitized Display**: Approved profane questions show censored text

---

## ✍️ Written Answers

Instructors can provide detailed responses using markdown formatting.

### **Creating Written Answers**

1. Click **"📝 Answer"** on any question
2. A markdown editor opens with formatting toolbar
3. Write your answer using:
   - **Bold text**: `**bold**`
   - *Italic text*: `*italic*`
   - Code snippets: \`code\`
   - Lists, links, headers

4. Click **"Save Answer"** (saves as draft)
5. Click **"✓ Publish to Students"** (makes visible to students)

### **Student View**

- Published answers appear below questions with 📝 icon
- Markdown is rendered as formatted HTML
- Students see professional-looking responses

---

## 🔧 Advanced Features

### **Session Management**

- **Toggle Voting**: Disable/enable voting during Q&A periods
- **End Session**: Stop new question submissions
- **Download Reports**: Export all data as JSON or CSV
- **Session Statistics**: View public stats page

### **Multi-Monitor Classroom Setup**

For classrooms with multiple monitors/projectors:

1. **Primary Monitor**: Keep instructor dashboard for control
2. **Student Monitor**: Pop-out QR code window for easy scanning
3. **Projection Screen**: Pop-out presentation view with questions

All windows can be moved independently to different screens.

### **API Integration**

- Full REST API available at `/docs` when running
- Create sessions programmatically
- Integrate with LMS systems
- Export data for analysis

---

## 🎯 Typical Classroom Workflow

### **Before Class (2 minutes)**

1. Start RaiseMyHand application
2. Create session with topic-specific title
3. Display QR code on classroom screen

### **During Class**

1. **Students join** by scanning QR code
2. **Collect questions** as you lecture
3. **Monitor popularity** via vote counts
4. **Address top questions** during Q&A breaks
5. **Moderate content** as needed

### **End of Class**

1. **Download session data** for later review
2. **End the session** to stop new submissions
3. **Archive questions** for future reference

---

## 🔍 Troubleshooting

### **Common Issues**

**Application won't start**
- Check port 8000 isn't in use: `PORT=8001 docker compose up`
- Verify Docker is running (Docker option)

**QR code doesn't work**
- Check `BASE_URL` in .env matches your actual address
- For network access, use your IP: `BASE_URL=http://192.168.1.100:8000`

**Students can't connect**
- Ensure firewall allows port 8000
- Check students are on same network (local setup)

**Real-time updates not working**
- Verify WebSocket connection in browser dev tools
- Check `BASE_URL` configuration

### **Getting Help**

- Check browser console for error messages
- Review application logs for debugging info
- Verify API key was created correctly in admin panel

---

## ✅ Success Checklist

After completing this guide, you should be able to:

- [ ] Start the RaiseMyHand application
- [ ] Access the admin panel and create API keys
- [ ] Create instructor sessions with titles
- [ ] Share sessions via QR code or URL
- [ ] Submit and vote on questions as a student
- [ ] Use presentation mode for classroom projection
- [ ] Moderate flagged content appropriately
- [ ] Write formatted answers with markdown
- [ ] Export session data for analysis

---

## 🎉 What's Next?

### **For Regular Use**

1. **Customize** the .env file with your institution's settings
2. **Train instructors** on the moderation and answer features  
3. **Set up production deployment** with proper SSL and domains
4. **Integrate** with your LMS or class management system

### **Advanced Configuration**

- **PostgreSQL**: Migrate from SQLite for multi-user production
- **Custom Branding**: Modify CSS for institutional colors/logos
- **Analytics**: Set up logging and monitoring for usage insights

### **Educational Best Practices**

- **Encourage participation** by addressing popular questions
- **Use written answers** for complex explanations students can reference
- **Export data** to identify common confusion points
- **Moderate promptly** to maintain appropriate classroom environment

---

**Need more help?** Check the main [README.md](README.md) for detailed configuration options and API documentation.

**Ready for production?** See deployment guides for Docker, SSL, and scaling configurations.