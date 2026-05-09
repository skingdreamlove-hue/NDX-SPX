import requests
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Barchart NDTH
r1 = requests.get('https://www.barchart.com/stocks/quotes/$NDTH', headers=headers, timeout=10)
m1 = re.search(r'"lastPrice":([0-9.]+)', r1.text)
m1_close = re.search(r'"close":([0-9.]+)', r1.text)
dates1 = re.findall(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}', r1.text[:10000])
times1 = re.findall(r'"tradeTime":"([^"]+)"', r1.text)

print("=" * 50)
print("Barchart - NDTH (纳斯达克100高于200日线)")
print("=" * 50)
print(f"  最新值: {m1.group(1) if m1 else 'N/A'}%")
print(f"  收盘值: {m1_close.group(1) if m1_close else 'N/A'}%")
print(f"  交易时间: {times1[0] if times1 else 'N/A'}")
print(f"  页面日期: {dates1[:5]}")

# Barchart S5TH
r2 = requests.get('https://www.barchart.com/stocks/quotes/$S5TH', headers=headers, timeout=10)
m2 = re.search(r'"lastPrice":([0-9.]+)', r2.text)
m2_close = re.search(r'"close":([0-9.]+)', r2.text)
dates2 = re.findall(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}', r2.text[:10000])
times2 = re.findall(r'"tradeTime":"([^"]+)"', r2.text)

print()
print("=" * 50)
print("Barchart - S5TH (标普500高于200日线)")
print("=" * 50)
print(f"  最新值: {m2.group(1) if m2 else 'N/A'}%")
print(f"  收盘值: {m2_close.group(1) if m2_close else 'N/A'}%")
print(f"  交易时间: {times2[0] if times2 else 'N/A'}")
print(f"  页面日期: {dates2[:5]}")
