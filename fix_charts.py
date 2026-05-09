
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import sys

print("=== Fixing both charts ===\n")

def make_chart(index_ticker, index_name, filename):
    print(f"Generating {filename}...")
    ndx = yf.Ticker(index_ticker)
    ndx_hist = ndx.history(period="max", interval="1d")
    vix = yf.Ticker("^VIX")
    vix_hist = vix.history(period="max", interval="1d")
    ndx_hist.index = ndx_hist.index.tz_localize(None)
    vix_hist.index = vix_hist.index.tz_localize(None)
    ten_years_ago = datetime.now() - timedelta(days=3652)
    data_10y = ndx_hist[ndx_hist.index >= ten_years_ago].copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data_10y.index, y=data_10y['Close'],
        mode='lines', name=index_name,
        line=dict(color='#2563EB', width=1.5),
    ))
    vix_aligned = vix_hist.reindex(data_10y.index, method='ffill')
    vix_aligned = vix_aligned.bfill()
    vix_common = vix_aligned.dropna()
    if not vix_common.empty:
        fig.add_trace(go.Scatter(
            x=vix_common.index, y=vix_common['Close'],
            mode='lines', name="VIX恐慌指数",
            line=dict(color='#EF4444', width=1),
            yaxis='y2'
        ))
    max_price = data_10y['Close'].max()
    min_price = data_10y['Close'].min()
    y_range_top = max_price * 1.1
    y_range_bottom = min_price * 0.9 if min_price > 0 else 0
    fig.update_layout(
        title=dict(text=f'{index_name} 与 VIX恐慌指数（近10年）', x=0.02, y=0.98, 
                   xanchor='left', yanchor='top', 
                   font=dict(size=16, color='#1F2937')),
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation='h', y=1.02, x=1, xanchor='right', yanchor='bottom',
            font=dict(size=12), bgcolor='rgba(255,255,255,0.9)', 
            bordercolor='#E5E7EB', borderwidth=1
        ),
        margin=dict(l=70, r=70, t=60, b=40),
        height=500,
        hovermode='x',
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
        autosize=True,
        yaxis=dict(
            title_text='',
            tickfont=dict(size=12, color='#2563EB'),
            tickformat=',.0f',
            gridcolor='#E5E7EB',
            gridwidth=1,
            griddash='dash',
            showgrid=True,
            side='left',
            zeroline=False,
            range=[y_range_bottom, y_range_top]
        ),
        yaxis2=dict(
            title_text='',
            tickfont=dict(size=12, color='#EF4444'),
            tickformat='.2f',
            gridcolor='rgba(0,0,0,0)',
            showgrid=False,
            side='right',
            overlaying='y',
            zeroline=False,
            range=[0, 80]
        )
    )
    fig.update_xaxes(
        tickfont=dict(size=11, color='#6B7280'),
        tickformat='%Y-%m-%d',
        showgrid=False,
        zeroline=False,
        showspikes=True,
        spikecolor='black',
        spikethickness=2,
        spikedash='dash',
        spikemode='across',
        spikesnap='cursor'
    )
    fig.write_html(filename, include_plotlyjs='cdn', full_html=True)
    print(f"✅ {filename} saved!")

make_chart("^NDX", "纳斯达克100", "nasdaq100_chart.html")
make_chart("^GSPC", "标普500", "sp500_chart.html")

print("\n✅ All charts fixed!")
