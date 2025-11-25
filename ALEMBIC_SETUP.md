# Alembic Migration Setup (Optional)

This guide explains how to set up Alembic for professional database migration management.

## Status

**Phase 2B (Optional)** - Alembic has been added to `requirements.txt` but not yet configured. This is **not required** for the application to run - it's a professional enhancement for managing future database schema changes.

---

## Why Alembic?

Currently, your database schema is managed by:
- `models.py` - Current schema definition
- `init_database.py` - Creates fresh databases
- `deprecated/migrations/` - Old one-time migration scripts

**Alembic provides:**
- ✅ Version control for database schema
- ✅ Automatic migration generation
- ✅ Rollback capability
- ✅ Team collaboration support
- ✅ Production-ready migration management

---

## Installation

After recreating your virtual environment with the updated `requirements.txt`:

```bash
# Verify Alembic is installed
python -c "import alembic; print(alembic.__version__)"
```

---

## Setup Steps

### 1. Initialize Alembic

```bash
# Initialize Alembic in your project
alembic init alembic
```

This creates:
```
alembic/
├── env.py              # Alembic environment configuration
├── script.py.mako      # Migration template
├── versions/           # Migration scripts go here
└── README              # Alembic documentation
alembic.ini            # Alembic configuration file
```

### 2. Configure Alembic

Edit `alembic/env.py` to connect to your database:

```python
# Near the top of the file, add:
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base
from models import Session, Question, APIKey  # Import all models

# Find the line: target_metadata = None
# Replace with:
target_metadata = Base.metadata
```

Edit `alembic.ini`:

```ini
# Find the line: sqlalchemy.url = driver://user:pass@localhost/dbname
# Replace with:
sqlalchemy.url = sqlite:///./data/raisemyhand.db
```

### 3. Create Initial Migration

This captures your current database schema:

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Review the generated migration in alembic/versions/
# It should show all your tables (sessions, questions, api_keys)
```

### 4. Mark Current Database as Up-to-Date

Since your database already has the current schema, mark it as migrated:

```bash
# Stamp the database as being at the current revision
alembic stamp head
```

---

## Daily Usage

### Creating New Migrations

When you change your database models:

1. **Edit** `models.py` with your changes
2. **Generate migration** automatically:
   ```bash
   alembic revision --autogenerate -m "Description of change"
   ```
3. **Review** the generated migration in `alembic/versions/`
4. **Apply** the migration:
   ```bash
   alembic upgrade head
   ```

### Example Workflow

Let's say you want to add a `description` field to sessions:

```python
# In models.py, add to Session class:
description = Column(String, nullable=True)
```

```bash
# Generate migration
alembic revision --autogenerate -m "Add description to sessions"

# Review the migration file
cat alembic/versions/XXXX_add_description_to_sessions.py

# Apply migration
alembic upgrade head

# If something goes wrong, rollback
alembic downgrade -1
```

---

## Common Commands

```bash
# Check current revision
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Upgrade one step
alembic upgrade +1

# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Show pending migrations
alembic show head
```

---

## Migration Best Practices

1. **Always review** auto-generated migrations before applying
2. **Test migrations** on a copy of your database first
3. **Backup database** before running migrations in production
4. **Never edit** applied migrations - create new ones
5. **Commit migrations** to version control with your code
6. **Document** complex migrations with comments

---

## Converting Old Migrations (Optional)

Your old migration scripts in `deprecated/migrations/` have already been applied. You don't need to convert them to Alembic format since:

1. The current schema in `models.py` includes all those changes
2. Your database already has the current schema
3. `alembic stamp head` marks your database as up-to-date

However, for historical reference, here's what each old migration did:

| Old Script | What It Did | Now In models.py |
|------------|-------------|------------------|
| `migrate_db.py` | Added `password_hash` to sessions | ✅ Line 23 |
| `migrate_api_keys.py` | Created `api_keys` table | ✅ Lines 43-52 |
| `migrate_question_numbers.py` | Added `question_number` to questions | ✅ Line 32 |
| `migrate_questions.py` | Added fields to questions | ✅ Lines 31-34 |

---

## Troubleshooting

### "Target database is not up to date"

```bash
# Check current state
alembic current

# If no revision, stamp as current
alembic stamp head
```

### "Can't locate revision identified by"

```bash
# The alembic_version table might be out of sync
# Check what revision is in the database
sqlite3 data/raisemyhand.db "SELECT * FROM alembic_version;"

# If needed, manually update
sqlite3 data/raisemyhand.db "UPDATE alembic_version SET version_num='<correct_version>';"

# Or drop and re-stamp
sqlite3 data/raisemyhand.db "DROP TABLE alembic_version;"
alembic stamp head
```

### "Table already exists"

This means Alembic is trying to create a table that exists. Solutions:

1. **If starting fresh:** Your database is newer than migrations
   ```bash
   alembic stamp head
   ```

2. **If mid-migration:** Skip the problematic migration
   ```bash
   # Manually mark as applied
   alembic stamp <next_revision>
   ```

---

## Docker Usage

To use Alembic in Docker:

### Add to Dockerfile

```dockerfile
# Alembic is already in requirements.txt, just copy config
COPY alembic.ini .
COPY alembic ./alembic
```

### Update docker-entrypoint.sh

```bash
#!/bin/bash

# Run migrations before starting server
alembic upgrade head

# Start application
exec python main.py
```

This ensures migrations run automatically on container startup.

---

## When NOT to Use Alembic

Skip Alembic if:
- You're a single developer with simple database needs
- You rebuild your database from scratch during development
- Your application is still in early prototype stage
- You prefer manual SQL migrations

The current setup (`init_database.py` + `models.py`) works fine for these cases.

---

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [SQLAlchemy Migration Guide](https://docs.sqlalchemy.org/en/14/core/metadata.html#altering-database-objects-through-migrations)

---

## Summary

**Alembic is optional but recommended if:**
- You're deploying to production
- Multiple developers are working on the database
- You need rollback capability
- You want professional database change management

**Current status:**
- ✅ Alembic added to `requirements.txt`
- ⏳ Configuration files not yet created (follow setup steps above)
- ✅ Database schema is current and complete
- ✅ Old migrations archived in `deprecated/migrations/`

**Next steps (when ready):**
1. Follow "Setup Steps" above
2. Run `alembic stamp head` to mark database as current
3. Use Alembic for future schema changes
