@echo off
REM AI Resume Auto-Submission - Setup Script for Windows

echo.
echo ======================================
echo 🚀 AI Resume Auto-Submission - Setup
echo ======================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.9+ from python.org
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✓ %PYTHON_VERSION%

REM Check Node.js
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 16+ from nodejs.org
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✓ Node.js %NODE_VERSION%

echo.
echo Setting up Backend...

cd backend

REM Create virtual environment
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -q -r requirements.txt

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install chromium

echo ✓ Backend setup complete

cd ..

echo.
echo Setting up Frontend...

cd frontend

if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install -q
)

echo ✓ Frontend setup complete

cd ..

echo.
echo ======================================
echo ✅ Setup complete!
echo ======================================
echo.
echo 📝 Next steps:
echo.
echo 1️⃣  Start the backend (in command prompt 1):
echo    cd backend
echo    .venv\Scripts\activate.bat
echo    uvicorn main:app --reload --port 8001
echo.
echo 2️⃣  Start the frontend (in command prompt 2):
echo    cd frontend
echo    set VITE_BACKEND_URL=http://localhost:8001
echo    npm run dev
echo.
echo 3️⃣  Open http://localhost:5173 in your browser
echo.
echo 📖 Documentation:
echo    - README.md - Quick start and overview
echo    - TESTING.md - Testing guide
echo    - DEVELOPER.md - Architecture and development
echo.
echo ⚠️  Make sure both servers are running!
pause
