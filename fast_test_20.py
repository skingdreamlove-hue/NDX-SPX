
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import yfinance as yf
import time

print("=" * 60)
print("快速测试：前20只股票的52周新高/新低")
print("=" * 60)

tickers = [
    'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'META', 'TSLA', 'AVGO', 'COST',
    'NFLX', 'AMD', 'PEP', 'ADBE', 'CSCO', 'CMCSA', 'TMUS', 'INTC', 'INTU', 'AMGN'
]

nh = 0
nl = 0

for i, sym in enumerate(tickers):
    try:
        print(f"[{i+1}/{len(tickers)}] {sym}...", end=" ", flush=True)
        ticker = yf.Ticker(sym)
        hist = ticker.history(period='1y')
        
        if len(hist) >= 120:
            today_high = hist['High'].iloc[-1]
            today_low = hist['Low'].iloc[-1]
            high_max = hist['High'].max()
            low_min = hist['Low'].min()
            
            if today_high >= high_max:
                nh += 1
                print(f"✓ 新高！({today_high:.2f})")
            elif today_low <= low_min:
                nl += 1
                print(f"✗ 新低！({today_low:.2f})")
            else:
                print(f"OK")
        else:
            print(f"数据不足")
        time.sleep(0.2)
    except Exception as e:
        print(f"错误: {e}")

print("\n" + "=" * 60)
print(f"结果：新高 {nh} / 新低 {nl}")
print("=" * 60)
