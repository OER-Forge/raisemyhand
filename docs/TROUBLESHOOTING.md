# Troubleshooting Guide

## General Issues

### Application Won't Start

**Symptom:** Application crashes when starting, or shows connection errors.

**Solutions:**

1. Check logs for errors:
```bash
docker compose logs
```

2. Verify .env configuration:
```bash
cat .env | grep -E "HOST|PORT|DATABASE"
```

3. Check port availability:
```bash
lsof -i :8000  # If port 8000 is in use, change PORT in .env
```

4. Verify database file permissions:
```bash
# For SQLite
ls -la ./data/
chmod 755 ./data/
```

5. Restart cleanly:
```bash
docker compose down -v
docker compose up -d
```

### High CPU Usage

**Symptom:** Server running slowly or CPU at 100%.

**Causes:**
- Too many concurrent users
- Inefficient query
- WebSocket connection issues

**Solutions:**

1. Check current load:
```bash
docker stats
```

2. View active sessions:
- Go to Admin Panel
- Check "Active Sessions" count

3. Identify slow queries:
- Check application logs
- Look for database errors

4. Temporary fix: Restart application
```bash
docker compose restart
```

5. Long-term: Upgrade server resources or add load balancer

### High Memory Usage

**Symptom:** Memory usage grows over time, application becomes slow.

**Causes:**
- Memory leak in application
- Too many cached WebSocket connections
- Large database

**Solutions:**

1. Check memory usage:
```bash
docker stats --no-stream
```

2. Restart to clear memory:
```bash
docker compose restart
```

3. If persistent after restart:
   - Check application logs for errors
   - Contact system administrator
   - Consider upgrading server

4. Monitor with memory limits:
```yaml
# docker-compose.yml
services:
  raisemyhand:
    mem_limit: 2g
```

## Network Issues

### WebSocket Connection Failed

**Symptom:** Real-time updates not working. New questions don't appear automatically.

**Symptoms in browser:**
- Console shows WebSocket errors
- Questions only appear after refresh
- Chat appears disconnected

**Solutions:**

1. Check browser console (F12 → Console):
```javascript
// Look for errors like:
// "WebSocket connection failed"
// "Could not establish a socket connection"
```

2. Verify BASE_URL in .env matches your domain:
```bash
# If using http://localhost:8000
BASE_URL=http://localhost:8000

# If using https://questions.school.edu
BASE_URL=https://questions.school.edu
```

3. Check firewall allows WebSocket:
   - Ask IT department to allow port 8000
   - Or allow wss:// (secure WebSocket)

4. If behind Nginx proxy, verify WebSocket config:
```nginx
location /ws/ {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

5. Try different browser or incognito mode:
   - Disables browser extensions that might interfere
   - Clears browser cache

6. Check if your institution blocks WebSocket:
   - Some corporate/school networks block WebSocket
   - Workaround: Use different network (personal hotspot)

### Session Code Not Found

**Symptom:** "Session not found" error when joining.

**Causes:**
- Wrong session code
- Session ended
- Typo in code

**Solutions:**

1. Verify session code:
   - Copy/paste from instructor's URL (don't retype)
   - Check for extra spaces

2. Confirm session is still active:
   - Ask instructor if session is running
   - Check if session was ended

3. Try full URL instead of code:
   - If code isn't working, try full student URL
   - Example: `https://questions.school.edu/student?code=abc123`

4. Verify session code format:
   - Should be alphanumeric
   - Usually 20+ characters
   - Contains dashes or underscores

### Questions Not Appearing in Real-time

**Symptom:** Questions appear after refresh but not in real-time.

**Causes:**
- WebSocket disconnected
- Network latency
- Browser cache issues

**Solutions:**

1. Check WebSocket connection:
```javascript
// In browser console:
console.log(navigator.onLine)  // Should be true
```

2. Hard refresh to clear cache:
   - Windows/Linux: Ctrl+Shift+R
   - Mac: Cmd+Shift+R

3. Check internet connection:
   - Run speed test
   - Try on different network

4. Restart browser

5. Try different browser

### Can't Reach Application at All

**Symptom:** "Cannot reach server" or "Connection refused".

**Causes:**
- Application not running
- Wrong URL/port
- Firewall blocking

**Solutions:**

1. Verify application is running:
```bash
docker ps | grep raisemyhand  # Should show container running
```

