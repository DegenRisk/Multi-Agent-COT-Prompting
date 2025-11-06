@echo off
REM Financial Corpus Analyzer - Startup Script for Windows

echo.
echo Starting Financial Corpus Analyzer...
echo.

REM Check if we're in the right directory
if not exist "src\ui\server.py" (
    echo Error: This script must be run from the universal-orchestrator directory
    echo    Run: cd universal-orchestrator ^&^& start.bat
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo No .env file found. Creating from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and add your API keys!
    echo    Required: OPENAI_API_KEY or ANTHROPIC_API_KEY or GOOGLE_API_KEY
    echo.
    pause
)

REM Start the server
echo.
echo Starting Financial Corpus Analyzer on http://localhost:8000
echo.
echo Features available:
echo   - Drag ^& drop file upload (PDF, CSV, XLSX, DOC, TXT)
echo   - URL scraping for financial data
echo   - Alpha extraction with AI
echo   - Comprehensive report generation
echo.
echo Press Ctrl+C to stop the server
echo.

python -m src.ui.server
