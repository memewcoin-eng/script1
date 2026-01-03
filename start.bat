@echo off
REM Remote Camera System - Windows Start Script

echo 🚀 Remote Camera System - Quick Start
echo ====================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 🐍 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Set environment variables
set PORT=5000
set PYTHONUNBUFFERED=1

REM Create logs directory
if not exist "logs" mkdir logs

echo 🌐 Starting Remote Camera System...
echo 📱 Access URL: http://localhost:5000
echo 👤 Admin Panel: http://localhost:5000
echo ====================================

REM Start the application
python app.py

pause
