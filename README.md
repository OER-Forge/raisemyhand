# 🙋 RaiseMyHand

A real-time classroom question system where students submit questions anonymously, vote on what matters most, and see instructor responses instantly.

[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

Perfect for lectures, coding sessions, or any classroom where you want to encourage questions without putting students on the spot.

---

## ⚡ Quick Start

Choose your setup:

### 🎯 Demo Mode (Try it out)

Perfect for testing and demonstrations. Includes pre-loaded physics class data.

```bash
docker compose -f docker-compose.demo.yml up -d
```

**Access at:** http://localhost:8000
**Login:** `admin` / `demo123`
**Note:** Database resets on every container restart

---

### 🎓 Development Mode (Use in your class)

For actual classroom use with persistent data.

```bash
# 1. Create environment configuration
cp .env.example .env

# 2. Set admin password
mkdir -p secrets
echo "YourSecurePassword" > secrets/admin_password.txt

# 3. Start the application
docker compose -f docker-compose.dev.yml up -d
```

**Access at:** http://localhost:8001
**Login:** `admin` / (your password from secrets file)
**Note:** Data persists between sessions

---

## 📖 First Time Setup

### 1. Create an API Key

1. Visit http://localhost:8001/admin-login (or :8000 for demo)
2. Login with admin credentials
3. Click "API Keys" in the admin panel
4. Create a new API key for instructors

### 2. Start a Session

1. Go to the home page
2. Enter your API key and session title
3. Click "Create Session"
4. Share the QR code or URL with students

### 3. Students Join & Ask

- Students scan the QR code or visit the shared URL
- They submit questions anonymously
- Questions appear in real-time, sorted by votes
- You can answer, moderate, and manage questions from the instructor dashboard

---

## ✨ Key Features

- **Anonymous Questions** - Students ask without fear of judgment
- **Real-time Voting** - Most important questions rise to the top
- **Live Updates** - WebSocket connections keep everyone in sync
- **QR Code Access** - Students join instantly from phones
- **Content Moderation** - Automatic profanity filtering
- **Markdown Support** - Rich formatting for instructor answers
- **Presentation Mode** - Full-screen view for classroom displays
- **Data Export** - Download session reports as JSON or CSV

---

## 🔧 Advanced Setup

### Run Both Demo and Dev Simultaneously

```bash
# Start demo on :8000
docker compose -f docker-compose.demo.yml up -d

# Start dev on :8001
docker compose -f docker-compose.dev.yml up -d
```

### Auto-Reset Demo Every 24 Hours

For public demos, automatically reset to fresh data:

```bash
# Set up cron job
chmod +x scripts/reset-demo.sh
crontab -e

# Add this line (resets daily at 3 AM):
0 3 * * * /path/to/raisemyhand/scripts/reset-demo.sh
```

See [scripts/setup-demo-cron.md](scripts/setup-demo-cron.md) for detailed instructions.

### Use Different Demo Contexts

Choose from pre-loaded demo data:

```bash
# Physics (default)
docker compose -f docker-compose.demo.yml up -d

# Biology
DEMO_CONTEXT=biology_200 docker compose -f docker-compose.demo.yml up -d

# Computer Science
DEMO_CONTEXT=computer_science_101 docker compose -f docker-compose.demo.yml up -d
```

Available contexts: `physics_101`, `biology_200`, `chemistry_110`, `calculus_150`, `computer_science_101`

---

## 📚 Documentation

- **[Full Documentation](docs/README.md)** - Complete feature guide
- **[Instructor Guide](docs/INSTRUCTOR_GUIDE.md)** - Step-by-step classroom workflow
- **[Student Guide](docs/STUDENT_GUIDE.md)** - How students use the system
- **[Admin Guide](docs/ADMIN_GUIDE.md)** - User and API key management
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production setup with Nginx
- **[API Documentation](docs/API.md)** - REST API reference
- **[FAQ](docs/FAQ.md)** - Common questions and troubleshooting

---

## 🛠️ Local Development (Without Docker)

```bash
# Clone and setup
git clone <your-repo-url>
cd raisemyhand
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and set ADMIN_PASSWORD

# Run
python main.py
```

Access at http://localhost:8000

---

## 🏗️ Tech Stack

- **Backend:** FastAPI, SQLAlchemy, WebSockets, SQLite (PostgreSQL-ready)
- **Frontend:** Vanilla JavaScript, CSS, EasyMDE markdown editor
- **Security:** JWT auth, bcrypt passwords, CSRF protection, rate limiting
- **Deployment:** Docker, Docker Compose, Nginx-ready

---

## 🎯 Use Cases

- **Physics/Math:** Students ask conceptual questions during problem-solving
- **Computer Science:** Debugging help and code clarification in real-time
- **Large Lectures:** Collect questions from hundreds of students simultaneously
- **Remote Teaching:** Works great for hybrid and online classes

---

## 📊 System Requirements

- Docker 20.10+ and Docker Compose 2.0+
- OR Python 3.11+
- 1GB RAM minimum (2GB recommended)
- Modern web browser with WebSocket support

---

## 🤝 Contributing

This is educational software built for classroom use. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🆘 Getting Help

- **Issues:** Report bugs and request features via GitHub Issues
- **Troubleshooting:** Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Questions:** See [docs/FAQ.md](docs/FAQ.md)

---

<div align="center">

**Built for education with ❤️**

[Documentation](docs/) • [Report Issue](../../issues) • [View Demo](#)

</div>
