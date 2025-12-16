# Instructor FAQ

Frequently asked questions from instructors using RaiseMyHand.

**Table of Contents:**
- [Getting Started](#getting-started)
- [Managing Sessions](#managing-sessions)
- [Sharing with Students](#sharing-with-students)
- [Moderation & Content](#moderation--content)
- [Answering Questions](#answering-questions)
- [Session Management](#session-management)
- [Data & Reports](#data--reports)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Getting Started

### Q: How do I get started with RaiseMyHand?

**A:** You need three things:
1. **API Key** - Request from your administrator
2. **Browser** - Chrome, Firefox, Safari, or Edge
3. **Internet connection** - For your students

Once you have your API key:
1. Go to `http://localhost:8000/instructor-login` (or your school's URL)
2. Paste your API key
3. Create your first session
4. Share the session with students

*See: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) → "Creating a Session"*

**Screenshot Suggestion:** Show instructor login page with API key entry field

---

### Q: What if I lost my API key?

**A:** API keys are shown only once. You'll need to:
1. Contact your administrator
2. Ask them to create a **new** API key for you
3. They cannot recover the old one - only create new ones

Save your API key securely in a password manager (1Password, LastPass, Bitwarden).

*See: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) → "Creating Your First Session"*

---

### Q: Can I use RaiseMyHand on my phone?

**A:** Yes, but desktop is better for instructors:
- **Desktop** - Recommended (full dashboard, all features visible)
- **Tablet** - Works well (good screen size)
- **Phone** - Works but cramped (hard to see all questions at once)

Students should use their own devices. You should monitor from a laptop or tablet.

---

### Q: Do I need to log in every time?

**A:** Your API key stays valid until:
- Your administrator deactivates it
- You deliberately delete it
- Your account is deactivated

Once logged in via API key, your session persists. You can close the browser and come back later.

---

## Managing Sessions

### Q: How do I create a session?

**A:** Two methods:

**Method 1: Web Interface (Easiest)**
1. Login with API key
2. Click "Create New Session"
3. Enter session title (e.g., "Physics 101 - Lecture 5")
4. Click "Create Session"
5. Done! You get two URLs (student and instructor)

**Method 2: API (Programmatic)**
See [API.md](API.md) → "Create Session" endpoint for automation.

*See: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) → "Creating a Session"*

**Screenshot Suggestion:** Show session creation form and confirmation page

---

### Q: What's the difference between student URL and instructor URL?

**A:** They're different codes:
- **Student URL** - What you give to students (they submit questions and vote)
- **Instructor URL** - Your private dashboard (you moderate and answer)

Never give students your instructor URL. Only share the student URL.

---

### Q: Can I use the same session multiple times?

**A:** Yes! You can:
1. End a session after class
2. Download the report
3. Start a new session next class (different code, fresh questions)

Or you can use the same session code multiple times (questions accumulate). Choose what works best for you.

---

### Q: How long can a session last?

**A:** As long as you want:
- Hours during a long lab
- Days across multiple sessions (some schools keep one session open all semester)
- Sessions stay active until you end them

We recommend ending sessions after each class for clarity.

---

## Sharing with Students

### Q: What's the best way to share the session with students?

**A:** Use QR code (best for in-person):
1. Click "Show QR Code" on your dashboard
2. Display on projector
3. Students scan with phone camera
4. They're instantly in the session

Takes 30 seconds, no typing required.

*See: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) → "Sharing with Students"*

**Screenshot Suggestion:** Show QR code modal with large, clear code

---

### Q: Can I share the URL instead of QR code?

**A:** Yes, perfect for online/hybrid classes:
- **LMS** - Paste in Canvas/Blackboard/Moodle
- **Chat** - Paste in Zoom/Teams/Slack
- **Email** - Send to class mailing list
- **Website** - Add to course syllabus

All methods work. Use whatever fits your workflow.

---

### Q: Is there a password option for sessions?

**A:** Yes, when creating a session:
1. Enter session title
2. (Optional) Enter password
3. Create session

Students must enter the password to join. Use if you want to restrict access.

---

### Q: How do I know if students joined?

**A:** Watch your dashboard:
- Questions start appearing when students are active
- Vote counts update in real-time
- If no questions for a minute, students might not be connected

If worried:
1. Have a trusted student test joining
2. Check WebSocket connection in browser console (F12 → Console)
3. Verify they have the correct URL

---

## Moderation & Content

### Q: What happens if a student submits profanity?

**A:** Automatic workflow:
1. **Student submits:** "What the hell is this?"
2. **System flags it** for profanity
3. **You see it** in "Flagged for Review" tab (hidden from other students)
4. **Shows as censored:** "What the *** is this?"
5. **You decide:** Approve (show censored) or Reject (hide)

*See: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) → "Managing Flagged Questions"*

**Screenshot Suggestion:** Show flagged question in dashboard with "Flagged for Review" tab and action buttons

---

### Q: Can I approve a profane question so students see it?

**A:** Yes! That's exactly what "Approve" does:
- **Before:** Profane question hidden from students
- **After clicking "Approve & Show":** Students see censored version

Use this when:
- Question is legitimate despite profanity
- "What the *** is this?" is a legitimate confused student
- You want to address the topic

All buttons work - you have full control.

---

### Q: What if I accidentally approve or reject a question?

**A:** No problem! Click the opposite button:
- Approved it by mistake? Click "Reject & Hide"
- Rejected it by mistake? Click "Approve & Show"

You can change your mind anytime.

---

### Q: How do I hide a question permanently?

**A:** Two options:

**Option 1: Delete it**
- Completely removes from system
- Can't be undone
- Use for spam or inappropriate questions

**Option 2: Reject it**
- Hides from students
- Still visible to you (strikethrough)
- Can be undone (click "Approve & Show")

---

### Q: Can I see which student asked a question?

**A:** No, that's the point of anonymous:
- Students submit without names
- Questions don't show identity
- Encourages honest questions

This is a feature, not a limitation. Anonymity increases participation.

---

## Answering Questions

### Q: How do I mark a question as answered?

**A:** Click the checkmark button:
1. Read question
2. Answer it verbally during class
3. Click "✓ Mark as Answered"
4. Checkmark appears - students see it's addressed

Use this to help students track which questions you've covered.

*See: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) → "Monitoring Questions During Class"*

**Screenshot Suggestion:** Show dashboard with checkmark button and answered question with checkmark icon

---

### Q: Can I write a detailed written answer?

**A:** Yes! Click "Write Answer":
1. Click button on question
2. Write markdown-formatted answer
3. Click "Publish"
4. Answer appears under question for students

Students see:
- Original question
- Your detailed response
- Timestamps

Great for:
- Sharing formulas or code
- Writing step-by-step explanations
- Creating reference material

*See: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) → "Answering Questions"*

**Screenshot Suggestion:** Show answer writing modal with markdown editor and preview

---

### Q: What markdown formatting is supported?

**A:** Standard markdown:
```markdown
# Heading
## Subheading
**bold**
*italic*
- bullet points
1. numbered list
`code`
[link](url)
```

Live preview available while typing. Plain text also works fine.

---

### Q: Can students see my answer before I publish it?

**A:** No. Answers are:
- **Draft** - Only you see them
- **Published** - Students see them

You control when they see your response. Perfect for preparing detailed answers.

---

## Session Management

### Q: How do I control the voting order?

**A:** Toggle voting on/off:

**When Voting ON:**
- Students can upvote questions
- Order changes as votes come in
- Use when: Collecting questions ("What should I address?")

**When Voting OFF:**
- Voting frozen
- Order stays same
- Use when: Answering a question (no distractions mid-explanation)

Best practice: Toggle off/on for each question.

*See: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) → "Managing Voting"*

