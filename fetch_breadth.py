import requests
import re
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

results = {}

# 1. Google Finance - NDTH
print("=== Google Finance NDTH ===")
url = 'https://www.google.com/finance/quote/NDTH:INDEXNASDAQ'
r = requests.get(url, headers=headers, timeout=10)
print(f"Status: {r.status_code}, Length: {len(r.text)}")
m = re.search(r'data-last-price="([0-9.]+)"', r.text)
if m:
    print(f"NDTH last price: {m.group(1)}")
    results['NDTH_google'] = m.group(1)
else:
    print("NDTH price not found in data-last-price")
    # Try alternative patterns
    m2 = re.findall(r'([4-9][0-9]\.[0-9]+)', r.text[:5000])
    print(f"Possible prices in first 5000 chars: {m2[:5]}")

# 2. Google Finance - S5TH
print("\n=== Google Finance S5TH ===")
url2 = 'https://www.google.com/finance/quote/S5TH:INDEXTSP'
r2 = requests.get(url2, headers=headers, timeout=10)
print(f"Status: {r2.status_code}, Length: {len(r2.text)}")
m3 = re.search(r'data-last-price="([0-9.]+)"', r2.text)
if m3:
    print(f"S5TH last price: {m3.group(1)}")
    results['S5TH_google'] = m3.group(1)
else:
    print("S5TH price not found")
    url3 = 'https://www.google.com/finance/quote/S5TH:INDEXSP'
    r3 = requests.get(url3, headers=headers, timeout=10)
    m4 = re.search(r'data-last-price="([0-9.]+)"', r3.text)
    if m4:
        print(f"S5TH INDEXSP last price: {m4.group(1)}")
        results['S5TH_google'] = m4.group(1)
    else:
        print("S5TH INDEXSP price not found either")

# 3. Investing.com search result mentioned S5TH = 54.98
print("\n=== Investing.com (from search snippet) ===")
print("S5TH (SP500 above 200MA): 54.98 (from search result snippet, date unknown)")

# 4. Try TradingView widget API
print("\n=== TradingView ===")
tv_url = 'https://api.tradingview.com/v1/symbols/INDEX-NDTH/quote'
try:
    r4 = requests.get(tv_url, headers=headers, timeout=10)
    print(f"TradingView NDTH status: {r4.status_code}")
    if r4.status_code == 200:
        data = r4.json()
        print(f"TradingView NDTH data: {json.dumps(data, indent=2)[:500]}")
except Exception as e:
    print(f"TradingView NDTH error: {e}")

tv_url2 = 'https://api.tradingview.com/v1/symbols/INDEX-S5TH/quote'
try:
    r5 = requests.get(tv_url2, headers=headers, timeout=10)
    print(f"TradingView S5TH status: {r5.status_code}")
    if r5.status_code == 200:
        data2 = r5.json()
        print(f"TradingView S5TH data: {json.dumps(data2, indent=2)[:500]}")
except Exception as e:
    print(f"TradingView S5TH error: {e}")

# 5. Try Barchart API
print("\n=== Barchart ===")
bc_url = 'https://www.barchart.com/stocks/quotes/$NDTH'
try:
    r6 = requests.get(bc_url, headers=headers, timeout=10)
    print(f"Barchart NDTH status: {r6.status_code}")
    # Search for JSON data in page
    m5 = re.search(r'"lastPrice":([0-9.]+)', r6.text)
    if m5:
        print(f"Barchart NDTH lastPrice: {m5.group(1)}")
    m6 = re.search(r'"close":([0-9.]+)', r6.text)
    if m6:
        print(f"Barchart NDTH close: {m6.group(1)}")
except Exception as e:
    print(f"Barchart error: {e}")

# 6. Try MacroMicro
print("\n=== MacroMicro ===")
mm_url = 'https://en.macromicro.me/series/25229/nasdaq100-ma200-breadth'
try:
    r7 = requests.get(mm_url, headers=headers, timeout=10)
    print(f"MacroMicro NDTH status: {r7.status_code}")
except Exception as e:
    print(f"MacroMicro error: {e}")

print("\n=== Summary ===")
print(json.dumps(results, indent=2))
