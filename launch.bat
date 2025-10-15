@echo off
REM Drafting Tools Suite Launcher
REM This script activates the virtual environment, installs dependencies, and launches the dashboard

echo ========================================
echo  Drafting Tools Suite Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create it first with: python -m venv .venv
    echo.
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [2/3] Installing/updating dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [3/3] Launching Dashboard...
echo.
python dashboard.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Dashboard failed to launch
    pause
    exit /b 1
)

