@echo off
chcp 65001 >nul
echo ==========================================
echo   诊断GitHub上传状态
echo ==========================================
echo.
cd /d "d:\web\美股情绪监测"

echo [1] 检查Git状态...
git status
echo.

echo [2] 检查远程仓库配置...
git remote -v
echo.

echo [3] 检查提交历史...
git log --oneline -5
echo.

echo [4] 检查分支状态...
git branch -v
echo.

echo ==========================================
echo 请截图或复制上面的信息给我
echo ==========================================
pause
