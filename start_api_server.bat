@echo off
echo ======================================
echo Ukraine Passport Checker API Server
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is not available
    pause
    exit /b 1
)

echo ✅ pip found
echo.

REM Install requirements if needed
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

REM Check if config.json exists
if not exist "config.json" (
    echo ❌ config.json not found
    echo Please make sure config.json exists in this directory
    pause
    exit /b 1
)

echo ✅ Configuration found
echo.

echo 🚀 Starting API server...
echo 📱 Your mobile app should connect to: http://localhost:8000
echo 🛑 Press Ctrl+C to stop the server
echo.

python api_server.py

pause
