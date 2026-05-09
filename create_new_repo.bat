@echo off
chcp 65001 >nul
title 创建GitHub私有仓库并上传
echo ==========================================
echo   创建私有仓库: NDX-SPX
echo ==========================================
echo.

cd /d "d:\web\美股情绪监测"

echo [1/5] 清理旧的远程仓库配置...
git remote remove origin 2>nul

echo [2/5] 创建GitHub私有仓库...
gh repo create NDX-SPX --private --description "NDX&SPX 美股情绪监测系统" --source=. --remote=origin

if errorlevel 1 (
    echo.
    echo [错误] 创建仓库失败
    pause
    exit /b 1
)

echo [3/5] 添加所有文件...
git add .

echo [4/5] 提交代码...
git commit -m "feat: initial commit - NDX&SPX sentiment monitoring system" 2>nul

echo [5/5] 推送到GitHub...
git push -u origin master

if errorlevel 1 (
    echo.
    echo [错误] 推送失败
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   成功！
echo ==========================================
echo.
echo 仓库地址: https://github.com/roger-mengqi/NDX-SPX
echo.
pause
