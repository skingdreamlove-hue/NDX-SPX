@echo off
chcp 65001 >nul
cd /d "d:\web\美股情绪监测"

echo 修复远程仓库地址...
git remote remove origin 2>nul
git remote add origin https://github.com/roger-mengqi/us-stock-sentiment-monitor.git

echo.
echo 验证远程仓库...
git remote -v

echo.
echo 添加所有文件...
git add .

echo.
echo 提交代码...
git commit -m "feat: initial commit" 2>nul
if errorlevel 1 (
    echo 提交失败或已提交
)

echo.
echo 推送到GitHub...
git push -u origin master
if errorlevel 1 (
    echo.
    echo 推送失败！请检查网络或仓库是否存在
    pause
    exit /b 1
)

echo.
echo ==========================================
echo 推送成功！
echo ==========================================
pause