---

### Q: Can I pause a session without ending it?

**A:** Pause = end temporarily:
1. Click "End Session"
2. Later, click "Restart Session"
3. Same session code, same questions

Students can't submit new questions while ended, but all old ones remain.

---

### Q: What happens when I end a session?

**A:** Students can no longer:
- Submit questions
- Vote on questions

But they can still:
- See all questions
- See all answers
- Review what was discussed

You can restart if needed.

---

### Q: Why would I end vs. restart a session?

**A:** End = archive for that day

**Use End when:**
- Class is over for the day
- You want to download a report
- You want fresh questions next time

**Use Restart when:**
- You ended by accident
- You want to continue same session next class
- Questions should accumulate across multiple sessions

---

## Data & Reports

### Q: How do I download my session questions?

**A:** Two formats available:

**CSV Format** (open in Excel/Sheets):
1. Go to "My Sessions"
2. Find your session
3. Click "Download Report"
4. Choose CSV
5. Open in Excel

Great for: Analysis, grading, sharing with co-instructors

**JSON Format** (for developers):
- Same process, choose JSON
- For: Programmatic use, archiving, integration

*See: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) → "Downloading Session Data"*

**Screenshot Suggestion:** Show "My Sessions" view with download buttons

---

### Q: What's included in the report?

**A:** CSV includes:
- Question number (Q1, Q2, etc.)
- Full question text
- Upvote count
- Answer status
- Timestamps

Perfect for:
- Attendance documentation
- Learning analytics
- Student engagement metrics
- Content analysis

---

### Q: Can I export answers too?

**A:** Yes! The report includes:
- Which questions you marked as answered
- Written answer text (if provided)
- When you answered

Great for creating session notes or sharing with students.

---

### Q: How long are sessions stored?

**A:** Indefinitely:
- Sessions never auto-delete
- You can download anytime
- Historical data preserved

