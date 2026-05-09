
import yfinance as yf
import time

print("=== 快速测试 ===")

sample_stocks = [
    'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL'
]

nh_count = 0
nl_count = 0

for sym in sample_stocks:
    print(f"\n---> 处理: {sym}", flush=True)
    try:
        ticker = yf.Ticker(sym)
        print(f"  调用 history...", flush=True)
        hist = ticker.history(period="1y", interval="1d")
        print(f"  成功，数据长度: {len(hist)}", flush=True)
        
        if len(hist) >= 250:
            current = hist['Close'].iloc[-1]
            h52wk_max = hist['High'].max()
            h52wk_min = hist['Low'].min()
            
            print(f"  当前: {current:.2f}, 52周最高: {h52wk_max:.2f}, 52周最低: {h52wk_min:.2f}")
            
            if current >= h52wk_max * 0.98:
                nh_count += 1
                print(f"  → 计入52周新高！")
            elif current <= h52wk_min * 1.02:
                nl_count += 1
                print(f"  → 计入52周新低！")
        else:
            print(f"  历史数据不足250天")
        
        time.sleep(0.1)
    except Exception as e:
        print(f"  错误: {str(e)}", flush=True)

print(f"\n=== 最终统计 ===")
print(f"52周新高: {nh_count}")
print(f"52周新低: {nl_count}")
total = nh_count + nl_count
if total > 0:
    print(f"比率: {nh_count / total:.2f}")
else:
    print("无有效数据！")
