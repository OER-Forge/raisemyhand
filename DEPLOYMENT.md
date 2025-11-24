# RaiseMyHand Deployment Guide

This guide covers deployment options for both individual instructors and institutional use.

## Deployment Scenarios

### 🧑‍🏫 Scenario 1: Individual Instructor (Personal Laptop)

**Perfect for:** Running during a single class, no permanent hosting needed.

**Setup:**
```bash
# Clone the repository
git clone <your-repo-url>
cd raisemyhand

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database with a default API key (optional but recommended)
python init_database.py --create-key

# Run the server
python main.py
```

**Access:**
- Open browser to `http://localhost:8000`
- Login to admin panel: `http://localhost:8000/admin-login` (default: admin/changeme123)
- Create or use the generated API key to create sessions
- Sessions persist in local `raisemyhand.db` file

**Note:** Save the API key displayed during initialization - you'll need it to create sessions!

**Network Access (Optional):**
To let students connect from their devices:
```bash
# Find your local IP (macOS/Linux)
ifconfig | grep "inet " | grep -v 127.0.0.1

# Run server on local network
HOST=0.0.0.0 python main.py
```
Students connect to: `http://YOUR_LOCAL_IP:8000`

---

### 🏫 Scenario 2: Department/College Server (Shared Hosting)

**Perfect for:** Multiple instructors across department, persistent hosting.

#### Option A: Docker Deployment (Recommended)

**1. Install Docker:**
- Follow instructions at https://docs.docker.com/get-docker/

**2. Configure:**
Edit `docker-compose.yml`:
```yaml
environment:
  - BASE_URL=http://your-server-address:8000  # Change to your actual URL
  - CREATE_DEFAULT_API_KEY=true  # Creates a default key on first run
  - ADMIN_USERNAME=admin  # Change for production!
  - ADMIN_PASSWORD=changeme123  # Change for production!
```

**3. Deploy:**
```bash
cd raisemyhand
docker-compose up -d
```

**4. Get the default API key:**
```bash
# View container logs to see the generated API key
docker-compose logs raisemyhand | grep "Key:"
```

**5. Access:**
- Navigate to `http://your-server-address:8000`
- Login to admin panel: `http://your-server-address:8000/admin-login`
- Use the API key from logs or create new ones in the admin panel
- Distribute API keys to instructors for creating sessions

**Advantages:**
- Automatic restarts
- Database persists in Docker volume
- Easy updates (`docker-compose pull && docker-compose up -d`)
- Isolated from system Python
- Default API key created automatically

**Configuration:**
Edit `docker-compose.yml` to change port:
```yaml
ports:
  - "80:8000"  # Use port 80 for production
```

#### Option B: Systemd Service (Linux Server)

**1. Create service file:** `/etc/systemd/system/raisemyhand.service`
```ini
[Unit]
Description=RaiseMyHand Student Q&A System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/raisemyhand
Environment="PATH=/opt/raisemyhand/venv/bin"
ExecStart=/opt/raisemyhand/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**2. Enable and start:**
```bash
sudo systemctl enable raisemyhand
sudo systemctl start raisemyhand
```

#### Option C: Cloud Deployment

##### Heroku
```bash
# Add Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

##### DigitalOcean App Platform
1. Connect GitHub repository
2. Select Python as runtime
3. Set run command: `uvicorn main:app --host 0.0.0.0 --port 8000`

##### AWS EC2 / Azure VM
- Use Docker deployment method above
- Set up reverse proxy with nginx (see below)

---

## Production Recommendations

### 1. Use a Reverse Proxy (nginx)

**Why:** Better performance, SSL/TLS support, static file caching

**nginx configuration:**
```nginx
server {
    listen 80;
    server_name raisemyhand.yourschool.edu;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /opt/raisemyhand/static/;
        expires 7d;
    }
}
```

### 2. Enable HTTPS

**Using Let's Encrypt (free):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d raisemyhand.yourschool.edu
```

### 3. Database Considerations

**SQLite (Current - Recommended for most cases):**
- ✅ Zero configuration
- ✅ Perfect for <100 concurrent users
- ✅ Simple backups (`cp raisemyhand.db backup/`)
- ⚠️ Single server only (no clustering)

**PostgreSQL (For high-traffic institutions):**
```bash
# Install PostgreSQL
sudo apt install postgresql

# Update .env
DATABASE_URL=postgresql://user:password@localhost/raisemyhand

