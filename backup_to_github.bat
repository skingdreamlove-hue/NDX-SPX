@echo off
chcp 65001 >nul
title 备份项目到GitHub
echo ==========================================
echo   美股情绪监测系统 - GitHub备份工具
echo ==========================================
echo.

:: 检查Git是否安装
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Git未安装，正在尝试安装...
    winget install --id Git.Git --accept-package-agreements --accept-source-agreements
    echo.
    echo 请安装完成后重启此脚本！
    pause
    exit /b 1
)
echo [✓] Git已安装

:: 检查GitHub CLI是否安装
gh --version >nul 2>&1
if errorlevel 1 (
    echo [错误] GitHub CLI未安装，正在尝试安装...
    winget install --id GitHub.cli --accept-package-agreements --accept-source-agreements
    echo.
    echo 请安装完成后重启此脚本！
    pause
    exit /b 1
)
echo [✓] GitHub CLI已安装

:: 检查GitHub认证
gh auth status >nul 2>&1
if errorlevel 1 (
    echo.
    echo [提示] 需要先登录GitHub账号
    echo 请在弹出的提示中完成登录...
    gh auth login
    if errorlevel 1 (
        echo [错误] GitHub登录失败
        pause
        exit /b 1
    )
)
echo [✓] GitHub已认证

echo.
echo ==========================================
echo   开始备份项目
echo ==========================================
echo.

:: 进入项目目录
cd /d "d:\web\美股情绪监测"

:: 检查是否已是git仓库
if not exist ".git" (
    echo [1/5] 初始化Git仓库...
    git init
    if errorlevel 1 (
        echo [错误] 初始化Git仓库失败
        pause
        exit /b 1
    )
) else (
    echo [1/5] Git仓库已存在，跳过初始化
)

:: 配置Git用户信息（如果未配置）
git config user.name >nul 2>&1
if errorlevel 1 (
    echo [2/5] 配置Git用户信息...
    git config user.email "backup@example.com"
    git config user.name "Backup Bot"
) else (
    echo [2/5] Git用户信息已配置
)

:: 创建.gitignore
echo [3/5] 检查.gitignore文件...
if not exist ".gitignore" (
    echo 正在创建.gitignore文件...
    (
        echo # Python
        echo __pycache__/
        echo *.py[cod]
        echo *$py.class
        echo *.so
        echo .Python
        echo build/
        echo develop-eggs/
        echo dist/
        echo downloads/
        echo eggs/
        echo .eggs/
        echo lib/
        echo lib64/
        echo parts/
        echo sdist/
        echo var/
        echo wheels/
        echo *.egg-info/
        echo .installed.cfg
        echo *.egg
        echo.
        echo # Virtual Environment
        echo venv/
        echo ENV/
        echo env/
        echo .venv/
        echo.
        echo # IDE
        echo .vscode/
        echo .idea/
        echo *.swp
        echo *.swo
        echo *~
        echo.
        echo # Node.js
        echo node_modules/
        echo npm-debug.log*
        echo yarn-debug.log*
        echo yarn-error.log*
        echo.
        echo # Environment variables
        echo .env
        echo .env.local
        echo .env.*.local
        echo.
        echo # Logs
        echo logs/
        echo *.log
        echo.
        echo # OS
        echo .DS_Store
        echo Thumbs.db
    ) > .gitignore
    echo [✓] .gitignore已创建
) else (
    echo [✓] .gitignore已存在
)

:: 添加并提交文件
echo [4/5] 添加文件到Git...
git add .
if errorlevel 1 (
    echo [错误] 添加文件失败
    pause
    exit /b 1
)

:: 检查是否有变更需要提交
git diff --cached --quiet
if %errorlevel% == 0 (
    echo [✓] 没有新的变更需要提交
) else (
    echo 正在提交代码...
    git commit -m "feat: backup US stock sentiment monitoring project"
    if errorlevel 1 (
        echo [错误] 提交代码失败
        pause
        exit /b 1
    )
    echo [✓] 代码已提交
)

:: 创建GitHub仓库并推送
echo [5/5] 创建GitHub仓库并推送...
echo.

:: 询问仓库名称
set /p REPO_NAME="请输入GitHub仓库名称 (直接回车使用默认: us-stock-sentiment-monitor): "
if "!REPO_NAME!"=="" set REPO_NAME=us-stock-sentiment-monitor

echo.
echo 请选择仓库类型:
echo [1] 公开仓库 (Public)
echo [2] 私有仓库 (Private)
set /p CHOICE="请输入选项 (1或2): "

if "!CHOICE!"=="2" (
    set VISIBILITY=--private
    set VISIBILITY_NAME=私有
) else (
    set VISIBILITY=--public
    set VISIBILITY_NAME=公开
)

echo.
echo 正在创建!VISIBILITY_NAME!仓库: !REPO_NAME!...
echo.

gh repo create !REPO_NAME! !VISIBILITY! --description "美股情绪监测系统 - US Stock Sentiment Monitoring System" --source=. --push

if errorlevel 1 (
    echo.
    echo [错误] 创建GitHub仓库失败
    echo 可能的原因:
    echo   - 仓库名称已存在
    echo   - 网络连接问题
    echo   - 权限不足
    echo.
    echo 您可以手动在GitHub上创建仓库，然后运行:
    echo   git remote add origin https://github.com/YOUR_USERNAME/!REPO_NAME!.git
    echo   git push -u origin main
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   [✓] 备份成功！
echo ==========================================
echo.
echo 您的项目已成功备份到GitHub！
echo 仓库地址: https://github.com/YOUR_USERNAME/!REPO_NAME!
echo.
echo 后续更新代码，请运行:
echo   git add .
echo   git commit -m "描述你的更改"
echo   git push
pause
