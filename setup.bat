@echo off
REM AXXO Builder - Quick Setup Script for Windows
REM Run this once to prepare everything

echo ================================================
echo   AXXO Builder - Initial Setup
echo ================================================
echo.

cd /d "%~dp0"

echo Installing backend dependencies...
cd backend
pip install -r requirements.txt
cd ..
echo [OK] Backend ready
echo.

echo Installing frontend dependencies...
cd frontend
call yarn install
echo [OK] Frontend dependencies installed
echo.

echo Building optimized frontend for desktop...
copy .env.desktop .env.production.local >nul
set GENERATE_SOURCEMAP=false
call yarn build
del .env.production.local >nul 2>&1
cd ..
echo [OK] Frontend built
echo.

echo Installing Electron...
cd electron
call yarn install
cd ..
echo [OK] Electron ready
echo.

echo ================================================
echo   Setup Complete!
echo ================================================
echo.
echo To start the application, run: start.bat
echo.
pause
