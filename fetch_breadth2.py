import requests
import re
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("=" * 60)
print("抓取纳斯达克100和标普500高于200日线比例数据")
print("=" * 60)

# 1. Barchart NDTH
print("\n【1. Barchart - NDTH (纳斯达克100高于200日线)】")
r1 = requests.get('https://www.barchart.com/stocks/quotes/$NDTH', headers=headers, timeout=10)
print(f"  状态码: {r1.status_code}")
m1 = re.search(r'"lastPrice":([0-9.]+)', r1.text)
if m1:
    print(f"  NDTH 最新值: {m1.group(1)}%")
m1_close = re.search(r'"close":([0-9.]+)', r1.text)
if m1_close:
    print(f"  NDTH 收盘值: {m1_close.group(1)}%")
# find date
dates1 = re.findall(r'"tradeTime":"([^"]+)"', r1.text)
if dates1:
    print(f"  交易时间: {dates1[0]}")
dates1b = re.findall(r'"lastUpdate":"([^"]+)"', r1.text)
if dates1b:
    print(f"  最后更新: {dates1b[0]}")
# find all date-like patterns
all_dates = re.findall(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}', r1.text[:10000])
if all_dates:
    print(f"  页面中的日期: {all_dates[:5]}")

# 2. Barchart S5TH
print("\n【2. Barchart - S5TH (标普500高于200日线)】")
r2 = requests.get('https://www.barchart.com/stocks/quotes/$S5TH', headers=headers, timeout=10)
print(f"  状态码: {r2.status_code}")
m2 = re.search(r'"lastPrice":([0-9.]+)', r2.text)
if m2:
    print(f"  S5TH 最新值: {m2.group(1)}%")
m2_close = re.search(r'"close":([0-9.]+)', r2.text)
if m2_close:
    print(f"  S5TH 收盘值: {m2_close.group(1)}%")
dates2 = re.findall(r'"tradeTime":"([^"]+)"', r2.text)
if dates2:
    print(f"  交易时间: {dates2[0]}")
dates2b = re.findall(r'"lastUpdate":"([^"]+)"', r2.text)
if dates2b:
    print(f"  最后更新: {dates2b[0]}")
all_dates2 = re.findall(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}', r2.text[:10000])
if all_dates2:
    print(f"  页面中的日期: {all_dates2[:5]}")

# 3. Google Finance
print("\n【3. Google Finance - NDTH】")
r3 = requests.get('https://www.google.com/finance/quote/NDTH:INDEXNASDAQ', headers=headers, timeout=10)
print(f"  状态码: {r3.status_code}")
# Google Finance uses different patterns
gm1 = re.search(r'data-last-price="([0-9.]+)"', r3.text)
if gm1:
    print(f"  NDTH 最新值: {gm1.group(1)}%")
else:
    # try another pattern
    gm1b = re.findall(r'"price":([0-9.]+)', r3.text)
    if gm1b:
        print(f"  NDTH price字段: {gm1b[:3]}")
    gm1c = re.findall(r'([4-9][0-9]\.[0-9]+)', r3.text[:2000])
    if gm1c:
        print(f"  NDTH 可能的值: {gm1c[:5]}")

print("\n【4. Google Finance - S5TH】")
r4 = requests.get('https://www.google.com/finance/quote/S5TH:INDEXSP', headers=headers, timeout=10)
print(f"  状态码: {r4.status_code}")
gm2 = re.search(r'data-last-price="([0-9.]+)"', r4.text)
if gm2:
    print(f"  S5TH 最新值: {gm2.group(1)}%")
else:
    gm2b = re.findall(r'"price":([0-9.]+)', r4.text)
    if gm2b:
        print(f"  S5TH price字段: {gm2b[:3]}")

# 5. Investing.com (from search)
print("\n【5. Investing.com (搜索结果摘要)】")
print("  S5TH (标普500高于200日线): 54.98% (来自搜索摘要，日期未知)")

# 6. StreetStats
print("\n【6. StreetStats】")
print("  网站: https://streetstats.finance/markets/breadth-momentum/NQ100")
print("  网站: https://streetstats.finance/markets/breadth-momentum/SP500")
print("  注: JavaScript渲染，无法通过API直接抓取数值")

# 7. MacroMicro
print("\n【7. MacroMicro】")
print("  网站: https://en.macromicro.me/series/25229/nasdaq100-ma200-breadth")
print("  网站: https://en.macromicro.me/series/22718/sp-500-200ma-breadth")
print("  注: 需要登录，返回403")

# 8. MarketInOut
print("\n【8. MarketInOut】")
print("  网站: https://www.marketinout.com/chart/market.php?breadth=above-sma-200")
print("  注: JavaScript渲染，无法直接抓取数值")

print("\n" + "=" * 60)
print("汇总结果")
print("=" * 60)
print(f"  纳斯达克100高于200日线 (NDTH): {m1.group(1) if m1 else 'N/A'}% (Barchart)")
print(f"  标普500高于200日线 (S5TH): {m2.group(1) if m2 else 'N/A'}% (Barchart)")
print(f"  标普500高于200日线 (S5TH): 54.98% (Investing.com搜索摘要)")
print(f"\n  你项目market_data.json中的数据:")
print(f"    ndx_breadth_200ma: 53.0%")
print(f"    sp500_breadth_200ma: 57.0%")
print(f"    last_update: 2026-04-29 00:21:52")
