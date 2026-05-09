const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { v4: uuidv4 } = require('crypto');

let mainWindow;
let backtestTasks = {};
let flaskProcess = null;
let flaskPort = null;

function startFlaskServer() {
    return new Promise((resolve, reject) => {
        const serverScript = path.join(__dirname, 'server.py');
        console.log('正在启动Flask服务端...');

        flaskProcess = spawn('python', [serverScript], {
            cwd: __dirname,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        let output = '';
        let portResolved = false;

        flaskProcess.stdout.on('data', (data) => {
            const text = data.toString('utf8');
            output += text;
            console.log('Flask:', text.trim());

            const portMatch = text.match(/端口:\s*(\d+)/);
            if (portMatch && !portResolved) {
                portResolved = true;
                flaskPort = parseInt(portMatch[1]);
                const portFile = path.join(__dirname, '.server_port');
                fs.writeFileSync(portFile, String(flaskPort));
                console.log(`Flask服务端已启动，端口: ${flaskPort}`);
                resolve(flaskPort);
            }
        });

        flaskProcess.stderr.on('data', (data) => {
            const text = data.toString('utf8');
            console.log('Flask stderr:', text.trim());
        });

        flaskProcess.on('close', (code) => {
            if (!portResolved) {
                reject(new Error(`Flask进程意外退出，代码: ${code}, 输出: ${output.slice(-200)}`));
            }
        });

        flaskProcess.on('error', (err) => {
            reject(new Error(`启动Flask失败: ${err.message}`));
        });

        setTimeout(() => {
            if (!portResolved) {
                reject(new Error('Flask启动超时（30秒）'));
            }
        }, 30000);
    });
}

function stopFlaskServer() {
    if (flaskProcess) {
        console.log('正在关闭Flask服务端...');
        flaskProcess.kill();
        flaskProcess = null;
    }
    try {
        const portFile = path.join(__dirname, '.server_port');
        if (fs.existsSync(portFile)) {
            fs.unlinkSync(portFile);
        }
    } catch (e) {}
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, 'assets/icon.png'),
        title: '美股情绪监测'
    });

    // 加载本地HTML文件
    mainWindow.loadFile('index.html');

    // 拦截页面内导航，将 /backtest 和 /restriction 映射到本地文件
    mainWindow.webContents.on('will-navigate', (event, url) => {
        if (url.endsWith('/backtest')) {
            event.preventDefault();
            mainWindow.loadFile('backtest.html');
        }
        if (url.endsWith('/restriction')) {
            event.preventDefault();
            mainWindow.loadFile('restriction.html');
        }
    });

    // 开发时打开开发者工具
    // mainWindow.webContents.openDevTools();
}