# Install driver
pip install psycopg2-binary
```

**When to upgrade:**
- More than 50 concurrent sessions
- Multiple servers needed
- Advanced analytics required

### 4. Monitoring

**Check server health:**
```bash
curl http://localhost:8000/api/health
```

**View logs (Docker):**
```bash
docker-compose logs -f
```

**View logs (systemd):**
```bash
sudo journalctl -u raisemyhand -f
```

---

## Multi-Tenancy Options

### Current Design (Recommended for Most)
- **No user accounts needed**
- Each instructor creates sessions on-demand
- Session codes provide access control
- All instructors share one deployment

**Advantages:**
- Zero friction for instructors
- No IT support needed
- Works like Google Meet/Zoom links

**Access Control:**
- Only person with `instructor_code` can manage session
- Only person with `session_code` can join
- Codes are cryptographically random (8 chars = 2.8 trillion possibilities)

### Optional: Add Instructor Authentication

**If your institution requires user accounts:**

See `AUTHENTICATION.md` (future feature) for adding:
- SSO/SAML integration
- LDAP/Active Directory
- Simple username/password
- Session ownership tracking

**Note:** Most educational institutions prefer the current "no-login" approach for ease of use.

---

## Backup Strategy

### Automated Backups (Cron)

```bash
# Add to crontab (crontab -e)
0 2 * * * cp /opt/raisemyhand/raisemyhand.db /backup/raisemyhand-$(date +\%Y\%m\%d).db
```

### Docker Volume Backup
```bash
# Backup
docker run --rm -v raisemyhand_raisemyhand-data:/data -v $(pwd):/backup alpine tar czf /backup/raisemyhand-backup.tar.gz /data

# Restore
docker run --rm -v raisemyhand_raisemyhand-data:/data -v $(pwd):/backup alpine tar xzf /backup/raisemyhand-backup.tar.gz -C /
```

---

## Scaling Considerations

### Current Capacity
- **SQLite + Single Server:** 50+ concurrent sessions
- **WebSocket connections:** 1000+ students
- **Request handling:** Thousands of questions per session

### When to Scale Up
- Implement load balancer
- Use PostgreSQL with connection pooling
- Add Redis for WebSocket pub/sub
- Deploy multiple app servers

Most institutions won't need this - a single $5/month DigitalOcean droplet handles 100+ concurrent sessions.

---

## Security Considerations

### Already Implemented ✅
- Random cryptographic session codes
- XSS prevention (HTML escaping)
- CORS headers
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

### Recommended for Production
- Enable HTTPS (Let's Encrypt)
- Set up firewall (allow only 80/443)
- Regular updates (`git pull && docker-compose up -d`)
- Rate limiting (nginx: `limit_req_zone`)

### Not Needed for Most Cases
- User authentication (sessions self-secure via codes)
- Session passwords (codes are sufficient)
- API keys (public service within institution)

---

## Cost Estimates

### Self-Hosted (One-time setup)
- **Laptop:** $0 (use existing hardware)
- **Department server:** $0 (use existing infrastructure)
- **DigitalOcean Droplet:** $5-10/month
- **AWS EC2 t3.micro:** $8-10/month

### Managed Hosting
- **Heroku:** $7/month (Hobby tier)
- **DigitalOcean App Platform:** $5/month
- **AWS Lightsail:** $3.50/month

**Recommendation:** Start with laptop for testing, then DigitalOcean droplet with Docker for institutional deployment.

---

## Support Matrix

| Deployment | Best For | Complexity | Cost |
|------------|----------|------------|------|
| Laptop | Single class, testing | ⭐ Easy | $0 |
| Docker | Department/college | ⭐⭐ Medium | $5/mo |
| Cloud (Heroku) | Quick deploy | ⭐ Easy | $7/mo |
| Cloud (DO/AWS) | Full control | ⭐⭐⭐ Advanced | $5/mo |
| Systemd | Linux admins | ⭐⭐⭐ Advanced | $0-5/mo |

---

## Quick Start by Role

**👨‍💻 IT Administrator:**
1. Use Docker deployment
2. Set up nginx reverse proxy
3. Enable Let's Encrypt SSL
4. Configure automated backups

**🧑‍🏫 Individual Instructor:**
1. Install Python + dependencies
2. Run `python main.py`
3. Share link with students
4. Done!

**🏫 Department Chair:**
- Request IT to deploy using Docker method
- Share server URL with faculty
- No training needed - intuitive interface
