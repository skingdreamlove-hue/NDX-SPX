
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import sys

print("=== 只运行图表生成 ===")

# 获取数据
print("获取纳斯达克100...")
ndx = yf.Ticker("^NDX")
ndx_hist = ndx.history(period="max", interval="1d")

print("获取VIX...")
vix = yf.Ticker("^VIX")
vix_hist = vix.history(period="max", interval="1d")

# 处理时区
ndx_hist.index = ndx_hist.index.tz_localize(None)
vix_hist.index = vix_hist.index.tz_localize(None)

# 10年范围
ten_years_ago = datetime.now() - timedelta(days=3652)
data_10y = ndx_hist[ndx_hist.index >= ten_years_ago].copy()
vix_10y = vix_hist[vix_hist.index >= ten_years_ago].copy()

print(f"数据长度: {len(data_10y)} 纳斯达克, {len(vix_10y)} VIX")

fig = go.Figure()

# 纳斯达克线
fig.add_trace(go.Scatter(
    x=data_10y.index, y=data_10y['Close'],
    mode='lines', name="纳斯达克100",
    line=dict(color='#2563EB', width=1.5),
))

# VIX线
print("处理VIX对齐...")
vix_aligned = vix_hist.reindex(data_10y.index, method='ffill')
vix_aligned = vix_aligned.bfill()
vix_common = vix_aligned.dropna()
print(f"VIX对齐后: {len(vix_common)}")

if not vix_common.empty:
    print("添加VIX线...")
    fig.add_trace(go.Scatter(
        x=vix_common.index, y=vix_common['Close'],
        mode='lines', name="VIX恐慌指数",
        line=dict(color='#EF4444', width=1),
        yaxis='y2'
    ))

fig.update_layout(
    title="纳斯达克100 与 VIX恐慌指数（近10年）",
    template='plotly_white',
    yaxis=dict(side='left'),
    yaxis2=dict(side='right', overlaying='y', range=[0, 80]),
    showlegend=True
)

fig.write_html("nasdaq100_chart.html", include_plotlyjs='cdn', full_html=True)
print("nasdaq100_chart.html 保存完毕！")
print("现在验证图表文件...")

with open("nasdaq100_chart.html", 'r', encoding='utf-8') as f:
    content = f.read()
    if "VIX恐慌指数" in content:
        print("✅ 成功：图表包含 VIX恐慌指数！")
    else:
        print("❌ 失败：图表没有找到 VIX恐慌指数")
