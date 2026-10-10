@echo off
where python >nul 2>nul
if errorlevel 1 (
  echo Python is required. See BEGINNER.md.
  exit /b 2
)
python "%~dp0try_demo.py" %*
exit /b %errorlevel%
