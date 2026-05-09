
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_advanced_metrics import AdvancedMetricsFetcher
import time

print("=" * 60)
print("快速测试：52周新高/新低计算")
print("=" * 60)

fetcher = AdvancedMetricsFetcher()

print("\n1. 抓取标普500成分股...")
sp500_tickers = fetcher._get_cached_or_fetch(
    'sp500_components.json',
    fetcher._fetch_sp500_components
)
if sp500_tickers:
    print(f"   成功：{len(sp500_tickers)}只成分股")
    print(f"   前10只：{', '.join(sp500_tickers[:10])}")
else:
    print("   失败！")

print("\n2. 抓取纳斯达克100成分股...")
ndx_tickers = fetcher._get_cached_or_fetch(
    'ndx100_components.json',
    fetcher._fetch_ndx100_components
)
if ndx_tickers:
    print(f"   成功：{len(ndx_tickers)}只成分股")
    print(f"   前10只：{', '.join(ndx_tickers[:10])}")
else:
    print("   失败！")

print("\n3. 计算52周新高/新低（只计算前10只测试，避免超时）...")
if sp500_tickers:
    test_sp500 = sp500_tickers[:10]
    spy_nh, spy_nl = 0, 0
    for ticker in test_sp500:
        try:
            import yfinance as yf
            data = yf.Ticker(ticker)
            hist = data.history(period='1y')
            if len(hist) >= 252:
                current_high = hist['High'].iloc[-1]
                current_low = hist['Low'].iloc[-1]
                high_max = hist['High'].max()
                low_min = hist['Low'].min()
                if current_high >= high_max:
                    print(f"   {ticker} - 创52周新高！")
                    spy_nh += 1
                elif current_low <= low_min:
                    print(f"   {ticker} - 创52周新低！")
                    spy_nl += 1
                else:
                    print(f"   {ticker} - 无新高/新低")
            else:
                print(f"   {ticker} - 数据不足")
        except Exception as e:
            print(f"   {ticker} - 错误: {e}")
    print(f"\n   测试标普500前10只结果：新高 {spy_nh} / 新低 {spy_nl}")
print("=" * 60)
