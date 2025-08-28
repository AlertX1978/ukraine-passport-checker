# Ukraine Passport Checker

A Python application to monitor Ukrainian passport status with both GUI and API interfaces. Get notified automatically when your passport status changes!

## 🚀 Features

- **Desktop GUI**: User-friendly interface with real-time status updates
- **Auto-check**: Scheduled monitoring at configurable intervals (every 30 minutes by default)
- **Email notifications**: Automatic alerts when passport status changes
- **Log management**: Organized logs with easy access from GUI
- **API server**: REST endpoints for mobile/web integration
- **Stealth browsing**: Uses undetected Chrome driver to avoid detection

## 📋 Requirements

- Python 3.8 or higher
- Google Chrome browser
- Gmail account (for email notifications)

## 🛠️ Installation

### Method 1: Quick Start (Recommended)

1. **Download or clone this repository**
   ```bash
   git clone https://github.com/yourusername/ukraine-passport-checker.git
   cd ukraine-passport-checker
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application**
   ```bash
   cp config.example.json config.json
   ```
   Edit `config.json` with your settings:
   - Add your passport code
   - Configure email settings (sender, recipient, app password)

4. **Run the application**
   - **Windows**: Double-click `start_gui.bat`
   - **Manual**: `python gui_app.py`

### Method 2: Virtual Environment (Recommended for developers)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python gui_app.py
```

## ⚙️ Configuration

Settings are stored in `config.json`:

- **passport_code**: Your Ukrainian passport tracking code
- **check_interval_seconds**: How often to check (1800 = 30 minutes)
- **email**: SMTP configuration for notifications
  - Use Gmail App Passwords for security
  - Enable 2FA and generate an app password
- **timeouts**: Web scraping timeout settings

### Email Setup (Gmail)

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password: Account Settings → Security → App Passwords
3. Use the app password (not your regular password) in the config

## 🎯 Usage

### GUI Application
1. **Launch**: Double-click `start_gui.bat` or run `python gui_app.py`
2. **Configure**: Enter your passport code and email settings
3. **Check**: Click "Run One Check" for immediate check or "Start Auto-Check" for continuous monitoring

### API Server
```bash
python api_server.py
```
- Access at `http://localhost:5000`
- Endpoints: `/check`, `/status`, `/config`

## 📁 Project Structure

```
ukraine-passport-checker/
├── gui_app.py              # Desktop GUI application
├── passport_check.py       # Core passport checking logic
├── api_server.py          # REST API server
├── enhanced_stealth.py    # Stealth browsing utilities
├── config.json           # Configuration file (create from example)
├── config.example.json   # Configuration template
├── default.json          # Default values for reset function
├── start_gui.bat         # Windows launcher
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🐛 Troubleshooting

**Import errors**: 
```bash
pip install setuptools
```

**Chrome issues**: 
- Ensure Google Chrome is installed and up to date
- The application will automatically download the correct ChromeDriver

**Permission errors**: 
- Run as administrator on Windows
- Check file permissions on Linux/Mac

**Email not working**:
- Verify Gmail app password is correct
- Check that 2FA is enabled on Gmail
- Ensure "Less secure app access" is disabled (use app passwords instead)

## 🔒 Security Notes

- Email credentials are stored in `config.json` - keep this file secure
- Consider using environment variables for production deployment
- The application uses stealth techniques to avoid detection by anti-bot systems

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## ⚠️ Disclaimer

This tool is for personal use only. Please respect the terms of service of the Ukrainian passport tracking website. The authors are not responsible for any misuse of this application.

## 🙋‍♂️ Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Search existing issues on GitHub
3. Create a new issue with detailed information about your problem

---

**Star ⭐ this repository if it helped you track your Ukrainian passport!**
