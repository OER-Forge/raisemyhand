# RaiseMyHand Documentation

Welcome to the RaiseMyHand documentation hub. Find guides for every role and use case.

## Quick Navigation

### For Users

**I'm a student - how do I participate?**
→ [Student Guide](STUDENT_GUIDE.md)

**I'm an instructor - how do I run a session?**
→ [Instructor Guide](INSTRUCTOR_GUIDE.md)

**I'm an admin - how do I manage the system?**
→ [Admin Guide](ADMIN_GUIDE.md)

### For Developers & IT

**I want to deploy RaiseMyHand**
→ [Deployment Guide](DEPLOYMENT.md)

**I need the API reference**
→ [API Documentation](API.md)

**I'm having technical problems**
→ [Troubleshooting Guide](TROUBLESHOOTING.md)

### Information

**What features are available?**
→ [Features Overview](FEATURES.md)

**Where do I get screenshots?**
→ [Screenshots & Visual Guide](SCREENSHOTS.md)

---

## Documentation Overview

### User Guides

- **[STUDENT_GUIDE.md](STUDENT_GUIDE.md)** - How to join sessions, submit questions, vote, and see answers
- **[INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md)** - How to create sessions, moderate content, manage questions, and download reports
- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** - How to manage API keys, configure system, and monitor usage

### Technical Guides

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - How to deploy to production with Docker, Nginx, and SSL
- **[API.md](API.md)** - Complete REST API reference for programmatic access
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Solutions for common problems and errors

### Reference

- **[FEATURES.md](FEATURES.md)** - Current features and capabilities
- **[SCREENSHOTS.md](SCREENSHOTS.md)** - Recommended screenshots and visual documentation

---

## What is RaiseMyHand?

RaiseMyHand is a real-time classroom question management system that lets:

- **Students** submit questions anonymously and vote on what matters most
- **Instructors** monitor, moderate, and respond to questions in real-time
- **Admins** manage users and system configuration

Perfect for lectures, labs, seminars, and online classes.

**Key features:**
- Anonymous question submission
- Real-time upvoting
- Content moderation with profanity detection
- QR code for easy student access
- Session statistics and reporting
- WebSocket for instant updates

---

## Getting Started

### For Students
1. Ask your instructor for a session URL or QR code
2. Scan the QR code or click the link
3. Submit your question anonymously
4. Upvote questions you want answered
5. See instructor responses in real-time

See [Student Guide](STUDENT_GUIDE.md) for details.

### For Instructors
1. Get an API key from your admin
2. Create a session
3. Share the QR code or URL with students
4. Monitor questions in real-time
5. Moderate flagged content
6. Download session reports

See [Instructor Guide](INSTRUCTOR_GUIDE.md) for details.

### For Admins
1. Deploy the application
2. Create API keys for instructors
3. Monitor system health
4. Configure settings

See [Deployment Guide](DEPLOYMENT.md) and [Admin Guide](ADMIN_GUIDE.md).

---

## Common Tasks

