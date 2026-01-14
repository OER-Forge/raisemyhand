# Features

RaiseMyHand is a real-time classroom question system that enables students to ask questions anonymously and instructors to moderate and answer them in real-time.

## Student Features

- **Anonymous Question Submission** - Submit questions without revealing identity
- **Real-time Voting** - Upvote questions to show instructor priorities
- **Instant Updates** - See new questions and instructor responses as they happen
- **Mobile Friendly** - Works on phones, tablets, and computers
- **QR Code Access** - Scan QR code displayed by instructor to join session
- **Vote Transparency** - See how many other students have upvoted each question

## Instructor Features

- **Real-time Dashboard** - Monitor all incoming questions live during class
- **Auto-sorting** - Questions automatically sort by upvote count
- **Question Numbering** - Persistent Q1, Q2, Q3... numbering for classroom reference
- **Vote Management** - Toggle voting on/off to freeze question order when needed
- **Content Moderation** - Review and approve/reject flagged questions
- **Question Status** - Mark questions as answered or hidden
- **Session Control** - Start, pause, and end sessions with one click
- **Data Export** - Download session data as JSON or CSV
- **Written Answers** - Write detailed responses with markdown formatting
- **Presentation Mode** - Full-screen stats view for classroom projection
- **Multi-monitor Support** - Pop-out QR code and stats windows

## Content Moderation

- **Profanity Detection** - Automatic flagging of profane content
- **Three-state System** - Content is Approved, Flagged, or Rejected
  - **Approved** - Visible to students (profanity is automatically censored as ***)
  - **Flagged** - Hidden from students, requires instructor review
  - **Rejected** - Hidden from students permanently
- **Server-side Filtering** - Flagged/rejected content never reaches student view
- **Instructor Control** - All buttons operational - approve, reject, or delete questions

## Security

- **Rate Limiting** - Prevents spam and DDoS attacks
- **CSRF Protection** - Prevents unauthorized state changes
- **XSS Prevention** - HTML sanitization to prevent injection attacks
- **Password Security** - Admin passwords hashed with bcrypt
- **Session Isolation** - Students only see approved content
- **Authentication** - API key authentication for instructors

## Admin Features

- **User Management** - Create and manage API keys for instructors
- **System Configuration** - Manage profanity filter settings
- **Session Overview** - View all active sessions and usage statistics
- **Key Management** - Enable/disable API keys as needed

## User Interface

- **Responsive Design** - Works on all screen sizes
- **Keyboard Accessible** - Full keyboard navigation support
- **Vanilla JavaScript** - No framework dependencies for lightweight performance
- **Real-time Synchronization** - WebSocket-based instant updates across all users

## Browser Compatibility

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Android Chrome)

## Scalability & Performance

RaiseMyHand is tested and verified to handle large classroom environments:

### Verified Performance

**200+ Concurrent Students**
- **Success Rate:** 99.92% (13,469/13,480 requests)
- **Average Response Time:** 932ms
- **95th Percentile Response Time:** 1840ms
- **Throughput:** 45 requests/second sustained
- **Error Rate:** 0.08% (gracefully handled race conditions)

### Tested Workload

Per-student behavior during 5-minute sustained load test:
- Submit questions at 3x rate (~3 questions/minute total)
- Vote on questions at 5x rate (~5 votes/minute per user)
- Fetch question lists periodically
- Check session statistics every 2-3 seconds

### Scaling Limits

| Concurrent Users | Configuration | Success Rate | Status |
|-----------------|---------------|--------------|--------|
| 100 | Single worker | 99.98% | ✅ Excellent |
| 200 | 4 workers | 99.92% | ✅ Verified |
| 300 | 8 workers | ~99.5% | ✅ Estimated |
| 500+ | 16+ workers + DB scaling | ~95%+ | ✅ Possible |

See [Load Testing Report](LOAD_TESTING.md) and [Performance Tuning](PRODUCTION_DEPLOYMENT.md#performance-tuning) for detailed methodology and optimization strategies.

## Not Included

RaiseMyHand does **not** include:

- Student authentication/login - Sessions are anonymous
- Recording or archiving of live sessions beyond basic exports
- Video or audio integration
- Integration with Learning Management Systems (Canvas, Blackboard, etc.)
- Mobile apps (web-based only)
- User accounts for students
- Persistent student profiles across sessions
