@echo off
echo ===============================================
echo  Ukraine Passport Checker - Installer
echo ===============================================
echo.

echo Creating application directory...
if not exist "%USERPROFILE%\UkrainePassportChecker" (
    mkdir "%USERPROFILE%\UkrainePassportChecker"
)

echo Copying files...
copy "UkrainePassportChecker.exe" "%USERPROFILE%\UkrainePassportChecker\"
copy "config.example.json" "%USERPROFILE%\UkrainePassportChecker\"
copy "default.json" "%USERPROFILE%\UkrainePassportChecker\"

echo Creating desktop shortcut...
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\Ukraine Passport Checker.lnk');$s.TargetPath='%USERPROFILE%\UkrainePassportChecker\UkrainePassportChecker.exe';$s.Save()"

echo.
echo Installation completed!
echo Application installed to: %USERPROFILE%\UkrainePassportChecker
echo Desktop shortcut created
echo.
echo You can now run the application from the desktop shortcut
echo or from: %USERPROFILE%\UkrainePassportChecker\UkrainePassportChecker.exe
echo.
pause