
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

print("Testing chart generation...")

nasdaq = yf.Ticker("^NDX")
nasdaq_hist = nasdaq.history(period="max", interval="1d")
print(f"NASDAQ data: {len(nasdaq_hist)}")

vix = yf.Ticker("^VIX")
vix_hist = vix.history(period="max", interval="1d")
print(f"VIX data: {len(vix_hist)}")

nasdaq_hist = nasdaq_hist.copy()
nasdaq_hist.index = nasdaq_hist.index.tz_localize(None)
vix_hist = vix_hist.copy()
vix_hist.index = vix_hist.index.tz_localize(None)

ten_years_ago = datetime.now() - timedelta(days=3652)

data_10y = nasdaq_hist[nasdaq_hist.index >= ten_years_ago].copy()
vix_10y = vix_hist[vix_hist.index >= ten_years_ago].copy()

print(f"Data 10y len: {len(data_10y)}")
print(f"VIX 10y len: {len(vix_10y)}")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=data_10y.index, y=data_10y['Close'],
    mode='lines', name="纳斯达克100",
    line=dict(color='#2563EB', width=1.5),
))

if vix_aligned = vix_hist.reindex(data_10y.index, method='ffill')
vix_aligned = vix_aligned.bfill()
vix_common = vix_aligned.dropna()
print(f"VIX common len: {len(vix_common)}")

if not vix_common.empty:
    print("Adding VIX trace...")
    fig.add_trace(go.Scatter(
        x=vix_common.index, y=vix_common['Close'],
        mode='lines', name="VIX恐慌指数",
        line=dict(color='#EF4444', width=1),
        yaxis='y2'
    ))

fig.write_html("test_chart.html")
print("test_chart.html saved!")
