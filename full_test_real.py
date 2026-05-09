
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_advanced_metrics import AdvancedMetricsFetcher

print("=" * 60)
print("完整测试：调用 get_52wk_nh_nl_counts()")
print("=" * 60)

fetcher = AdvancedMetricsFetcher()

result = fetcher.get_52wk_nh_nl_counts()

print("\n" + "=" * 60)
print(f"最终结果：")
print(f"  标普500新高：{result[0]}")
print(f"  标普500新低：{result[1]}")
print(f"  纳指100新高：{result[2]}")
print(f"  纳指100新低：{result[3]}")
print("=" * 60)