2. Check it's actually listening:
```bash
curl http://localhost:8000  # Should get response
```

3. Verify correct URL:
   - Local: `http://localhost:8000`
   - Production: `https://questions.yourschool.edu`

4. Check if port is open:
```bash
# On server
netstat -tlnp | grep 8000
```

5. Check firewall:
```bash
# On Linux
sudo ufw status
```

## Authentication Issues

### "Invalid or Missing API Key"

**Symptom:** Getting error when trying to login as instructor.

**Causes:**
- Typo in API key
- Key doesn't exist
- Key is deactivated

**Solutions:**

1. Verify API key is correct:
   - Copy from password manager
   - Check for extra spaces
   - Verify capitalization

2. Check if key exists in Admin Panel:
   - Admin Panel → API Keys
   - Look for your key in the list

3. Check if key is active:
   - If marked "Inactive", contact admin to reactivate
   - Or create new key

4. Paste vs. type:
   - Always paste API keys, don't type them
   - Copy from `secrets/admin_password.txt` or wherever you saved it

### "Invalid Admin Credentials"

**Symptom:** Can't login to Admin Panel.

**Causes:**
- Wrong password
- Password not set
- Wrong username (should be "admin")

**Solutions:**

1. Check username: Should be `admin` (lowercase)

2. Verify password:
   - Check .env file for ADMIN_PASSWORD
   - Check `secrets/admin_password.txt`

3. For Docker:
```bash
cat secrets/admin_password.txt
```

4. If using .env:
```bash
grep ADMIN_PASSWORD .env
```

5. If password is blank or missing:
```bash
# Set password in .env
ADMIN_PASSWORD=YourSecurePassword123!

# Restart application
docker compose down
docker compose up -d
```

6. Try incognito/private window to clear cookies

## Content Moderation Issues

### Profanity Not Being Detected

**Symptom:** Profane questions appearing that should be flagged.

**Causes:**
- Profanity filter disabled
- Misspelled profanity
- Word not in dictionary

**Solutions:**

1. Verify filter is enabled:
   - Admin Panel → System Configuration
   - Check "Profanity Filter Enabled"

2. Check what's being flagged:
   - Submit test question: "What the hell?"
   - Should appear in "Flagged for Review" tab

3. Known limitations:
   - Misspellings not caught (e.g., "h3ll" without letters)
   - Some regional slang not recognized
   - Only English language

4. Restart filter:
```bash
docker compose restart
```

### Flagged Questions Not Showing in Tab

**Symptom:** Flagged count shows 0 but questions should be flagged.

**Causes:**
- Questions already approved/rejected
- Tab not loaded
- Browser cache

**Solutions:**

1. Hard refresh (Ctrl+Shift+R)

2. Clear browser cache:
   - F12 → Application → Clear Storage → Clear Site Data

3. Check "All Questions" tab:
   - Approved questions won't show in Flagged tab

4. Submit new test question to flag

5. Refresh page manually

6. If issue persists:
   - Check browser console for errors
   - Report to administrator with:
     - Session code
     - Question ID
     - Screenshot
     - Browser version

### Can't Approve/Reject Questions

**Symptom:** Buttons on flagged questions not responding or grayed out.

**Causes:**
- Button disabled (by design)
- JavaScript error
- Browser cache

**Solutions:**

1. Hard refresh page:
   - Ctrl+Shift+R (Windows/Linux)
   - Cmd+Shift+R (Mac)

2. Check browser console (F12 → Console):
   - Look for JavaScript errors
   - Red X icons indicate errors

3. Try different browser

4. Try incognito/private window

5. If buttons are grayed out (disabled):
   - This only happens for rejected questions
   - Click "Unflag" to re-enable other buttons

6. Clear browser cache:
   - F12 → Application → Storage → Clear Site Data

## Data Issues

### Can't Download Session Report

**Symptom:** Download button not working or file doesn't download.

**Causes:**
- Browser download blocked
- Pop-up blocker
- Large file timeout

**Solutions:**

1. Check download settings:
   - F12 → DevTools → Settings → Allow downloads
   - Browser may have blocked the download

2. Disable pop-up blocker for the site

3. Try different format:
   - If JSON fails, try CSV or vice versa
   - Some browsers handle formats differently

4. Try different browser

