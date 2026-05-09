@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   Stock Sentiment Monitor - Desktop App
echo ============================================
echo.
echo Starting application, please wait...
echo.

cd /d "d:\web\美股情绪监测"

REM Check if dependencies are installed
if not exist "node_modules" (
    echo Installing dependencies for first run...
    npm install
    echo.
)

echo Launching desktop application...
npm start

echo.
echo Application started!
echo.
pause