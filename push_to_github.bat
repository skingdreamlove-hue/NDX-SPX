@echo off
chcp 65001 >nul
title 上传代码到GitHub
echo ==========================================
echo   美股情绪监测系统 - GitHub上传工具
echo ==========================================
echo.

:: 进入项目目录
cd /d "d:\web\美股情绪监测"

:: 检查Git是否安装
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Git未安装，请先安装Git
    pause
    exit /b 1
)

:: 检查是否是git仓库
if not exist ".git" (
    echo [错误] 不是Git仓库，请先运行初始化
    pause
    exit /b 1
)

echo [1/3] 检查远程仓库...
git remote -v >nul 2>&1
if errorlevel 1 (
    echo [错误] 未配置远程仓库
    pause
    exit /b 1
)
echo [✓] 远程仓库已配置

echo.
echo [2/3] 添加修改的文件...
git add .
if errorlevel 1 (
    echo [错误] 添加文件失败
    pause
    exit /b 1
)
echo [✓] 文件已添加

echo.
echo [3/3] 检查是否有变更需要提交...
git diff --cached --quiet
if %errorlevel% == 0 (
    echo [✓] 没有新的变更需要提交
    echo.
    echo ==========================================
    echo   代码已是最新状态！
    echo ==========================================
    pause
    exit /b 0
)

echo 正在提交代码...
git commit -m "update: %date% %time%"
if errorlevel 1 (
    echo [错误] 提交失败
    pause
    exit /b 1
)
echo [✓] 代码已提交

echo.
echo 推送到GitHub...
git push
if errorlevel 1 (
    echo [错误] 推送失败
    pause
    exit /b 1
)
echo [✓] 推送成功

echo.
echo ==========================================
echo   [✓] 上传完成！
echo ==========================================
echo.
echo 代码已成功上传到GitHub！
pause
