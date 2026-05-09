
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_advanced_metrics import AdvancedMetricsFetcher

print("=" * 60)
print("运行：获取52周新高/新低")
print("=" * 60)

fetcher = AdvancedMetricsFetcher()

result = fetcher.get_52wk_nh_nl_counts()

print("\n" + "=" * 60)
print("最终抓取结果：")
print(f"  标普500：新高 {result[0]} / 新低 {result[1]}")
print(f"  纳指100：新高 {result[2]} / 新低 {result[3]}")
print("=" * 60)

# 保存结果到临时文件
import json
with open('test_nhnl_result.json', 'w') as f:
    json.dump({
        'spy_nh': result[0],
        'spy_nl': result[1],
        'ndx_nh': result[2],
        'ndx_nl': result[3]
    }, f, indent=2)
