"""
Build script to create executable files for Ukraine Passport Checker
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed successfully")

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"🧹 Cleaned {dir_name} directory")
            except PermissionError:
                print(f"⚠️ Could not clean {dir_name} (files may be in use)")
                # Try to continue anyway
                continue
            except Exception as e:
                print(f"⚠️ Error cleaning {dir_name}: {e}")
                continue

def create_spec_file():
    """Create PyInstaller spec file for GUI application"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('default.json', '.'),
        ('config.example.json', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'requests',
        'requests.adapters',
        'requests.packages',
        'requests.packages.urllib3',
        'requests.packages.urllib3.util',
        'requests.packages.urllib3.util.retry',
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common',
        'selenium.webdriver.common.by',
        'selenium.webdriver.common.keys',
        'selenium.webdriver.support',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.webdriver.support.wait',
        'undetected_chromedriver',
        'undetected_chromedriver.v2',
        'undetected_chromedriver.patcher',
        'undetected_chromedriver.options',
        'undetected_chromedriver.webelement',
        'beautifulsoup4',
        'bs4',
        'bs4.builder',
        'bs4.builder.html',
        'bs4.builder._html5lib',
        'bs4.builder._lxml',
        'flask',
        'flask_cors',
        'smtplib',
        'email',
        'email.mime',
        'email.mime.text',
        'email.mime.multipart',
        'email.mime.base',
        'threading',
        'json',
        'logging',
        'logging.handlers',
        'datetime',
        'time',
        'os',
        'sys',
        'subprocess',
        'webbrowser',
        'pathlib',
        'urllib',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        'http',
        'http.client',
        'ssl',
        'socket',
        'zipfile',
        'tempfile',
        'shutil',
        'platform',
        'psutil',
        'websockets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='UkrainePassportChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)'''
    
    with open('gui_app.spec', 'w') as f:
        f.write(spec_content.strip())
    print("📝 Created PyInstaller spec file")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    try:
        # Use more comprehensive PyInstaller command
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--add-data", "default.json;.",
            "--add-data", "config.example.json;.",
            "--hidden-import", "undetected_chromedriver",
            "--hidden-import", "undetected_chromedriver.v2",
            "--hidden-import", "undetected_chromedriver.patcher",
            "--hidden-import", "selenium.webdriver.chrome.service",
            "--hidden-import", "selenium.webdriver.chrome.options",
            "--hidden-import", "selenium.webdriver.common.by",
            "--hidden-import", "selenium.webdriver.support.ui",
            "--hidden-import", "selenium.webdriver.support.expected_conditions",
            "--hidden-import", "requests",
            "--hidden-import", "beautifulsoup4",
            "--hidden-import", "bs4",
            "--hidden-import", "flask",
            "--hidden-import", "flask_cors",
            "--hidden-import", "smtplib",
            "--hidden-import", "email.mime.text",
            "--hidden-import", "email.mime.multipart",
            "--collect-all", "undetected_chromedriver",
            "--collect-all", "selenium",
            "--name", "UkrainePassportChecker",
            "gui_app.py"
        ]
        
        print("Running PyInstaller with command:")
        print(" ".join(cmd))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Executable built successfully!")
            exe_path = os.path.join("dist", "UkrainePassportChecker.exe")
            if os.path.exists(exe_path):
                print(f"📂 Executable location: {os.path.abspath(exe_path)}")
                return True
            else:
                print("❌ Executable file not found after build!")
                return False
        else:
            print("❌ Build failed!")
            print("STDOUT:")
            print(result.stdout)
            print("\nSTDERR:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error building executable: {e}")
        return False

def create_installer_script():
    """Create a simple installer script"""
    installer_content = '''@echo off
echo ===============================================
echo  Ukraine Passport Checker - Installer
echo ===============================================
echo.

echo Creating application directory...
if not exist "%USERPROFILE%\\UkrainePassportChecker" (
    mkdir "%USERPROFILE%\\UkrainePassportChecker"
)

echo Copying files...
copy "UkrainePassportChecker.exe" "%USERPROFILE%\\UkrainePassportChecker\\"
copy "config.example.json" "%USERPROFILE%\\UkrainePassportChecker\\"
copy "default.json" "%USERPROFILE%\\UkrainePassportChecker\\"

echo Creating desktop shortcut...
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\\Desktop\\Ukraine Passport Checker.lnk');$s.TargetPath='%USERPROFILE%\\UkrainePassportChecker\\UkrainePassportChecker.exe';$s.Save()"

echo.
echo Installation completed!
echo Application installed to: %USERPROFILE%\\UkrainePassportChecker
echo Desktop shortcut created
echo.
echo You can now run the application from the desktop shortcut
echo or from: %USERPROFILE%\\UkrainePassportChecker\\UkrainePassportChecker.exe
echo.
pause'''
    
    # Create dist directory if it doesn't exist
    if not os.path.exists('dist'):
        os.makedirs('dist')
    
    with open('dist/install.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    print("📦 Created installer script")

def main():
    """Main build process"""
    print("🚀 Starting build process for Ukraine Passport Checker")
    print("=" * 60)
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if build_executable():
        # Create installer
        create_installer_script()
        
        print("\n" + "=" * 60)
        print("🎉 Build completed successfully!")
        print(f"📂 Files created:")
        print(f"   - dist/UkrainePassportChecker.exe")
        print(f"   - dist/install.bat")
        if os.path.exists('dist/UkrainePassportChecker.exe'):
            print(f"📏 Executable size: {os.path.getsize('dist/UkrainePassportChecker.exe') / 1024 / 1024:.1f} MB")
        print("\n💡 To distribute:")
        print("   1. Copy the entire 'dist' folder")
        print("   2. Users can run install.bat for easy installation")
        print("   3. Or run UkrainePassportChecker.exe directly")
        return True
    else:
        print("\n❌ Build failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
