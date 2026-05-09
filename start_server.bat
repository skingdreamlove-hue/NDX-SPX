@echo off
chcp 65001 >nul 2>&1

cd /d "d:\web\美股情绪监测"

REM 检查是否已有服务器在运行
if exist ".server_port" (
    del /q ".server_port"
)

REM 后台静默启动服务器，不显示窗口
start /B pythonw server.py >nul 2>&1

exit
