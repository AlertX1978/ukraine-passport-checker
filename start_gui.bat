@echo off
setlocal
pushd "%~dp0"

echo.
echo ================================================
echo    Ukraine Passport Checker - Starting GUI
echo ================================================
echo.

if exist ".venv\Scripts\python.exe" (
  echo Using virtual environment Python...
  ".venv\Scripts\python.exe" gui_app.py
) else (
  echo Virtual environment not found - using system Python...
  echo If this fails, please run: python -m venv .venv
  py -3 gui_app.py
)

echo.
echo GUI has been closed.
pause

popd
endlocal
