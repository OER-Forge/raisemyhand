#!/bin/bash
# Docker entrypoint script for RaiseMyHand
# This ensures the database is initialized and optionally creates a default API key

set -e

echo "Starting RaiseMyHand..."

# Load admin password from Docker secret if available
if [ -f "/run/secrets/admin_password" ]; then
    export ADMIN_PASSWORD=$(cat /run/secrets/admin_password)
    echo "Loaded admin password from Docker secret"
fi

# Always run migrations first (safe - they check if needed)
echo "Running database migrations..."
python migrate_db.py 2>/dev/null || true
python migrate_api_keys.py 2>/dev/null || true
python migrate_questions.py 2>/dev/null || true
python migrate_question_numbers.py 2>/dev/null || true

# Check if we should create a default API key
if [ "$CREATE_DEFAULT_API_KEY" = "true" ] || [ "$CREATE_DEFAULT_API_KEY" = "1" ]; then
    echo "Checking for API keys..."
    python init_database.py --create-key
fi

# Start the application
echo "Starting server..."
exec python main.py
