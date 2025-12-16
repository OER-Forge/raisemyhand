# Screenshots Guide

This guide recommends which screenshots to take to document the application visually.

## Screenshot Recommendations

### 1. Home Page

**File:** `screenshot-home-page.png`

**What to show:**
- Full width, desktop resolution (1920x1080)
- "Students: Join a Session" section with code entry box
- "Instructors: Create Session" button/section
- Responsive layout with both sections visible

**Instructions:**
1. Go to `http://localhost:8000` or your production URL
2. Don't be logged in to anything
3. Show full page with both student and instructor sections
4. Desktop view

**Why:** Users need to see entry points

---

### 2. Student Interface - Question Submission

**File:** `screenshot-student-view.png`

**What to show:**
- Student session page
- Question submission text box at top
- Empty or with a few example questions
- Mobile-friendly layout
- Submit button and voting interface

**Instructions:**
1. Open student session in desktop browser
2. Don't submit anything yet (show clean state)
3. Show the input box for questions
4. Show vote buttons next to questions
5. Show upvote count

**Why:** Students need to see how to submit questions

---

### 3. Student Interface - Real-time Updates

**File:** `screenshot-student-with-questions.png`

**What to show:**
- Student view with 5-10 questions
- Questions sorted by upvote count (highest first)
- Different vote counts visible
- Some questions with checkmarks (answered)
- Clean, readable layout

**Instructions:**
1. Create a test session
2. Submit several test questions with different vote counts
3. Mark some as answered
4. Screenshot with questions visible
5. Desktop view showing multiple questions

**Why:** Potential users see real-time voting in action

---

### 4. Student Mobile View

**File:** `screenshot-student-mobile.png`

**What to show:**
- Same student view but on mobile (iPhone/Android)
- Portrait orientation
- Questions readable and buttons tapable
- Responsive layout
- Question text visible without horizontal scrolling

**Instructions:**
1. Open student session on mobile phone
2. Portrait orientation
3. Show question list and voting
4. At least 3-4 questions visible
5. Screenshot from actual device or browser dev tools mobile view

**Why:** Users need to see mobile experience works

---

### 5. Instructor Dashboard - All Questions Tab

**File:** `screenshot-instructor-all-questions.png`

**What to show:**
- Instructor dashboard main view
- Session title and metadata
- All Questions tab (active)
- 5-10 questions with vote counts
- Question numbering (Q1, Q2, etc.)
- Action buttons visible
- Vote count visible
- Toggle voting button

**Instructions:**
1. Login as instructor
2. Go to active session
3. Make sure "All Questions" tab is selected
4. Have at least 5-10 questions in session
5. Desktop resolution (1920x1080)
6. Show the full dashboard

**Why:** Instructors need to see their primary interface

---

### 6. Instructor Dashboard - Flagged Questions Tab

**File:** `screenshot-instructor-flagged-questions.png`

**What to show:**
- Instructor dashboard
- Flagged for Review tab (active)
- Red badge showing count
- At least one flagged question
- Censored profanity visible (e.g., "What the *** is this?")
- ⚠️ flag icon visible
- Approve, Reject, and Delete buttons visible
- All buttons operational (not grayed out)

**Instructions:**
1. Login as instructor
2. Go to session with flagged questions
3. Click "Flagged for Review" tab
4. Submit a test question with profanity to create one
5. Show the flagged question with buttons
6. Don't click the buttons yet

**Why:** Instructors need to understand content moderation workflow

---

### 7. Instructor Dashboard - Flagged Question Moderation

**File:** `screenshot-instructor-approve-action.png`

**What to show:**
- Flagged question with buttons visible
- Show buttons: "✓ Approve & Show", "✗ Reject & Hide", "🗑️ Delete"
- Buttons are clearly clickable (not disabled)
- Censored text visible
- Original profanity shown in hover/tool-tip (if applicable)

**Instructions:**
1. Same setup as screenshot 6
2. Hover over or show the approval buttons
3. Make buttons visible and readable
4. Show the three button options

**Why:** Instructors need to know their options for moderation

---

### 8. QR Code Display

**File:** `screenshot-qr-code.png`

**What to show:**
- QR code modal/window
- Large, scannable QR code
- Session title near QR
- URL visible below QR code
- Modal title or context

**Instructions:**
1. Login as instructor
2. Go to session dashboard
3. Click "Show QR Code"
4. Screenshot the QR code
5. Make it large and clear
6. Ensure it's readable

**Why:** Teachers need to see how to display QR code for students

---

### 9. Instructor Presentation Mode / Stats

**File:** `screenshot-stats-view.png`

**What to show:**
- Stats page or presentation mode
- Large, readable text
- Question count
- Upvote count
- Answered count
- Session title
- Suitable for classroom projection
- Clean, minimal design

**Instructions:**
1. Go to instructor dashboard
2. Click "Presentation Mode" or "View Stats"
3. Screenshot the full screen
4. Ensure text is large and readable
5. Show it would be visible on projector

**Why:** Teachers need to see engagement metrics

---

### 10. Admin Panel - Dashboard

**File:** `screenshot-admin-dashboard.png`

**What to show:**
- Admin login page success
- Admin dashboard overview
- Navigation menu
- Statistics visible
- API keys section accessible
- Clean, professional layout

**Instructions:**
1. Login to admin panel with credentials
2. Go to dashboard
3. Screenshot main admin page
4. Show navigation options
5. Desktop resolution

**Why:** Administrators need to see management interface

---

### 11. Admin Panel - API Key Management

**File:** `screenshot-admin-api-keys.png`

