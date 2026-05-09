
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

print("=== 开始调试测试 ===")

from fetch_advanced_metrics import AdvancedMetricsFetcher
import time

if __name__ == "__main__":
    print("正在初始化...", flush=True)
    fetcher = AdvancedMetricsFetcher()
    
    print("正在调用 get_52wk_nh_nl_ratio()...", flush=True)
    result = fetcher.get_52wk_nh_nl_ratio()
    
    print(f"\n=== 最终结果 ===")
    print(f"返回值: {result}")
