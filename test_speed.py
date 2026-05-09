
"""
测试广度计算速度
"""
import yfinance as yf
import tempfile
import time

yf.set_tz_cache_location(tempfile.gettempdir())

# 测试用的股票列表（100只）
TEST_SYMBOLS = [
    'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'META', 'TSLA', 'AVGO', 'COST',
    'NFLX', 'AMD', 'PEP', 'ADBE', 'CSCO', 'CMCSA', 'TMUS', 'INTC', 'INTU', 'AMGN',
    'QCOM', 'TXN', 'HON', 'AMAT', 'SBUX', 'ISRG', 'BKNG', 'GILD', 'ADI', 'MDLZ',
    'ADP', 'VRTX', 'REGN', 'LRCX', 'PANW', 'MU', 'PYPL', 'KLAC', 'SNPS', 'CDNS',
    'ABNB', 'MELI', 'CRWD', 'MAR', 'MRVL', 'ORLY', 'CSX', 'FTNT', 'ADSK', 'DASH',
    'WDAY', 'NXPI', 'ROP', 'PCAR', 'CPRT', 'AEP', 'PAYX', 'MNST', 'ODFL', 'ROST',
    'FAST', 'KDP', 'EA', 'VRSK', 'CTSH', 'BKR', 'GEHC', 'EXC', 'KHC', 'TEAM',
    'DXCM', 'CTAS', 'IDXX', 'LULU', 'CSGP', 'ON', 'TTWO', 'FANG', 'CDW', 'BIIB',
    'ANSS', 'GFS', 'DDOG', 'ZS', 'ILMN', 'MRNA', 'ARM', 'SMCI', 'TTD', 'WBD',
    'DLTR', 'MDB', 'CEG', 'CCEP', 'XEL', 'APP'
]

print("="*60)
print("开始速度测试（100只股票）")
print("="*60)

start_total = time.time()
above_200 = 0
total = 0
success = 0
failed = 0

for i, sym in enumerate(TEST_SYMBOLS):
    try:
        ticker = yf.Ticker(sym)
        info = ticker.info
        
        current_price = info.get('regularMarketPrice')
        ma200 = info.get('twoHundredDayAverage')
        
        if current_price is not None and ma200 is not None and ma200 > 0:
            total += 1
            success += 1
            if current_price > ma200:
                above_200 += 1
        else:
            failed += 1
            
    except Exception:
        failed += 1
        continue
    
    # 每10只显示一下进度
    if (i + 1) % 10 == 0:
        elapsed = time.time() - start_total
        print(f"进度: {i+1}/{len(TEST_SYMBOLS)} - 已用{elapsed:.1f}秒")

elapsed_total = time.time() - start_total

print(f"\n{'='*60}")
print("测试结果:")
print(f"{'='*60}")
print(f"成功: {success}, 失败: {failed}")
print(f"高于MA200: {above_200}/{total} = {(above_200/total*100):.1f}%")
print(f"总耗时: {elapsed_total:.1f}秒")
print(f"平均每只: {(elapsed_total/len(TEST_SYMBOLS)):.2f}秒")
print(f"\n估算500只耗时: {(elapsed_total/len(TEST_SYMBOLS)*500):.1f}秒 = {(elapsed_total/len(TEST_SYMBOLS)*500/60):.1f}分钟")

