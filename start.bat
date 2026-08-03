@echo off
echo ============================================
echo   AI Personal Agent - Starting up...
echo ============================================

:: Check for .env
if not exist ".env" (
    echo [ERROR] .env file not found! Copy .env.example to .env first.
    pause
    exit /b 1
)

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.10+ first.
    pause
    exit /b 1
)

:: Install dependencies
echo.
echo [1/3] Installing Python dependencies...
pip install -r backend\requirements.txt -q
if errorlevel 1 (
    echo [WARNING] Some packages may have failed to install.
)

:: Build frontend
echo.
echo [2/3] Building frontend...
if exist "frontend\package.json" (
    cd frontend
    if not exist "node_modules" (
        echo Installing npm packages...
        call npm install
    )
    echo Building frontend...
    call npm run build
    cd ..
    echo Frontend build complete.
) else (
    echo [WARNING] frontend\package.json not found, skipping build.
)

:: Start server
echo.
echo [3/3] Starting server...
echo ============================================
echo.
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info

pause
