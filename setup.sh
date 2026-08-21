#!/bin/bash
# ==========================================
# Ghost QA Production Setup Script
# ==========================================
# Run this after filling in .env with real credentials

set -e

echo "=== Ghost QA Production Setup ==="

# 1. Install dependencies
echo "1. Installing dependencies..."
pip install -r requirements.txt
pip install psycopg2-binary  # PostgreSQL driver

# 2. PostgreSQL setup (skip if using SQLite)
if command -v psql &> /dev/null; then
    echo "2. PostgreSQL detected. Setting up database..."
    # Requires sudo/root access
    sudo -u postgres psql -c "CREATE USER ghost_qa WITH PASSWORD 'ghost_qa_pass';" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE ghost_qa OWNER ghost_qa;" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ghost_qa TO ghost_qa;" 2>/dev/null || true
fi

# 3. Initialize database
echo "3. Initializing database..."
python3 -c "from app.database import init_db; init_db(); print('Database initialized.')"

# 4. Verify configuration
echo "4. Verifying configuration..."
DEMO_MODE=$(python3 -c "from app.config import settings; print(settings.DEMO_MODE)")
echo "   DEMO_MODE: $DEMO_MODE"

if [ "$DEMO_MODE" = "True" ]; then
    echo "   WARNING: Running in DEMO_MODE. Set DEMO_MODE=false and provide real credentials."
else
    echo "   Production mode active."
fi

echo ""
echo "=== Setup Complete ==="
echo "Start server: DEMO_MODE=false python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "Dashboard: http://localhost:8000/dashboard"
echo "API Docs: http://localhost:8000/docs"
