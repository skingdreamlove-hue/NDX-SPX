@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   Stock Monitor - Data Update
echo ============================================
echo.
echo Updating data, please wait...
echo.

cd /d "d:\web\美股情绪监测"
python generate_charts.py

echo.
echo ============================================
echo   Update Complete!
echo ============================================
echo.
echo Please refresh the browser page to see the latest data.
echo.
pause
