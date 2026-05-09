
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_advanced_metrics import AdvancedMetricsFetcher
import json

print("=" * 70)
print("完整运行：52周新高/新低（标普500 + 纳指100）")
print("=" * 70)

fetcher = AdvancedMetricsFetcher()

print("\n[1/4] 正在获取成分股...")
sp500_tickers = fetcher._get_cached_or_fetch('sp500_components.json', fetcher._fetch_sp500_components)
ndx_tickers = fetcher._get_cached_or_fetch('ndx100_components.json', fetcher._fetch_ndx100_components)
print(f"    标普500成分股数量：{len(sp500_tickers) if sp500_tickers else 0}")
print(f"    纳指100成分股数量：{len(ndx_tickers) if ndx_tickers else 0}")

print("\n[2/4] 计算标普500新高/新低...")
spy_nh, spy_nl = fetcher._calculate_52wk_counts(sp500_tickers, "标普500") if sp500_tickers else (0,0)

print("\n[3/4] 计算纳指100新高/新低...")
ndx_nh, ndx_nl = fetcher._calculate_52wk_counts(ndx_tickers, "纳指100") if ndx_tickers else (0,0)

print("\n" + "=" * 70)
print("最终完整结果：")
print(f"  【标普500】  新高：{spy_nh}  /  新低：{spy_nl}")
print(f"  【纳指100】  新高：{ndx_nh}  /  新低：{ndx_nl}")
print("=" * 70)

# 保存结果到临时文件
with open('full_result.json', 'w') as f:
    json.dump({
        'spy_nh': spy_nh,
        'spy_nl': spy_nl,
        'ndx_nh': ndx_nh,
        'ndx_nl': ndx_nl,
        'time': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, f, indent=2)

print(f"\n结果已保存到 full_result.json")
