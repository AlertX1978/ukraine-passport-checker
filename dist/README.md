# Ukraine Passport Checker - Executable Distribution

## 🚀 Quick Start

### Option 1: Easy Installation (Recommended)

1. Run `install.bat` as Administrator
2. This will:
   - Install the application to your user folder
   - Create a desktop shortcut
   - Copy configuration files

### Option 2: Portable Use

1. Run `UkrainePassportChecker.exe` directly
2. No installation required

## 📁 Files Included

- **UkrainePassportChecker.exe** - Main application (27.2 MB)
- **install.bat** - Installer script for system installation
- **config.example.json** - Configuration template
- **default.json** - Default settings for reset function

## ⚙️ First Time Setup

1. **Launch the application** (double-click the .exe or desktop shortcut)
2. **Configure your settings:**
   - Enter your Ukrainian passport tracking code
   - Add your email settings for notifications
   - Set check interval (default: 30 minutes)

## 📧 Email Configuration (Gmail)

For email notifications to work:

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password:**
   - Go to Gmail → Settings → Security → App Passwords
   - Generate a new app password
3. **Use the app password** (not your regular password) in the application

## 🔧 System Requirements

- **Windows 10/11** (64-bit)
- **Google Chrome browser** (will be auto-configured)
- **Internet connection**

## 🐛 Troubleshooting

**Windows Defender Warning:**
- This is a false positive common with PyInstaller executables
- Click "More info" → "Run anyway" if prompted

**First Run is Slow:**
- Normal behavior - downloading Chrome driver components
- Subsequent runs will be much faster

**Application Won't Start:**
- Run as Administrator
- Check if Google Chrome is installed
- Ensure you have an active internet connection

## 📞 Support

For issues or questions:
- GitHub: https://github.com/AlertX1978/ukraine-passport-checker
- Check the main repository README for detailed documentation

---

**Note:** This is a standalone executable. No Python installation required!
