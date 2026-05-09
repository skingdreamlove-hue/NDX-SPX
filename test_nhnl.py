
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_advanced_metrics import AdvancedMetricsFetcher

if __name__ == "__main__":
    fetcher = AdvancedMetricsFetcher()
    result = fetcher.get_52wk_nh_nl_ratio()
    print(f"\n最终返回值: {result}")
