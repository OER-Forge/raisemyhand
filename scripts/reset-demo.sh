#!/bin/bash
# Reset Demo Environment Script
# This script resets the demo environment to fresh demo data
# Can be run manually or scheduled via cron for automatic daily resets

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔄 Resetting RaiseMyHand Demo Environment..."
echo "📁 Project directory: $PROJECT_DIR"
echo ""

cd "$PROJECT_DIR"

# Check if demo container is running
if docker ps --format '{{.Names}}' | grep -q '^raisemyhand-demo$'; then
    echo "🛑 Stopping demo container..."
    docker compose -f docker-compose.demo.yml down
    echo "✅ Container stopped"
else
    echo "ℹ️  Demo container is not running"
fi

# Remove the demo data volume to force a fresh start
echo "🗑️  Removing demo data volume..."
docker volume rm raisemyhand_demo-data 2>/dev/null || echo "ℹ️  Volume not found (already clean)"

# Start the demo environment (will auto-load fresh data)
echo ""
echo "🚀 Starting demo environment with fresh data..."
docker compose -f docker-compose.demo.yml up -d

# Wait for container to be healthy
echo ""
echo "⏳ Waiting for demo environment to be ready..."
sleep 5

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q '^raisemyhand-demo$'; then
    echo ""
    echo "✅ Demo environment reset complete!"
    echo "📍 Access at: http://localhost:8000"
    echo "🔑 Login: admin / demo123"
    echo ""
    echo "📊 Demo Context: ${DEMO_CONTEXT:-physics_101}"
else
    echo ""
    echo "❌ Error: Demo container failed to start"
    echo "Run 'docker compose -f docker-compose.demo.yml logs' for details"
    exit 1
fi