**What to show:**
- API Keys section in admin panel
- List of existing API keys
- Create New API Key button
- Keys listed with names and status (Active/Inactive)
- Actions (delete, deactivate) visible

**Instructions:**
1. In admin panel, go to API Keys
2. Show list of existing keys
3. Show "Create New API Key" button
4. Screenshot the list view
5. Don't show actual key values

**Why:** Admins need to see key management interface

---

### 12. API Key Creation Success

**File:** `screenshot-api-key-created.png`

**What to show:**
- API key successfully generated
- Full API key visible (blurred/redacted for public docs)
- "Copy to Clipboard" button visible
- Warning about saving the key
- Professional confirmation message

**Instructions:**
1. Create a new API key in admin panel
2. Screenshot the success screen
3. Show the full key (can be fake/redacted)
4. Show copy button
5. Show one-time warning message

**Why:** Admins need to see how to provide keys to instructors

---

### 13. Browser Console - Profanity Detection

**File:** `screenshot-console-logs.png`

**What to show:**
- Browser dev tools (F12) console tab
- Log messages showing question received
- Filter/censoring messages visible
- Shows `[STUDENT]` or `[INSTRUCTOR]` prefixes
- Multiple messages showing real-time activity

**Instructions:**
1. Open browser dev tools (F12)
2. Go to Console tab
3. Clear any existing logs: `console.clear()`
4. Submit a question as student
5. Screenshot showing new log entries
6. Show message about filtering if applicable

**Why:** Developers/admins need to see system is working

---

### 14. Session Report Download

**File:** `screenshot-download-report.png`

**What to show:**
- Instructor session view
- "Download Report" button visible
- Format options (CSV/JSON) shown
- After clicking, the report is downloaded

**Instructions:**
1. End a session in instructor view
2. Go to "My Sessions"
3. Find ended session
4. Show "Download Report" option
5. Screenshot the download dialog/options

**Why:** Instructors need to know how to export data

---

### 15. Session Join via QR (Mobile)

**File:** `screenshot-mobile-qr-scan.png`

**What to show:**
- Mobile phone camera
- QR code being scanned
- Safari/Chrome notification to open link
- Clear, in-focus QR code

**Instructions:**
1. Have QR code displayed on computer
2. Use mobile phone camera to scan
3. Screenshot the moment before clicking the notification
4. Ensure QR code is in frame
5. Show typical mobile QR experience

**Why:** Students need to understand QR scanning workflow

---

### 16. Error States (Optional)

**File:** `screenshot-error-invalid-session.png`

**What to show:**
- Error message when session code is wrong
- User-friendly error text
- Option to try again
- Professional error styling

**Instructions:**
1. Go to session join page
2. Enter invalid session code
3. Try to join
4. Screenshot error message
5. Desktop view

**Why:** Shows error handling is professional

---

## Recommended Resolutions

### Desktop Screenshots
- Width: 1920px
- Height: 1080px
- Format: PNG (for quality)

### Mobile Screenshots
- iPhone: 390x844 (typical modern phone)
- Android: 360x800
- Format: PNG

### QR Code Screenshot
- Size: Actual size from browser (usually 400-600px)
- Format: PNG (best for QR codes)

## File Naming Convention

Use this pattern for consistency:

```
screenshot-<feature>-<view>-<resolution>.png
```

Examples:
- `screenshot-student-view-questions-desktop.png`
- `screenshot-instructor-flagged-mobile.png`
- `screenshot-admin-api-keys-desktop.png`

## Organizing Screenshots

Suggested directory structure:

```
docs/screenshots/
├── student-view/
│   ├── home-page.png
│   ├── question-list.png
│   └── mobile-view.png
├── instructor-view/
│   ├── dashboard-all-questions.png
│   ├── dashboard-flagged-questions.png
│   ├── qr-code.png
│   └── stats-view.png
├── admin-view/
│   ├── dashboard.png
│   ├── api-keys-list.png
│   └── api-key-created.png
└── error-states/
    └── invalid-session.png
```

## Tips for Good Screenshots

1. **Use real data** - Submit actual test questions, don't fake the UI

2. **Consistent styling** - Use same browser, resolution, zoom level for all

3. **Show context** - Include page titles, buttons, and navigation

4. **Clean slate** - Close other windows/tabs to minimize distractions

5. **High contrast** - Ensure text is readable in screenshot

6. **Test readability** - Resize and view at different sizes to verify legibility

7. **Consistent timestamp** - Take screenshots at similar times for consistent look

8. **Professional appearance** - Use production domain names, clean test data

9. **Include variations** - Show both empty states and populated states

10. **Mobile first** - Prioritize mobile screenshots as mobile is increasingly important

## Updating Screenshots

When to retake screenshots:

- Major UI changes
- New features added
- Color scheme changes
- Resolution/responsive design updates
- At least annually (designs may shift)

## Accessibility

When creating screenshots:

- Use high contrast (dark text on light background)
- Include alt text descriptions
- Ensure text is at least 12pt in screenshots
- Use clear, readable fonts
- Avoid small icons (make them visible)

## Using Screenshots in Documentation

Template for including screenshots:

```markdown
## Feature Title

Description of the feature.

![Student view with multiple questions](../screenshots/student-view/question-list.png)

**Figure 1:** Student interface showing question list with voting

### How to use this feature

1. Step one
2. Step two
3. Step three

![Admin panel API keys](../screenshots/admin-view/api-keys-list.png)

**Figure 2:** API Key management in admin dashboard
```

Always include:
- Image file path
- Descriptive alt text
- Caption with "Figure X:" numbering
- Context explaining what's shown