Archive important sessions by downloading reports.

---

## Troubleshooting

### Q: Questions aren't appearing in real-time

**A:** Check these:

1. **Internet connection** - Ask student to test on different network
2. **WebSocket blocked** - Corporate/school firewall may block WebSocket
3. **Browser issue** - Try incognito mode (disables extensions)
4. **Base URL wrong** - Check that BASE_URL in settings matches your domain

If students say "questions aren't updating", have them:
- Refresh page (F5)
- Try different browser
- Check internet connection

*See: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "WebSocket Connection Failed"*

---

### Q: QR code isn't displaying

**A:** Try these:

1. **Pop-up blocker** - Disable for the site
2. **JavaScript** - Enable in browser settings
3. **Browser** - Try different browser
4. **Use URL instead** - Share student URL directly

QR code is convenient but not required. URL always works.

---

### Q: I can't see flagged questions count

**A:** Refresh page (Ctrl+Shift+R):
- Hard refresh clears cache
- Flagged count should appear

If still not showing:
- Submit a test question with profanity
- Wait a few seconds
- Refresh again

---

### Q: Students can see profane questions

**A:** This is a bug. Report it with:
- Session code
- Question text
- Browser and OS
- Screenshot

Should never happen - questions are filtered server-side. Contact administrator immediately.

*See: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)*

---

### Q: API key not working

**A:** Verify these:

1. **API key correct** - Copy from password manager, don't retype
2. **API key active** - Ask admin if it's enabled
3. **No extra spaces** - Paste carefully
4. **Credentials stored** - Browser might be autocompleting wrong one

If unsure: Request **new** API key from admin. Old one might be deactivated.

---

## Best Practices

### Q: What's the ideal session workflow?

**A:** Recommended flow:

1. **Before class** - Create session (5 min before start)
2. **Students arrive** - Display QR code (5 min)
3. **During class** - Check dashboard every 5-10 minutes
4. **Questions arrive** - Address most upvoted ones
5. **When answering** - Toggle voting OFF (no distractions)
6. **After explaining** - Toggle voting ON (get next priority)
7. **End of class** - Click "End Session"
8. **Later** - Download report if needed

This rhythm keeps students engaged and questions focused.

---

### Q: How often should I check the dashboard?

**A:** Recommended: Every 5-10 minutes

Too frequent:
- Distracts from teaching
- Students don't have time to ask questions

Too infrequent:
- Build-up of unanswered questions
- Students disengage

Find your rhythm. Most instructors check every 5-10 min.

---

### Q: How do I handle controversial or sensitive questions?

**A:** You have options:

1. **Approve & answer** - Address openly, provide context
2. **Reject & discuss separately** - Talk after class privately
3. **Reject & delete** - Remove if completely inappropriate

There's no "right" answer - depends on your course and students. Trust your judgment.

---

### Q: What if I get no questions?

**A:** Normal. Some classes:
- Take time to warm up (5-10 minutes)
- Prefer asking in person
- Don't use anonymous submissions

Encourage participation:
- "Questions? Use RaiseMyHand"
- Make it part of class routine
- Address questions that do come in
- Students see engagement and contribute more

---

### Q: How do I encourage more questions?

**A:** Try these:

1. **Make it routine** - Use every class, students get comfortable
2. **Respond positively** - Address questions with enthusiasm
3. **Use questions as teaching** - Turn Q&A into mini-lessons
4. **Address all upvoted questions** - Shows you're listening
5. **Be clear about anonymous** - Some students only ask anonymously
6. **Thank questioners** - Even though they're anonymous, say "Great question!"

Participation grows with time and example.

---

### Q: Can I use RaiseMyHand for exams or quizzes?

**A:** Not designed for:
- Graded assessments
- Multiple choice quizzes
- Synchronous testing

Better for:
- Lecture discussions
- Lab sessions
- Office hours Q&A
- Review sessions

Use your LMS (Canvas, Blackboard) for graded assessments.

---

### Q: How many students can use one session?

**A:** No hard limit. Should handle:
- 50 students - definitely
- 200 students - probably
- 500+ students - may need server upgrade

If slow with many students, contact administrator about scaling.

---

### Q: Can I reuse sessions across semesters?

**A:** Technically yes, but not recommended:

**Better approach:**
1. Create new session each semester
2. Download reports from old session
3. Delete old session (clean up)
4. Reference old data if needed

Keeps things organized and fresh.

---

## Getting Help

**Can't find an answer?**

1. Check [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) for step-by-step instructions
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common problems
3. Check [API.md](API.md) for technical questions
4. Contact your administrator

**Found a bug?**

Open a GitHub issue with:
- What you were doing
- What happened
- Expected behavior
- Browser and OS
- Screenshot

---

**Last Updated:** 2025-12-16
