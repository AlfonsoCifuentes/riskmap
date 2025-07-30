@echo off
echo ========================================
echo Enhanced Geopolitical Intelligence System
echo Professional Conflict Monitoring with AI
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python detected. Checking system...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install/upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install enhanced requirements
echo Installing enhanced AI requirements...
if exist "requirements_enhanced.txt" (
    pip install -r requirements_enhanced.txt
) else (
    echo WARNING: requirements_enhanced.txt not found, installing basic requirements
    pip install -r requirements.txt
)

REM Create necessary directories
echo Setting up directories...
if not exist "logs" mkdir logs
if not exist "reports" mkdir reports
if not exist "templates" mkdir templates

echo.
echo ========================================
echo Setup completed! Choose an option:
echo ========================================
echo 1. Run system setup and tests
echo 2. Start API server only
echo 3. Run comprehensive analysis
echo 4. Start full system (setup + API + monitoring)
echo 5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Running system setup and tests...
    python start_enhanced_system.py setup
    python start_enhanced_system.py test
) else if "%choice%"=="2" (
    echo Starting API server...
    echo API will be available at: http://localhost:8000
    echo Documentation at: http://localhost:8000/docs
    python start_enhanced_system.py api
) else if "%choice%"=="3" (
    echo Running comprehensive analysis...
    python start_enhanced_system.py analyze
) else if "%choice%"=="4" (
    echo Starting full enhanced system...
    echo This will setup, test, and start all services
    python start_enhanced_system.py full
) else if "%choice%"=="5" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice. Starting API server by default...
    python start_enhanced_system.py api
)

echo.
echo System startup completed!
echo.
echo Available endpoints:
echo - System Status: http://localhost:8000/system/status
echo - API Documentation: http://localhost:8000/docs
echo - Health Check: http://localhost:8000/health
echo.
pause