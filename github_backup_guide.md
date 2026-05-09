# GitHub备份指南

## 项目信息
- **项目名称**: 美股情绪监测系统 (US Stock Sentiment Monitoring System)
- **项目路径**: `d:\web\美股情绪监测`

## 备份步骤

### 1. 确保已安装Git和GitHub CLI

如果尚未安装，请运行以下命令：

```powershell
# 安装Git
winget install --id Git.Git

# 安装GitHub CLI
winget install --id GitHub.cli
```

安装完成后，**重启终端**或**重启电脑**以确保环境变量生效。

### 2. 登录GitHub

```powershell
gh auth login
```

按照提示选择：
- 选择 `GitHub.com`
- 选择 `HTTPS`
- 选择使用浏览器登录或输入token

### 3. 进入项目目录

```powershell
cd "d:\web\美股情绪监测"
```

### 4. 初始化Git仓库（如果尚未初始化）

```powershell
git init
```

### 5. 配置Git用户信息（首次使用）

```powershell
git config user.email "your-email@example.com"
git config user.name "Your Name"
```

### 6. 创建.gitignore文件

创建一个 `.gitignore` 文件，内容如下：

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.*.local

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db
```

### 7. 添加文件并提交

```powershell
# 添加所有文件
git add .

# 提交代码
git commit -m "feat: initial commit of US stock sentiment monitoring project"
```

### 8. 创建GitHub仓库并推送

#### 选项A: 使用GitHub CLI（推荐）

```powershell
# 创建公开仓库并推送
gh repo create us-stock-sentiment-monitor --public --description "美股情绪监测系统 - US Stock Sentiment Monitoring System" --source=. --push

# 或创建私有仓库
gh repo create us-stock-sentiment-monitor --private --description "美股情绪监测系统 - US Stock Sentiment Monitoring System" --source=. --push
```

#### 选项B: 手动创建仓库并推送

1. 在GitHub网站上创建新仓库: https://github.com/new
2. 复制仓库URL（HTTPS格式）
3. 执行以下命令：

```powershell
# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 推送到GitHub
git push -u origin main
# 或如果默认分支是master
git push -u origin master
```

## 一键备份脚本

已为您创建批处理脚本 `backup_to_github.bat`，双击运行即可自动完成备份。

## 项目结构

```
美股情绪监测/
├── .venv/                  # Python虚拟环境
├── backtest_data/          # 回测数据
├── node_modules/           # Node.js依赖
├── templates/              # HTML模板
├── .gitignore              # Git忽略文件
├── README.md               # 项目说明
├── backtest.html           # 回测页面
├── backtest.py             # 回测脚本
├── index.html              # 主页面
├── main.js                 # 主程序
├── package.json            # Node.js配置
├── server.py               # 服务器脚本
└── ...                     # 其他文件
```

## 注意事项

1. **敏感信息**: 确保 `.env` 文件和其他包含敏感信息的文件已被添加到 `.gitignore`
2. **大文件**: 回测数据文件较大，已配置在 `.gitignore` 中，不会被提交
3. **node_modules**: 依赖文件夹已配置忽略，GitHub Actions可以自动安装

## 后续更新

备份完成后，每次更新代码后执行：

```powershell
git add .
git commit -m "描述你的更改"
git push
```

## 常见问题

### Q: 提示 "git" 不是内部或外部命令？
A: 请重启终端或电脑，确保Git安装后的环境变量已生效。

### Q: 提示未认证？
A: 运行 `gh auth login` 进行GitHub认证。

### Q: 仓库已存在？
A: 使用不同的仓库名称，或先删除GitHub上的同名仓库。

### Q: 推送被拒绝？
A: 确保你有该仓库的写入权限，或检查是否正确添加了远程仓库。
