@echo off
echo Starting Project File Monitor...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import openpyxl, docx, PyPDF2" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install required packages
        pause
        exit /b 1
    )
)

REM Launch the application
python launch_project_monitor.py

if errorlevel 1 (
    echo.
    echo Application exited with an error
    pause
)
