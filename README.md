# RaiseMyHand - Student Question Aggregator

A real-time web-based tool for collecting, organizing, and managing student questions during live classes. Built for physics and computational science education.

## Features

- **Anonymous Question Submission**: Students can ask questions without revealing their identity
- **Reddit-style Upvoting**: Popular questions rise to the top, helping instructors prioritize
- **Real-time Updates**: Questions and votes appear instantly via WebSocket connections
- **QR Code Access**: Students can join sessions by scanning a QR code
- **Session Management**: Start and end Q&A sessions with unique URLs
- **Export Reports**: Download session data in JSON or CSV format
- **No Authentication Required**: Accessible via unique session codes, no login needed
- **Docker-ready**: Launch with a single command

## Quick Start

### For Individual Instructors (Run on Your Laptop)

```bash
# Clone and setup
git clone <your-repo-url>
cd raisemyhand
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the server
python main.py
```

Open [http://localhost:8000](http://localhost:8000) and start your session!

### For Departments/Colleges (Shared Server)

**Using Docker (Recommended):**
```bash
cd raisemyhand
docker-compose up -d
```

Server available at `http://your-server:8000`

**See [DEPLOYMENT.md](DEPLOYMENT.md) for:**
- Production deployment guides
- Cloud hosting options (AWS, Heroku, DigitalOcean)
- nginx + SSL configuration
- Scaling and backup strategies

## Usage Guide

### For Instructors

1. **Create a Session**:
   - Go to the home page
   - Enter a title for your session (e.g., "Quantum Mechanics - Week 5")
   - Click "Create Session"

2. **Share with Students**:
   - You'll be redirected to the instructor dashboard
   - Share the student URL with your class
   - OR click "Show QR Code" and display it on screen for students to scan

3. **Monitor Questions**:
   - Questions appear in real-time as students submit them
   - Questions are sorted by upvotes (most popular at the top)
   - Mark questions as "Answered" when you address them

4. **End the Session**:
   - Click "End Session" when finished
   - Students can no longer submit new questions
   - Download a report of all questions and statistics

### For Students

1. **Join a Session**:
   - Visit the URL shared by your instructor
   - OR scan the QR code displayed in class

2. **Submit Questions**:
   - Type your question in the text box
   - Click "Submit Question"
   - Your question appears immediately for everyone

3. **Upvote Questions**:
   - Click the upvote button on questions you're interested in
   - You can only upvote each question once
   - Popular questions rise to the top

## Architecture

### Backend (FastAPI)

- **FastAPI**: Modern, fast web framework with automatic API documentation
- **SQLAlchemy**: Database ORM for managing sessions and questions
- **SQLite**: Lightweight database (easily swappable for PostgreSQL)
- **WebSockets**: Real-time bidirectional communication
- **Pydantic**: Data validation and serialization

### Frontend

- **Vanilla JavaScript**: No framework dependencies, easy to understand and modify
- **WebSocket Client**: Real-time updates without polling
- **Responsive CSS**: Works on desktop, tablet, and mobile

### Database Schema

**Sessions Table**:
- `id`: Primary key
- `session_code`: Unique code for students to join
- `instructor_code`: Unique code for instructor access
- `title`: Session title
- `created_at`: Timestamp
- `ended_at`: Timestamp (nullable)
- `is_active`: Boolean

**Questions Table**:
- `id`: Primary key
- `session_id`: Foreign key to sessions
- `text`: Question content
- `upvotes`: Vote count
- `is_answered`: Boolean
- `created_at`: Timestamp
- `answered_at`: Timestamp (nullable)

## API Documentation

Once running, visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

### Key Endpoints

**Session Management**:
- `POST /api/sessions` - Create a new session
- `GET /api/sessions/{session_code}` - Get session details
- `POST /api/sessions/{instructor_code}/end` - End a session
- `GET /api/sessions/{instructor_code}/report` - Download session report

**Question Management**:
- `POST /api/sessions/{session_code}/questions` - Submit a question
- `POST /api/questions/{question_id}/upvote` - Upvote a question
- `POST /api/questions/{question_id}/answer` - Mark as answered (instructor only)

**Real-time**:
- `WS /ws/{session_code}` - WebSocket connection for live updates

## Configuration

Environment variables (see [.env.example](.env.example)):

- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)
- `DATABASE_URL`: Database connection string (default: `sqlite:///./raisemyhand.db`)
- `BASE_URL`: External URL for QR codes and links (default: `http://localhost:8000`)
- `TIMEZONE`: IANA timezone for timestamp display (default: `UTC`)

For detailed URL and timezone configuration, see [URL_CONFIGURATION.md](URL_CONFIGURATION.md).

## Extending RaiseMyHand

### Adding Features

The codebase is designed to be easily extensible:

1. **Database Models**: Add fields to [models.py](models.py)
2. **API Schemas**: Update [schemas.py](schemas.py) for validation
3. **Endpoints**: Add routes in [main.py](main.py)
4. **Frontend**: Modify HTML/CSS/JS in [templates/](templates/) and [static/](static/)

### Switching to PostgreSQL

1. Update `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost/raisemyhand
```

2. Install PostgreSQL driver:
```bash
pip install psycopg2-binary
```

3. The code will work without changes!

### Adding Authentication

To add user authentication:

1. Install `fastapi-users` or similar auth library
2. Add user models and authentication middleware
3. Update endpoints to require authentication
4. Modify frontend to include login flow

## Development

### Project Structure

```
raisemyhand/
├── main.py              # FastAPI application and routes
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic validation schemas
├── database.py          # Database configuration
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose configuration
├── static/
│   ├── css/
│   │   └── styles.css   # Application styles
│   └── js/
│       ├── instructor.js # Instructor dashboard logic
│       └── student.js    # Student interface logic
└── templates/
    ├── index.html        # Home page
    ├── instructor.html   # Instructor dashboard
    └── student.html      # Student interface
```

### Testing Locally

1. Install dependencies: `pip install -r requirements.txt`
2. Run the server: `python main.py`
3. Open multiple browser tabs to simulate instructor and students
4. Test real-time updates by submitting questions and upvoting

### Contributing

This is an open-source educational tool. Contributions are welcome! Consider:

- Bug fixes and improvements
- Additional export formats (PDF, Excel)
- Analytics and visualizations
- Mobile app integration
- Internationalization (i18n)
- Accessibility improvements

## License

MIT License - See LICENSE file for details

## Credits

Built for physics and computational science education by educators, for educators.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
