#!/bin/bash

echo "🚀 Starting Personal Finance Tracker (Development Mode)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "⚠️  Note: For full functionality, you need PostgreSQL and Redis running."
echo "   You can use Docker for these services:"
echo "   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=finance_tracker postgres:15-alpine"
echo "   docker run -d -p 6379:6379 redis:7-alpine"
echo ""
echo "   Or use SQLite (limited functionality) by updating DATABASE_URL in .env:"
echo "   DATABASE_URL=sqlite+aiosqlite:///./finance_tracker.db"
echo ""

# Start FastAPI server
echo "🌟 Starting FastAPI server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