### Student Tasks
- [Join a session](STUDENT_GUIDE.md#getting-started)
- [Submit a question](STUDENT_GUIDE.md#how-to-participate)
- [Upvote questions](STUDENT_GUIDE.md#upvoting-questions)
- [See answers](STUDENT_GUIDE.md#seeing-answers)

### Instructor Tasks
- [Create a session](INSTRUCTOR_GUIDE.md#creating-a-session)
- [Share with students](INSTRUCTOR_GUIDE.md#sharing-with-students)
- [Monitor questions](INSTRUCTOR_GUIDE.md#monitoring-questions-during-class)
- [Moderate flagged content](INSTRUCTOR_GUIDE.md#managing-flagged-questions)
- [Download reports](INSTRUCTOR_GUIDE.md#downloading-session-data)
- [End a session](INSTRUCTOR_GUIDE.md#ending-your-session)

### Admin Tasks
- [Deploy application](DEPLOYMENT.md#quick-start-with-docker-recommended)
- [Create API keys](ADMIN_GUIDE.md#creating-a-new-api-key)
- [Configure system](ADMIN_GUIDE.md#system-configuration)
- [Monitor sessions](ADMIN_GUIDE.md#monitoring)

---

## Troubleshooting

Having issues? Check the [Troubleshooting Guide](TROUBLESHOOTING.md) for:

- Application won't start
- Network issues (WebSocket connection failed)
- Authentication problems
- Content moderation issues
- Display and performance problems
- Mobile compatibility

---

## API & Integration

For developers:

- **[API Reference](API.md)** - All endpoints with examples
- **[WebSocket Documentation](API.md#websocket-connection)** - Real-time communication
- **[Code Examples](API.md#examples)** - Python, Bash, JavaScript samples

---

## Features

Current capabilities:

- Anonymous question submission
- Real-time voting system
- Content moderation (profanity detection)
- Three-state moderation (Approved/Flagged/Rejected)
- Written instructor responses (markdown)
- QR code generation
- Presentation mode for classroom projection
- Session statistics and metrics
- CSV & JSON data export
- Rate limiting and security
- Mobile-responsive design
- WebSocket for instant updates

See [Features Overview](FEATURES.md) for complete list.

---

## Deployment Options

### Option 1: Docker (Recommended)
Quick setup on any server:
```bash
docker compose up -d
```
See [Deployment Guide - Docker](DEPLOYMENT.md#quick-start-with-docker-recommended)

### Option 2: Production with Nginx + SSL
Full production setup:
- HTTPS/SSL encryption
- Nginx reverse proxy
- PostgreSQL database
- Automatic certificate renewal

See [Deployment Guide - Nginx Setup](DEPLOYMENT.md#production-setup-with-nginx--ssl)

---

## Configuration

Essential settings in `.env`:

```bash
BASE_URL=https://questions.yourschool.edu
ADMIN_PASSWORD=YourSecurePassword123!
TIMEZONE=America/New_York
DATABASE_URL=sqlite:///./data/raisemyhand.db
```

See [Deployment Guide](DEPLOYMENT.md#environment-configuration) for all options.

---

## Screenshots & Visuals

Need visual documentation? See [Screenshots Guide](SCREENSHOTS.md) for:
- What screenshots to take
- Where to place them
- How to organize them
- Recommended resolutions and formats

---

## Support

**Documentation issues?**
- Check relevant guide for your role
- See Troubleshooting guide for common problems
- Review API documentation for technical questions

**Found a bug?**
- Open a GitHub issue with details
- Include error message and reproduction steps
- Attach relevant logs or screenshots

**Have a feature request?**
- Open a GitHub issue with "enhancement" label
- Describe the use case
- Include why it would help

---

## Document Structure

```
docs/
├── README.md                    # This file - documentation hub
├── FEATURES.md                  # Current capabilities
├── STUDENT_GUIDE.md             # For students
├── INSTRUCTOR_GUIDE.md          # For instructors
├── ADMIN_GUIDE.md               # For administrators
├── DEPLOYMENT.md                # Production deployment
├── TROUBLESHOOTING.md           # Common problems & solutions
├── API.md                       # REST API reference
├── SCREENSHOTS.md               # Visual documentation guide
├── setup/                       # Legacy setup guides
├── deployment/                  # Legacy deployment guides
└── archive/                     # Historical documentation
```

---

## Last Updated

This documentation was updated for the current version of RaiseMyHand. Always check the repository for the latest version.

---

## Quick Links

- 🏠 [Main README](../README.md)
- 🌐 [GitHub Repository](#)
- 🐛 [Issue Tracker](#)
- 📚 [API Docs Swagger UI](#) - Available at `/docs` on your instance

---

**Built for education with ❤️**

For questions about this documentation, please refer to the appropriate guide or open an issue on GitHub.
