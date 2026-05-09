
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_advanced_metrics import AdvancedMetricsFetcher
import time

if __name__ == "__main__":
    print("=== 完整测试 52周新高/新低 ===")
    fetcher = AdvancedMetricsFetcher()
    result = fetcher.get_52wk_nh_nl_ratio()
    print(f"\n=== 最终结果 ===")
    print(f"返回值: {result}")