5. If file is very large:
   - Try on desktop instead of mobile
   - Use API endpoint instead: `/api/sessions/{code}/report`

### Lost Session Data

**Symptom:** Session disappeared or questions are gone.

**Causes:**
- Database deleted or lost
- Database corrupted
- Application crashed during save

**Solutions:**

1. Check if session exists:
   - Admin Panel → Sessions
   - Search by date/title

2. Try restarting:
   - Sometimes data is cached
   - Restart may recover it

3. Recover from backup:
   - Contact administrator
   - Use database backup from before data loss

4. If no backup:
   - Data cannot be recovered
   - Session is permanently lost

**Prevention:**
- Regular backups
- Use production database (PostgreSQL)
- Monitor disk space

## Display Issues

### QR Code Not Showing

**Symptom:** QR code modal doesn't appear or is blank.

**Causes:**
- Pop-up blocker
- JavaScript disabled
- QR library not loading

**Solutions:**

1. Disable pop-up blocker:
   - Allow pop-ups for your domain
   - Check browser settings

2. Enable JavaScript:
   - Chrome/Firefox/Edge: Should be on by default
   - Check Settings → Privacy & Security → JavaScript

3. Check browser console for errors:
   - F12 → Console
   - Look for red error messages

4. Try different browser

5. Use student URL directly instead:
   - Copy "Student URL" from dashboard
   - Share via link instead of QR

### Questions Look Weird/Garbled

**Symptom:** Question text appears as symbols or strange characters.

**Causes:**
- Encoding issue
- Markdown rendering problem
- Unicode characters

**Solutions:**

1. Hard refresh page:
   - Ctrl+Shift+R

2. Clear browser cache

3. Try different browser

4. Check browser console for errors:
   - May indicate markdown library not loading

5. Check if it's a markdown formatting issue:
   - Some characters used for formatting may display as symbols

## Performance Issues

### Page Loads Very Slowly

**Symptom:** Dashboard or student page takes 10+ seconds to load.

**Causes:**
- Slow internet
- Too many questions in session
- Server under heavy load
- Browser has too many tabs open

**Solutions:**

1. Check internet speed:
   - Run speedtest.net
   - Should be at least 5 Mbps

2. Close other browser tabs:
   - Each tab uses resources
   - Try with just 1 session open

3. Check if server is busy:
   - Open Admin Panel
   - Look at "Active Sessions" count
   - May need to upgrade server

4. Try different browser:
   - Sometimes extensions slow things down
   - Try incognito mode

5. Check server logs:
```bash
docker compose logs | tail -20
```

### Votes/Questions Update Slowly

**Symptom:** Changes take 5+ seconds to appear.

**Causes:**
- WebSocket connection is slow
- Server under heavy load
- Network latency

**Solutions:**

1. Check network (F12 → Network tab):
   - Look for slow WebSocket connection
   - May indicate network issue

2. Test from different location:
   - Corporate/school networks may throttle

3. Check server load:
```bash
docker stats
```

4. Restart application:
```bash
docker compose restart
```

## Mobile Issues

### Touch Targets Too Small (Mobile)

**Symptom:** Hard to tap buttons on phone.

**Solutions:**

1. Pinch to zoom in:
   - Zoom into 150% on mobile
   - Makes targets larger

2. Try landscape mode:
   - More space for buttons
   - Easier to tap

3. Increase system font size:
   - Device Settings → Display → Text Size

4. Use desktop instead for instructor view

### Page Not Responsive on Mobile

**Symptom:** Layout broken or hard to read on phone.

**Solutions:**

1. Rotate to landscape:
   - May render better

2. Zoom out then in:
   - Reset browser zoom
   - Let page re-render

3. Try different mobile browser

4. Check network connection:
   - Slow connection may not load responsive CSS

5. Try on different phone:
   - Some devices have rendering quirks

## Still Having Issues?

If your issue isn't listed:

1. **Check logs:**
```bash
docker compose logs --tail=50
```

2. **Check browser console:**
   - F12 → Console tab
   - Look for red error messages
   - Screenshot errors

3. **Report the issue with:**
   - What were you doing when it happened?
   - Error message (if any)
   - Browser and OS
   - Screenshot
   - Steps to reproduce
   - Server logs (if available)

4. **Where to report:**
   - Contact your system administrator
   - Open GitHub issue (include details above)
   - Include "Troubleshooting" tag in issue
