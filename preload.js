const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    updateData: () => ipcRenderer.invoke('update-data'),
    loadMarketData: () => ipcRenderer.invoke('load-market-data'),
    startBacktest: (startDate, endDate, params) => ipcRenderer.invoke('start-backtest', { start_date: startDate, end_date: endDate, ...params }),
    backtestProgress: (taskId) => ipcRenderer.invoke('backtest-progress', taskId),
    updateFundData: () => ipcRenderer.invoke('update-fund-data'),
    getFundData: () => ipcRenderer.invoke('get-fund-data'),
    getFundUpdateStatus: () => ipcRenderer.invoke('get-fund-update-status'),
    getServerUrl: () => ipcRenderer.invoke('get-server-url')
});