// 处理数据更新请求
ipcMain.handle('update-data', async () => {
    return new Promise((resolve) => {
        const pythonScript = path.join(__dirname, 'generate_charts.py');
        
        console.log('开始执行数据更新...');
        
        const pythonProcess = spawn('python', [pythonScript], {
            cwd: __dirname,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        let output = '';
        let errorOutput = '';
        let resolved = false;

        pythonProcess.stdout.on('data', (data) => {
            const text = data.toString('utf8');
            output += text;
            console.log('Python输出:', text);
        });

        pythonProcess.stderr.on('data', (data) => {
            const text = data.toString('utf8');
            errorOutput += text;
            console.error('Python错误:', text);
        });

        pythonProcess.on('close', (code) => {
            if (resolved) return;
            resolved = true;
            console.log(`Python进程退出，代码: ${code}`);
            
            if (code === 0) {
                console.log('开始执行基金数据爬虫...');
                const crawlerScript = path.join(__dirname, 'real_fund_crawler.py');
                const crawlerProcess = spawn('python', [crawlerScript], {
                    cwd: __dirname,
                    stdio: ['pipe', 'pipe', 'pipe']
                });
                let crawlerOutput = '';
                let crawlerError = '';
                crawlerProcess.stdout.on('data', (data) => { crawlerOutput += data.toString('utf8'); });
                crawlerProcess.stderr.on('data', (data) => { crawlerError += data.toString('utf8'); });
                crawlerProcess.on('close', (crawlerCode) => {
                    if (crawlerCode === 0) {
                        fundUpdateStatus = { is_running: false, message: '数据抓取完成', last_result: 'success' };
                        resolve({
                            success: true,
                            message: '数据更新成功（含基金限购数据）',
                            output: output,
                            fund_updated: true
                        });
                    } else {
                        fundUpdateStatus = { is_running: false, message: '抓取失败: ' + (crawlerError.slice(-200) || crawlerOutput.slice(-200)), last_result: 'error' };
                        resolve({
                            success: true,
                            message: '市场数据更新成功（基金限购数据更新失败）',
                            output: output,
                            fund_updated: false
                        });
                    }
                });
                crawlerProcess.on('error', (err) => {
                    resolve({
                        success: true,
                        message: '市场数据更新成功（基金爬虫启动失败）',
                        output: output,
                        fund_updated: false
                    });
                });
            } else {
                resolve({
                    success: false,
                    message: `数据更新失败: ${errorOutput || '未知错误'}`,
                    error: errorOutput
                });
            }
        });

        pythonProcess.on('error', (error) => {
            if (resolved) return;
            resolved = true;
            resolve({
                success: false,
                message: `启动Python进程失败: ${error.message}`
            });
        });

        setTimeout(() => {
            if (resolved) return;
            resolved = true;
            pythonProcess.kill();
            resolve({
                success: false,
                message: '数据更新超时（5分钟）'
            });
        }, 300000);
    });
});

// 处理读取最新市场数据请求
ipcMain.handle('load-market-data', async () => {
    try {
        const dataFile = path.join(__dirname, 'market_data.js');
        const content = fs.readFileSync(dataFile, 'utf8');
        const match = content.match(/var MARKET_DATA = ({.*});/s);
        if (match) {
            return { success: true, data: JSON.parse(match[1]) };
        }
        return { success: false, message: '无法解析market_data.js' };
    } catch (error) {
        return { success: false, message: error.message };
    }
});

let fundUpdateStatus = { is_running: false, message: '', last_result: null };

// 处理基金数据更新请求
ipcMain.handle('update-fund-data', async () => {
    if (fundUpdateStatus.is_running) {
        return { status: 'running', message: '爬虫正在运行中' };
    }
    fundUpdateStatus = { is_running: true, message: '正在抓取基金数据...', last_result: null };

    const runnerScript = path.join(__dirname, 'real_fund_crawler.py');
    const crawlerProcess = spawn('python', [runnerScript], {
        cwd: __dirname,
        stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    crawlerProcess.stdout.on('data', (data) => { stdout += data.toString('utf8'); });
    crawlerProcess.stderr.on('data', (data) => { stderr += data.toString('utf8'); });

    crawlerProcess.on('close', (code) => {
        if (code === 0) {
            fundUpdateStatus = { is_running: false, message: '数据抓取完成', last_result: 'success' };
        } else {
            fundUpdateStatus = { is_running: false, message: '抓取失败: ' + (stderr.slice(-200) || stdout.slice(-200)), last_result: 'error' };
        }
    });

    crawlerProcess.on('error', (err) => {
        fundUpdateStatus = { is_running: false, message: '启动爬虫失败: ' + err.message, last_result: 'error' };
    });

    return { status: 'started', message: '爬虫已启动' };
});

// 获取基金数据
ipcMain.handle('get-fund-data', async () => {
    try {
        const dataFile = path.join(__dirname, 'real_fund_data.json');
        const content = fs.readFileSync(dataFile, 'utf8');
        return { success: true, data: JSON.parse(content) };
    } catch (error) {
        return { success: false, message: error.message };
    }
});

// 查询基金更新状态
ipcMain.handle('get-fund-update-status', async () => {
    return fundUpdateStatus;
});

// 处理回测启动请求
ipcMain.handle('start-backtest', async (event, { start_date, end_date, initial_capital, initial_position, daily_sip, cash_yield, buy_cap }) => {
    if (start_date < '2007-10-01') {
        return { status: 'error', message: '开始时间不能早于2007年10月1日' };
    }
    const taskId = require('crypto').randomUUID();
    backtestTasks[taskId] = { status: 'running', progress: 0, message: '初始化...' };

    const pythonScript = path.join(__dirname, 'backtest_runner.py');
    const args = [pythonScript, start_date, end_date];
    if (initial_capital !== undefined) args.push('--initial-capital', String(initial_capital));
    if (initial_position !== undefined) args.push('--initial-position', String(initial_position));
    if (daily_sip !== undefined) args.push('--daily-sip', String(daily_sip));
    if (cash_yield !== undefined) args.push('--cash-yield', String(cash_yield));
    if (buy_cap !== undefined) args.push('--buy-cap', String(buy_cap));
    const pythonProcess = spawn('python', args, {
        cwd: __dirname,
        stdio: ['pipe', 'pipe', 'pipe']
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
        const text = data.toString('utf8');
        output += text;
        const lines = text.split('\n').filter(l => l.startsWith('PROGRESS:'));
        if (lines.length > 0) {
            try {
                const info = JSON.parse(lines[lines.length - 1].replace('PROGRESS:', ''));
                backtestTasks[taskId].progress = info.progress || 0;
                backtestTasks[taskId].message = info.message || '';
            } catch (e) {}
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString('utf8');
    });

    pythonProcess.on('close', (code) => {
        if (code === 0) {
            try {
                const reportMatch = output.match(/REPORT_START([\s\S]*?)REPORT_END/);
                if (reportMatch) {
                    const report = JSON.parse(reportMatch[1]);
                    backtestTasks[taskId] = { status: 'done', report: report };
                } else {
                    backtestTasks[taskId] = { status: 'error', message: '无法解析报告' };
                }
            } catch (e) {
                backtestTasks[taskId] = { status: 'error', message: '报告解析失败: ' + e.message };
            }
        } else {
            backtestTasks[taskId] = { status: 'error', message: errorOutput || '回测失败' };
        }
    });

    pythonProcess.on('error', (error) => {
        backtestTasks[taskId] = { status: 'error', message: error.message };
    });

    setTimeout(() => {
        if (backtestTasks[taskId] && backtestTasks[taskId].status === 'running') {
            pythonProcess.kill();
            backtestTasks[taskId] = { status: 'error', message: '回测超时' };
        }
    }, 600000);

    return { status: 'running', task_id: taskId };
});

// 处理回测进度查询请求
ipcMain.handle('backtest-progress', async (event, taskId) => {
    const task = backtestTasks[taskId];
    if (!task) {
        return { status: 'error', message: '任务不存在' };
    }
    return task;
});

ipcMain.handle('get-server-url', () => {
    try {
        const portFile = path.join(__dirname, '.server_port');
        const port = fs.readFileSync(portFile, 'utf8').trim();
        return `http://localhost:${port}`;
    } catch {
        return 'http://localhost:8080';
    }
});

app.whenReady().then(() => {
    createWindow();
    startFlaskServer().then((port) => {
        console.log(`Flask后台启动完成，端口: ${port}`);
    }).catch((err) => {
        console.error('Flask后台启动失败:', err.message);
    });
});

app.on('window-all-closed', () => {
    stopFlaskServer();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});