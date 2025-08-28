@echo off
echo ===============================================
echo  Ukraine Passport Checker - Build Executable
echo ===============================================

echo 🔍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

echo 📦 Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo 🔨 Building executable...
python build_exe.py
if errorlevel 1 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo ✅ Build completed successfully!
echo 📂 Executable created at: dist\UkrainePassportChecker.exe
echo 📦 Installer created at: dist\install.bat
echo.
echo You can now distribute the files in the 'dist' folder
pause
