#!/bin/bash

# Phish-Guard Backend Startup Script
# Automatically sets up Python environment and runs the server

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛡️  Starting Phish-Guard Backend..."

# Force PIP_USER to false to override any config files causing the "Can not perform --user install" error
export PIP_USER=false

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed."
    exit 1
fi

# Clean up any broken venv
if [ -d "venv" ] && [ ! -f "venv/bin/activate" ]; then
    echo "🧹 Removing broken virtual environment..."
    rm -rf venv
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "⚠️  Warning: Virtual environment activation script not found."
fi

# Ensure pip is up to date (ignore errors)
echo "⬇️  Checking dependencies..."
python3 -m pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
if [ -f "backend/requirements.txt" ]; then
    python3 -m pip install -r backend/requirements.txt > /dev/null 2>&1
else
    python3 -m pip install fastapi uvicorn pandas scikit-learn python-multipart requests > /dev/null 2>&1
fi

# Check if installation worked
if ! python3 -c "import fastapi" > /dev/null 2>&1; then
    echo "⚠️  Virtual environment setup failed or dependencies missing."
    echo "🔄 Falling back to global System Python..."
    # Deactivate venv if active
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        deactivate
    fi
    
    # Verify global python has dependencies
    if ! python3 -c "import fastapi" > /dev/null 2>&1; then
        echo "❌ Error: 'fastapi' not found in global python either."
        echo "   Please run: pip3 install fastapi uvicorn pandas scikit-learn python-multipart requests"
        # Try to install globally as last resort
        echo "   Attempting global install..."
        pip3 install fastapi uvicorn pandas scikit-learn python-multipart requests
    fi
fi

# Kill any existing process on port 8000
echo "🔄 Stopping any existing backend process..."
lsof -ti tcp:8000 | xargs kill -9 2>/dev/null
sleep 1

# Start the backend
echo "🚀 Launching server..."
echo "📂 Working directory: $(pwd)/backend"
cd backend
python3 main.py
