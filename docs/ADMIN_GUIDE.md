# Admin Guide

## Accessing the Admin Panel

1. Go to your instance: `https://yourschool.edu/admin-login`
2. Login with:
   - **Username:** `admin`
   - **Password:** (Set during deployment or stored in secrets file)

## Admin Dashboard Overview

The Admin Panel allows you to:
- Create and manage API keys for instructors
- View system status and configuration
- Monitor active sessions
- Manage profanity filter settings

## Managing API Keys

API Keys allow instructors to create and manage sessions. Each instructor needs one.

### Creating a New API Key

1. In Admin Dashboard, go to **"API Keys"** section
2. Click **"Create New API Key"**
3. Enter a descriptive name:
   - Format: "Department - Instructor Name - Course Code"
   - Example: "Engineering - Prof. Smith - ME301"
4. Click **"Generate Key"**
5. Key appears once - have instructor copy it immediately

### Key Format

API keys look like:
```
rmh_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**Note:** Keys are shown only once after creation. Instructors must save them securely.

### Managing Existing Keys

You can:
- **View** - See all created keys and their creation dates
- **Deactivate** - Disable a key (instructor can't create sessions)
- **Reactivate** - Re-enable a previously deactivated key
- **Delete** - Permanently remove a key

### Key Policies

- One key per instructor (typically)
- Keys never expire unless you deactivate them
- Deactivated keys can be reactivated
- Create new key if instructor loses theirs
- Keys provide full session creation privileges

## System Configuration

### Profanity Filter

The system includes an automatic profanity detection system:

**How it works:**
- Student submits question
- System checks for profanity automatically
- Flagged questions are hidden from students
- Instructor reviews in "Flagged for Review" tab

**Instructor options:**
- **Approve** - Show censored version (profanity becomes ***)
- **Reject** - Keep hidden from students
- **Delete** - Remove permanently

**To disable profanity filter (not recommended):**
- Contact system administrator
- Modify configuration file
- Restart application

## Monitoring

### Active Sessions

View all currently active sessions:
- Session title
- Question count
- Upvote count
- Duration
- Active instructor

### Session Statistics

- Total sessions created
- Questions per session (average)
- Engagement metrics
- Most active time periods

## Troubleshooting as Admin

### "Instructor forgot API key"

Solution:
1. Create a new API key for them
2. Have them delete the old one from password manager
3. Provide new key securely

### "Key is deactivated but instructor can't use it"

Solution:
1. Verify key is reactivated
2. Have instructor try again
3. Check browser cache (may need incognito window)
4. Verify internet connection

### "Too many API keys created"

Best practices:
- One key per instructor/role
- Archive old keys (note old ones are still valid)
- Document who has which key
- Deactivate keys for people who left

### "Students can see flagged questions"

This indicates a bug. Check:
1. Refresh browser to clear cache
2. Check browser console for errors
3. Report to system administrator with:
   - Session code
   - Question ID
   - Screenshot
   - Browser and OS version

### "Profanity filter not working"

Check:
1. Is filter enabled in system configuration?
2. Try restarting the application
3. Check system logs for errors
4. Verify better-profanity library is installed

## Database and Data

### Data Storage

- Questions and votes stored in database
- Accessible via API
- Exportable by instructors (CSV/JSON)

### Data Backup

- Regularly backup your database file
- Store backups in secure location
- Document backup schedule
- Test recovery procedures

### Data Retention

- System keeps all data indefinitely
- Instructors can download and archive
- Database grows with usage
- Consider cleanup strategies for old sessions

## Security Best Practices

1. **Admin Password**
   - Change from default immediately
   - Use strong password (16+ characters)
   - Store securely in password manager
   - Never share with instructors

2. **API Keys**
   - Never reuse keys across departments
   - Deactivate keys for staff who leave
   - Monitor key creation for unusual patterns
   - Document who has which key

3. **HTTPS**
   - Always use HTTPS in production
   - Install SSL certificate
   - Redirect HTTP to HTTPS

4. **Database**
   - Regular backups
   - Secure storage location
   - Restrict direct database access
   - Monitor for unauthorized changes

5. **Server Access**
   - Restrict admin login to trusted networks if possible
   - Use VPN for remote access
   - Monitor login attempts
   - Keep server software updated

## Maintenance Tasks

### Daily
- Monitor active sessions (optional)
- Check for error logs
- Verify backups completed

### Weekly
- Review new API key requests
- Check for deactivated keys that need cleanup
- Verify system status

### Monthly
- Review database size
- Archive old session data if needed
- Update documentation
- Review usage statistics

### Quarterly
- Security audit
- Backup verification
- Performance review
- Plan upgrades

## Common Questions

**Q: Can I limit how many questions a student can submit?**
A: No - the system allows unlimited submissions per session. Implement this via instructor monitoring.

**Q: Can students see each other's names?**
A: No - all submissions and votes are anonymous.

**Q: How long do sessions last?**
A: Indefinitely until the instructor ends them. Sessions stay active across page refreshes.

**Q: Can I reset an instructor's password?**
A: No - each instructor has an API key, not a password. Create a new API key if they lose theirs.

**Q: What's the maximum number of students in a session?**
A: No hard limit - system should handle hundreds of concurrent students.

**Q: Can I export all data from the system?**
A: Instructors can export individual sessions. Use database tools for full system export.

**Q: How do I know if profanity filter is working?**
A: Test by having students submit questions with common profanity. Check the "Flagged for Review" tab.

## Getting Help

- Check application logs for errors
- Verify all dependencies are installed
- Test connectivity to database
- Review system requirements
- Contact system support with:
  - Error logs
  - Steps to reproduce
  - System information (OS, browser, etc.)
