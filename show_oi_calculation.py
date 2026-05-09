import json
from datetime import datetime
from pathlib import Path
from fetch_advanced_metrics import AdvancedMetricsFetcher

def show_oi_deviation_calculation():
    print("=" * 80)
    print("OI 偏离率计算公式与计算过程")
    print("=" * 80)
    
    # 1. 获取原始数据
    print("\n【步骤 1】获取当前 OI Ratio")
    print("-" * 80)
    fetcher = AdvancedMetricsFetcher()
    qqq_volume_ratio, qqq_oi_ratio = fetcher.get_qqq_pcr()
    spy_volume_ratio, spy_oi_ratio = fetcher.get_spy_pcr()
    
    print(f"QQQ Volume Ratio: {qqq_volume_ratio}")
    print(f"QQQ OI Ratio: {qqq_oi_ratio}")
    print(f"SPY Volume Ratio: {spy_volume_ratio}")
    print(f"SPY OI Ratio: {spy_oi_ratio}")
    
    # 2. 加载历史数据
    print("\n【步骤 2】加载历史数据")
    print("-" * 80)
    history_file = Path(__file__).parent / "pcr_history.json"
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        print(f"\nQQQ 历史数据 (共 {len(history['qqq'])} 条):")
        qqq_valid_data = []
        for i, entry in enumerate(history['qqq']):
            if entry.get('oi_ratio') is not None:
                qqq_valid_data.append(entry)
                print(f"  {i+1}. 日期: {entry['date']}, OI Ratio: {entry['oi_ratio']}")
        
        print(f"\nSPY 历史数据 (共 {len(history['spy'])} 条):")
        spy_valid_data = []
        for i, entry in enumerate(history['spy']):
            if entry.get('oi_ratio') is not None:
                spy_valid_data.append(entry)
                print(f"  {i+1}. 日期: {entry['date']}, OI Ratio: {entry['oi_ratio']}")
    else:
        print("历史数据文件不存在")
        return
    
    # 3. 计算 MA20
    print("\n【步骤 3】计算 MA20 (20日简单移动平均)")
    print("-" * 80)
    
    # QQQ
    if qqq_valid_data:
        qqq_oi_values = [d['oi_ratio'] for d in qqq_valid_data]
        qqq_ma20 = sum(qqq_oi_values) / len(qqq_oi_values)
        print(f"\nQQQ 有效数据点: {len(qqq_oi_values)} 个")
        print(f"QQQ OI Ratio 历史值: {qqq_oi_values}")
        print(f"QQQ OI Ratio MA20 = ({' + '.join([f'{v}' for v in qqq_oi_values])}) / {len(qqq_oi_values)}")
        print(f"QQQ OI Ratio MA20 = {sum(qqq_oi_values)} / {len(qqq_oi_values)} = {qqq_ma20:.4f}")
    
    # SPY
    if spy_valid_data:
        spy_oi_values = [d['oi_ratio'] for d in spy_valid_data]
        spy_ma20 = sum(spy_oi_values) / len(spy_oi_values)
        print(f"\nSPY 有效数据点: {len(spy_oi_values)} 个")
        print(f"SPY OI Ratio 历史值: {spy_oi_values}")
        print(f"SPY OI Ratio MA20 = ({' + '.join([f'{v}' for v in spy_oi_values])}) / {len(spy_oi_values)}")
        print(f"SPY OI Ratio MA20 = {sum(spy_oi_values)} / {len(spy_oi_values)} = {spy_ma20:.4f}")
    
    # 4. 计算偏离率
    print("\n【步骤 4】计算相对偏离率")
    print("-" * 80)
    print("\n计算公式:")
    print("  偏离率 = ((当前值 - MA20) / MA20) × 100")
    print("\n(偏离率 > 0 表示当前值高于平均,偏离率 < 0 表示当前值低于平均)")
    
    # QQQ 计算
    if qqq_oi_ratio is not None and qqq_valid_data and qqq_ma20 > 0:
        qqq_deviation = ((qqq_oi_ratio - qqq_ma20) / qqq_ma20) * 100
        print(f"\nQQQ OI Ratio 计算:")
        print(f"  当前值 = {qqq_oi_ratio}")
        print(f"  MA20 = {qqq_ma20:.4f}")
        print(f"  差值 = {qqq_oi_ratio} - {qqq_ma20:.4f} = {qqq_oi_ratio - qqq_ma20:.4f}")
        print(f"  相对差值 = {qqq_oi_ratio - qqq_ma20:.4f} / {qqq_ma20:.4f} = {(qqq_oi_ratio - qqq_ma20) / qqq_ma20:.6f}")
        print(f"  偏离率 = {(qqq_oi_ratio - qqq_ma20) / qqq_ma20:.6f} × 100 = {qqq_deviation:.1f}%")
    
    # SPY 计算
    if spy_oi_ratio is not None and spy_valid_data and spy_ma20 > 0:
        spy_deviation = ((spy_oi_ratio - spy_ma20) / spy_ma20) * 100
        print(f"\nSPY OI Ratio 计算:")
        print(f"  当前值 = {spy_oi_ratio}")
        print(f"  MA20 = {spy_ma20:.4f}")
        print(f"  差值 = {spy_oi_ratio} - {spy_ma20:.4f} = {spy_oi_ratio - spy_ma20:.4f}")
        print(f"  相对差值 = {spy_oi_ratio - spy_ma20:.4f} / {spy_ma20:.4f} = {(spy_oi_ratio - spy_ma20) / spy_ma20:.6f}")
        print(f"  偏离率 = {(spy_oi_ratio - spy_ma20) / spy_ma20:.6f} × 100 = {spy_deviation:.1f}%")
    
    # 5. 完整公式总结
    print("\n【总结】完整公式")
    print("-" * 80)
    print("\n1. OI Ratio 计算公式 (fetch_advanced_metrics.py):")
    print("   OI Ratio = 近8个到期日Put持仓总和 / 近8个到期日Call持仓总和")
    print("\n2. MA20 计算公式 (generate_charts.py):")
    print("   MA20 = 历史数据中所有有效OI Ratio的平均值 (取最近20天)")
    print("\n3. 偏离率计算公式 (generate_charts.py):")
    print("   偏离率 = ((当前OI Ratio - MA20) / MA20) × 100")
    print("\n4. 情绪判断规则:")
    print("   - 极度恐慌: QQQ 偏离率 > +70%")
    print("   - 恐慌:     QQQ 偏离率 > +40%")
    print("   - 极度贪婪: QQQ 偏离率 < -40%")
    print("   - 贪婪:     QQQ 偏离率 < -25%")
    print("\n   (SPY作为辅助确认信号,两个PCR同时超阈值时信号强度+1)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    show_oi_deviation_calculation()
