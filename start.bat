@echo off
REM AXXO Builder - Startup Script for Windows
REM This script starts the AXXO Builder desktop application

echo ==========================================
echo   Starting AXXO Builder...
echo ==========================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed
    echo Please install Node.js 16 or higher from nodejs.org
    pause
    exit /b 1
)

REM Check if yarn is installed
yarn --version >nul 2>&1
if errorlevel 1 (
    echo Installing yarn...
    npm install -g yarn
)

echo [OK] Prerequisites check passed
echo.

REM Install backend dependencies if needed
if not exist "backend\__pycache__" (
    echo Installing backend dependencies...
    cd backend
    pip install -r requirements.txt --quiet
    cd ..
    echo [OK] Backend dependencies installed
)

REM Install frontend dependencies if needed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call yarn install --silent
    cd ..
    echo [OK] Frontend dependencies installed
)

REM Build frontend if build folder doesn't exist
if not exist "frontend\build" (
    echo Building frontend for desktop (first time only, may take a minute)...
    cd frontend
    REM Copy desktop env config
    copy .env.desktop .env.production.local >nul
    set GENERATE_SOURCEMAP=false
    call yarn build
    del .env.production.local >nul 2>&1
    cd ..
    echo [OK] Frontend built successfully
)

REM Install electron dependencies if needed
if not exist "electron\node_modules" (
    echo Installing Electron...
    cd electron
    call yarn install --silent
    cd ..
    echo [OK] Electron installed
)

REM Start the application
echo.
echo ==========================================
echo   Launching AXXO Builder...
echo ==========================================
echo.

cd electron
call yarn start

echo.
echo AXXO Builder closed. Thank you!
pause
