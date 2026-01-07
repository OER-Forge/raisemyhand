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

# Always run database initialization (safe - checks if tables exist)
echo "Initializing database..."
python init_db_v2.py 2>/dev/null || true

# Initialize demo data if requested
if [ "$CREATE_DEMO_DATA" = "true" ] || [ "$CREATE_DEMO_DATA" = "1" ]; then
    echo "Creating demo data..."
    python init_demo_data.py 2>/dev/null || true
fi

# Start the application
echo "Starting server..."
exec python main.py
