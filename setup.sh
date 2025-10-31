#!/bin/bash

# AI Resume Auto-Submission - Quick Setup Script
# Run this script to set up and start the application

set -e

echo "🚀 AI Resume Auto-Submission - Setup"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION}${NC}"

# Check Node.js
echo -e "${BLUE}Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js ${NODE_VERSION}${NC}"

echo ""
echo -e "${BLUE}Setting up Backend...${NC}"

# Backend setup
cd backend

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

echo -e "${GREEN}✓ Backend setup complete${NC}"

cd ..

echo ""
echo -e "${BLUE}Setting up Frontend...${NC}"

# Frontend setup
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install -q
fi

echo -e "${GREEN}✓ Frontend setup complete${NC}"

cd ..

echo ""
echo "===================================="
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "===================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "1️⃣  Start the backend (in terminal 1):"
echo "   cd backend"
echo "   source .venv/bin/activate"
echo "   uvicorn main:app --reload --port 8001"
echo ""
echo "2️⃣  Start the frontend (in terminal 2):"
echo "   cd frontend"
echo "   VITE_BACKEND_URL=http://localhost:8001 npm run dev"
echo ""
echo "3️⃣  Open http://localhost:5173 in your browser"
echo ""
echo "📖 Documentation:"
echo "   - README.md - Quick start and overview"
echo "   - TESTING.md - Testing guide"
echo "   - DEVELOPER.md - Architecture and development"
echo ""
echo -e "${YELLOW}⚠️  Make sure both servers are running!${NC}"
