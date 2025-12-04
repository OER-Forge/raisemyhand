# Database Setup

## First Time Setup

When running the application for the first time, the database will be automatically initialized with all required tables.

### Option 1: Automatic Initialization (Recommended)

Just start the server:
```bash
python main.py
```

The database will be created automatically on startup.

### Option 2: Manual Initialization with Default API Key

If you want to create a default API key during initialization:
```bash
python init_database.py --create-key
```

This will:
1. Create all database tables (api_keys, sessions, questions)
2. Create a default admin API key if none exists
3. Display the API key for you to save

**Save the API key displayed - you won't see it again!**

## Verifying Database Setup

To verify the database is correctly set up:
```bash
python init_database.py
```

This will check that all tables exist with the correct schema.

## Database Schema

### api_keys
- `id`: Primary key
- `key`: Unique API key string (format: rmh_xxxxx)
- `name`: Human-readable name for the key
- `created_at`: Timestamp when key was created
- `last_used`: Timestamp when key was last used
- `is_active`: Boolean indicating if key is active

### sessions
- `id`: Primary key
- `session_code`: Unique code for students to join
- `instructor_code`: Unique code for instructor to manage session
- `title`: Session title
- `password_hash`: Optional bcrypt hash of session password
- `created_at`: Timestamp when session was created
- `ended_at`: Timestamp when session was ended (null if active)
- `is_active`: Boolean indicating if session is active

### questions
- `id`: Primary key
- `session_id`: Foreign key to sessions table
- `text`: Question text
- `upvotes`: Number of upvotes
- `is_answered`: Boolean indicating if question was answered
- `created_at`: Timestamp when question was submitted
- `answered_at`: Timestamp when question was marked as answered

## Migration Notes

The following migration scripts exist for legacy purposes but **are not needed** for fresh installations:

- `migrate_db.py` - Adds password_hash column (included in schema)
- `migrate_api_keys.py` - Creates api_keys table (included in schema)
- `migrate_questions.py` - Adds question columns (included in schema)
- `fix_question_data.py` - Fixes orphaned questions (shouldn't occur with proper schema)

These scripts are only needed if you're upgrading from an older version of the application.

## Resetting the Database

To start fresh:

```bash
# Backup first (if needed)
cp raisemyhand.db raisemyhand.db.backup

# Delete the database
rm raisemyhand.db

# Reinitialize with a new API key
python init_database.py --create-key
```

## Creating Additional API Keys

After the database is set up, you can create additional API keys through:

1. **Admin Web Interface** (Recommended)
   - Login at `/admin-login` (default: admin/changeme123)
   - Go to the "API Keys" section
   - Click "Create New API Key"

2. **Python Script**
   ```python
   from database import SessionLocal
   from models import APIKey
   
   db = SessionLocal()
   key = APIKey(
       key=APIKey.generate_key(),
       name="My Custom Key",
       is_active=True
   )
   db.add(key)
   db.commit()
   print(f"Created key: {key.key}")
   db.close()
   ```
