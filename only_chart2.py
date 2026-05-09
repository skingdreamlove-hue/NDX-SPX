
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import sys

print("=== 只运行图表生成 ===")

ndx = yf.Ticker("^NDX")
ndx_hist = ndx.history(period="max", interval="1d")

vix = yf.Ticker("^VIX")
vix_hist = vix.history(period="max", interval="1d")

ndx_hist.index = ndx_hist.index.tz_localize(None)
vix_hist.index = vix_hist.index.tz_localize(None)

ten_years_ago = datetime.now() - timedelta(days=3652)
data_10y = ndx_hist[ndx_hist.index >= ten_years_ago].copy()
vix_10y = vix_hist[vix_hist.index >= ten_years_ago].copy()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=data_10y.index, y=data_10y['Close'],
    mode='lines', name="NASDAQ100",
    line=dict(color='#2563EB', width=1.5),
))

vix_aligned = vix_hist.reindex(data_10y.index, method='ffill')
vix_aligned = vix_aligned.bfill()
vix_common = vix_aligned.dropna()

if not vix_common.empty:
    fig.add_trace(go.Scatter(
        x=vix_common.index, y=vix_common['Close'],
        mode='lines', name="VIX",
        line=dict(color='#EF4444', width=1),
        yaxis='y2'
    ))

print(f"Total traces in fig: {len(fig.data)}")
for i, t in enumerate(fig.data):
    print(f"  Trace {i}: {t.name}, {len(t.x)} points")

fig.write_html("nasdaq100_chart.html", include_plotlyjs='cdn', full_html=True)
print("nasdaq100_chart.html saved!")

import json
# 检查HTML
with open("nasdaq100_chart.html", 'r', encoding='utf-8') as f:
    content = f.read()
    if "VIX" in content:
        print("✅ VIX FOUND in chart")
    else:
        print("❌ NO VIX in chart")
    if "NASDAQ100" in content:
        print("✅ NASDAQ100 FOUND in chart")
