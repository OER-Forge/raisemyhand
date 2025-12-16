# Instructor Guide

## Before You Start

You need an **API Key** to use RaiseMyHand. Contact your admin to create one in the Admin Panel.

## Creating a Session

### Via Web Interface (Recommended)

1. Go to **Instructor Login**: `https://yourschool.edu/instructor-login`
2. Paste your API key
3. Click **"Login"**
4. Click **"Create New Session"**
5. Enter:
   - **Title** - Session name (e.g., "Physics 101 - Lecture 12")
   - **Password** - (Optional) Leave blank for public sessions
6. Click **"Create Session"**

You'll see your new session with two URLs:
- **Student URL** - Share this with students
- **Instructor URL** - Your personal dashboard

## Understanding Your Dashboard

Your instructor dashboard shows:

```
Session Title
📊 3 questions  •  ⬆️ 12 votes  •  🟢 Active
```

### Sections

**All Questions Tab:**
- Displays all approved questions
- Sorted by upvote count (highest first)
- Each question shows vote count and answer status

**Flagged for Review Tab:**
- Shows questions that contain profanity or need review
- Count appears in red badge
- All buttons are operational for review

**Question Display:**
- **Q1, Q2, Q3...** - Permanent question numbers for classroom reference
- **⬆️ count** - Number of student upvotes
- **[Mark as Answered]** - Mark question as addressed
- **[Write Answer]** - Add detailed markdown response
- **[Approve/Reject]** - Review flagged questions
- **[Hide]** - Remove question from student view
- **[Delete]** - Permanently remove question

## Sharing with Students

### Option 1: QR Code (In-Person Classes)

1. Click **"Show QR Code"** on your dashboard
2. A large QR code appears with the student URL embedded
3. **Display it on your projector/screen** for 5+ minutes
4. Students scan with their phone camera
5. They're instantly taken to the session

**Tip:** Leave the QR code visible throughout class so latecomers can join.

### Option 2: Copy & Share URL

1. Click the **Student URL** to copy it
2. Share via:
   - Email to class list
   - Paste in Zoom/Teams/Slack chat
   - Post in Canvas/Blackboard/Moodle
   - Add to your course website

### Option 3: Session Code Only

Students can:
1. Go to the home page
2. Enter your session code manually
3. Click "Join"

## Monitoring Questions During Class

### Best Practices

1. **Keep dashboard open** on laptop/tablet while teaching

2. **Check every 5-10 minutes** for new questions

3. **Prioritize by votes** - Address most upvoted questions first

4. **Use question numbers** - Say "I'll answer Q3 now"

5. **Mark as answered** - Click checkmark when you address a question

6. **Watch voting status** - Toggle voting when needed (see below)

### Question Status Icons

- ✅ **Answered** - You've addressed this question
- 📝 **Answered with Details** - You've written a detailed response
- ⚠️ **Flagged** - Contains profanity, needs your review
- 🔴 **Rejected** - Hidden from students

## Managing Flagged Questions

When a student submits a question with profanity, it appears in the **"Flagged for Review"** tab.

### How It Works

1. **Student submits:** "What the hell is the answer?"
2. **System flags it** for profanity detection
3. **Appears in Flagged tab** - visible to you, NOT visible to students
4. **Shows as censored:** "What the *** is the answer?"

### Your Options

Click one of three buttons on the flagged question:

#### ✓ Approve & Show
- Question becomes visible to students
- Shows as censored version: "What the *** is the answer?"
- Students see it immediately
- Use this if the question is legitimate despite profanity

#### ✗ Reject & Hide
- Question remains hidden from students permanently
- Appears with strikethrough in your view
- Use this for inappropriate questions

#### 🗑️ Delete
- Permanently removes question from system
- Doesn't appear anywhere

**All buttons remain operational** - You can:
- Approve now, then reject later (button toggles)
- Change your mind and unflag a rejected question
- Delete at any time

## Working with Profanity

RaiseMyHand automatically detects common profanity like:
- Profane adjectives (damn, crap, hell, etc.)
- Offensive terms
- Vulgar expressions

### What Gets Flagged

These words trigger the filter:
- "damn", "hell", "crap", "ass", "bastard", "pissed", etc.
- More offensive terms

### What Doesn't Get Flagged

- Misspellings (e.g., "heck" instead of "hell")
- Academic terms (e.g., "volatile" in chemistry)
- Casual language variations

**Note:** Capitalization doesn't matter - "HELL" and "hell" both get flagged.

## Managing Voting

You can **toggle voting on/off** during your session:

### Toggle Voting Button

**When Voting is ON:**
- Students can upvote/downvote questions
- Question order changes as votes come in
- Use during question collection phase

**When Voting is OFF:**
- Students can't upvote
- Question order freezes
- Question remains at current vote count
- Use when explaining a question so the order doesn't change mid-answer

### Best Strategy

1. **Start class** with voting ON
2. **Ask "What should I address first?"** - Students upvote priorities
3. **Start answering Q1** - Click "Toggle Voting" to freeze order
4. **Finish Q1 answer** - Click "Toggle Voting" again to re-enable
5. **Repeat** for each question

## Ending Your Session

Click **"End Session"** when finished:

- Students can no longer submit questions or vote
- All questions and votes are preserved
- You can restart the session if needed

### After Ending

You can:
- **View Statistics** - See engagement metrics on the stats page
- **Download Report** - Export as JSON or CSV
- **Restart Session** - If you ended by accident, reactivate it

## Downloading Session Data

### Via Dashboard

1. Go to **"My Sessions"**
2. Find your session
3. Click **"Download Report"**
4. Choose format:
   - **CSV** - Open in Excel/Sheets for analysis
   - **JSON** - For programmatic use

### CSV Format Includes

- Question number
- Full question text
- Upvote count
- Answered status
- Timestamps

### JSON Format Includes

- Session metadata
- Engagement statistics
- All questions with full details
- Answer information

**Use cases:**
- Grade participation
- Document student learning
- Share results with other instructors
- Analyze teaching effectiveness

## Administrative Controls

### Session Password (Optional)

When creating a session, you can set a password. This:
- Requires students to enter password to access
- Works for all three joining methods (QR, URL, code)
- Prevents unauthorized access

### Presentation Mode

Click **"Presentation Mode"** to:
- Display stats in full-screen
- Show on classroom projector
- Display vote counts and engagement metrics

## Keyboard Shortcuts

- **Enter** - Submit question or interaction
- **Tab** - Navigate between buttons
- **Space** - Toggle upvote on selected question

## Troubleshooting

### "API key not working"
- Double-check it was copied correctly
- Contact your admin to verify it's active
- Try creating a new API key

### "Students can't see QR code"
- Check that QR code modal is not blocked
- Try sharing the Student URL directly instead
- Try in an incognito/private window

### "Questions aren't appearing in real-time"
- Check your WebSocket connection (F12 → Console)
- Verify students are online
- Try refreshing your dashboard
- Check browser network settings (may require firewall changes)

### "Profane questions appearing to students"
- Questions are typically hidden within a few seconds
- Try refreshing your browser
- Check that "Flagged for Review" tab shows the count
- Contact your administrator

### "Can't download report"
- Try different format (CSV vs JSON)
- Check browser download settings
- Try clearing browser cache
- Try in a different browser

## Tips for Success

1. **Start Early** - Create session 5 minutes before class starts

2. **Test Student URL** - Open in incognito window before class

3. **Display QR Code Early** - Put it up as students arrive so they can join

4. **Monitor Actively** - Check dashboard every 5-10 minutes

5. **Address Popular Questions** - Prioritize by vote count

6. **Mark as Answered** - This helps students see what's been addressed

7. **Give Clear Feedback** - Write detailed answers when needed

8. **Manage Timing** - Toggle voting when needed to control question order

9. **Save Data** - Download report after important sessions

10. **Communicate with Students** - Tell them the session is ending so they know
