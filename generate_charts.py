import os
import json
import time
import tempfile
import requests
from strategy_rules import (
    calc_emotion_core,
    calc_rate_shock,
    calc_signal_strength,
    get_target_position,
    get_position_advice,
    get_daily_buy_amount,
    apply_momentum_filter,
)
import re
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path


def get_last_trading_date():
    """获取美股最近一个实际交易日（自动排除周末和节假日）"""
    today = datetime.today()
    for days_back in range(0, 8):
        candidate = today - timedelta(days=days_back)
        if candidate.weekday() >= 5:
            continue
        try:
            spx = yf.Ticker('^GSPC')
            hist = spx.history(start=(candidate - timedelta(days=1)).strftime('%Y-%m-%d'),
                               end=(candidate + timedelta(days=1)).strftime('%Y-%m-%d'))
            if not hist.empty:
                return hist.index[0].strftime('%Y-%m-%d')
        except:
            pass
    return (today - timedelta(days=1)).strftime("%Y-%m-%d")

# Disable yfinance SQLite cache to avoid "unable to open database file" errors
yf.set_tz_cache_location(tempfile.gettempdir())

import sentiment_evaluator_v2 as sentiment_evaluator
import validate_indicators
from fetch_advanced_metrics import AdvancedMetricsFetcher

print("开始运行美股情绪分析...")
print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

advanced_fetcher = AdvancedMetricsFetcher()

def get_nasdaq100_data():
    print("\n正在获取纳斯达克100数据...")
    try:
        ndx = yf.Ticker("^NDX")
        hist = ndx.history(period="max", interval="1d")
        print(f"成功获取 {len(hist)} 天的数据")
        return hist
    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return None

def get_sp500_data():
    print("\n正在获取标普500数据...")
    try:
        spy = yf.Ticker("^GSPC")
        hist = spy.history(period="max", interval="1d")
        print(f"成功获取 {len(hist)} 天的数据")
        return hist
    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return None

def get_vix_data():
    print("\n正在获取VIX恐慌指数数据...")
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="max", interval="1d")
        print(f"成功获取 {len(hist)} 天的数据")
        return hist
    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return None

def analyze_index(data, name):
    if data is None or data.empty:
        print(f"{name} 数据为空")
        return None

    current = round(float(data['Close'].iloc[-1]), 2)
    max_val = round(float(data['High'].max()), 2)
    drawdown = round(((current - max_val) / max_val) * 100, 2)

    ma200_data = data['Close'].rolling(window=200).mean()
    ma200 = round(float(ma200_data.iloc[-1]), 2) if not pd.isna(ma200_data.iloc[-1]) else 0
    ma200_diff = round(((current - ma200) / ma200) * 100, 2) if ma200 > 0 else 0

    ma20_data = data['Close'].rolling(window=20).mean()
    ma20 = round(float(ma20_data.iloc[-1]), 2) if not pd.isna(ma20_data.iloc[-1]) else 0

    return {
        'current': current,
        'high': max_val,
        'drawdown': drawdown,
        'ma200': ma200,
        'ma200_diff': ma200_diff,
        'ma20': ma20,
        'breadth_200ma': 0
    }

def generate_chart(data, vix_data, index_name, vix_name, filename):
    if data is None or data.empty:
        return

    data = data.copy()
    data.index = data.index.tz_localize(None)
    
    if vix_data is not None and not vix_data.empty:
        vix_data = vix_data.copy()
        vix_data.index = vix_data.index.tz_localize(None)

    ten_years_ago = datetime.now() - pd.Timedelta(days=3652)
    data_10y = data[data.index >= ten_years_ago].copy()

    if data_10y.empty:
        return

    max_price = data_10y['Close'].max()
    min_price = data_10y['Close'].min()
    y_range_top = max_price * 1.1
    y_range_bottom = min_price * 0.9 if min_price > 0 else 0

    vix_min = 0
    vix_max = 80

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data_10y.index, y=data_10y['Close'],
        mode='lines', name=index_name,
        line=dict(color='#2563EB', width=1.5),
        hovertemplate='%{y:,.0f}<extra></extra>',
        yaxis='y'
    ))

    if vix_data is not None and not vix_data.empty:
        vix_aligned = vix_data.reindex(data_10y.index, method='ffill')
        vix_aligned = vix_aligned.bfill()
        vix_common = vix_aligned.dropna()
        
        if not vix_common.empty:
            fig.add_trace(go.Scatter(
                x=vix_common.index, y=vix_common['Close'],
                mode='lines', name=vix_name,
                line=dict(color='#EF4444', width=1),
                hovertemplate='%{y:.2f}<extra></extra>',
                yaxis='y2'
            ))

    fig.update_layout(
        title=dict(text=f'{index_name} 与 {vix_name}（近10年）', x=0.02, y=0.98, xanchor='left', yanchor='top', font=dict(size=16, color='#1F2937')),
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation='h', y=1.02, x=1, xanchor='right', yanchor='bottom',
            font=dict(size=12), bgcolor='rgba(255,255,255,0.9)', bordercolor='#E5E7EB', borderwidth=1
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
            range=[vix_min, vix_max]
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
    print(f"{filename} 已生成")

# VIX期限结构历史缓存
def load_vix_term_history():
    path = Path(__file__).parent / "vix_term_history.json"
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_vix_term_history(history):
    path = Path(__file__).parent / "vix_term_history.json"
    with open(path, 'w') as f:
        json.dump(history, f)

# PCR历史数据缓存
def load_pcr_history():
    path = Path(__file__).parent / "pcr_history.json"
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return {
                "qqq": [],
                "spy": []
            }
    return {
        "qqq": [],
        "spy": []
    }

def save_pcr_history(history):
    path = Path(__file__).parent / "pcr_history.json"
    with open(path, 'w') as f:
        json.dump(history, f)

validation_results = validate_indicators.validate_indicators()

buffett_indicator = validation_results.get('buffett_indicator', 158.0)
aaii_bullish = validation_results.get('aaii_bullish', 52.0)
aaii_bearish = validation_results.get('aaii_bearish', 25.0)

if isinstance(aaii_bullish, (int, float)) and isinstance(aaii_bearish, (int, float)):
    aaii_neutral = 100 - aaii_bullish - aaii_bearish
    aaii_sentiment_diff = aaii_bearish - aaii_bullish
else:
    aaii_bullish = 52.0
    aaii_bearish = 25.0
    aaii_neutral = 23.0
    aaii_sentiment_diff = -27.0

print("\n正在读取广度数据...")
breadth_file = Path(__file__).parent / "breadth_data.json"

# 尝试从Barchart实时抓取
barchart_ndth = None
barchart_s5th = None
try:
    bc_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    r_ndth = requests.get('https://www.barchart.com/stocks/quotes/$NDTH', headers=bc_headers, timeout=10)
    if r_ndth.status_code == 200:
        m_ndth = re.search(r'"lastPrice":([0-9.]+)', r_ndth.text)
        if m_ndth:
            barchart_ndth = float(m_ndth.group(1))
            print(f"[OK] Barchart NDTH (纳斯达克100高于200日线): {barchart_ndth:.2f}%")
    r_s5th = requests.get('https://www.barchart.com/stocks/quotes/$S5TH', headers=bc_headers, timeout=10)
    if r_s5th.status_code == 200:
        m_s5th = re.search(r'"lastPrice":([0-9.]+)', r_s5th.text)
        if m_s5th:
            barchart_s5th = float(m_s5th.group(1))
            print(f"[OK] Barchart S5TH (标普500高于200日线): {barchart_s5th:.2f}%")
except Exception as e:
    print(f"[WARN] Barchart抓取失败: {e}")

try:
    if barchart_ndth is not None and barchart_s5th is not None:
        ndx_breadth_200ma = barchart_ndth
        sp500_breadth_200ma = barchart_s5th
        print(f"[OK] 使用Barchart实时数据")
    elif breadth_file.exists():
        with open(breadth_file, 'r', encoding='utf-8') as f:
            breadth_data = json.load(f)
        sp500_breadth_200ma = breadth_data.get('sp500_breadth_200ma', 57.0)
        ndx_breadth_200ma = breadth_data.get('ndx_breadth_200ma', 53.0)
        update_time = breadth_data.get('update_time', 'N/A')
        print(f"[OK] 标普500高于MA200比例: {sp500_breadth_200ma:.2f}%")
        print(f"[OK] 纳斯达克100高于MA200比例: {ndx_breadth_200ma:.2f}%")
        print(f"[OK] 数据更新时间: {update_time}")
    else:
        print("[WARN] breadth_data.json 不存在，使用默认值")
        sp500_breadth_200ma = 57.0
        ndx_breadth_200ma = 53.0
except Exception as e:
    print(f"读取广度数据异常: {e}")
    sp500_breadth_200ma = 57.0
    ndx_breadth_200ma = 53.0

# ========== 获取新指标 ==========
print("\n正在获取新增指标...")

# 获取 PCR 单日数据
qqq_volume_ratio, qqq_oi_ratio = advanced_fetcher.get_qqq_pcr()
spy_volume_ratio, spy_oi_ratio = advanced_fetcher.get_spy_pcr()

# 加载 PCR 历史数据
pcr_history = load_pcr_history()
today_str = get_last_trading_date()

# 更新 QQQ PCR 历史，存储 OI Ratio 用于主信号判断
if qqq_oi_ratio is not None:
    # 检查今天是否已存在数据，存在则跳过（不覆盖，不追加）
    qqq_already_exists = any(entry.get("date") == today_str for entry in pcr_history["qqq"])
    if not qqq_already_exists:
        pcr_history["qqq"].append({
            "date": today_str,
            "oi_ratio": qqq_oi_ratio
        })
        if len(pcr_history["qqq"]) > 20:
            pcr_history["qqq"] = pcr_history["qqq"][-20:]

# 更新 SPY PCR 历史
if spy_oi_ratio is not None:
    # 检查今天是否已存在数据，存在则跳过（不覆盖，不追加）
    spy_already_exists = any(entry.get("date") == today_str for entry in pcr_history["spy"])
    if not spy_already_exists:
        pcr_history["spy"].append({
            "date": today_str,
            "oi_ratio": spy_oi_ratio
        })
        if len(pcr_history["spy"]) > 20:
            pcr_history["spy"] = pcr_history["spy"][-20:]

# 保存历史
save_pcr_history(pcr_history)

# 计算 PCR MA20 和偏离率
qqq_oi_ratio_current = qqq_oi_ratio
qqq_oi_ratio_ma20 = None
qqq_deviation_pct = None
qqq_data_status = "正常"

qqq_valid_oi = [entry["oi_ratio"] for entry in pcr_history["qqq"] if entry.get("oi_ratio") is not None]
qqq_data_count = len(qqq_valid_oi)

if qqq_data_count < 5:
    qqq_data_status = f"数据积累中({qqq_data_count}/20天)"
    qqq_deviation_pct = None
elif 5 <= qqq_data_count < 20:
    qqq_oi_ratio_ma20 = round(sum(qqq_valid_oi) / qqq_data_count, 2)
    qqq_data_status = "参考值，数据不足20天"
    if qqq_oi_ratio_current is not None and qqq_oi_ratio_ma20 > 0:
        qqq_deviation_pct = round(((qqq_oi_ratio_current - qqq_oi_ratio_ma20) / qqq_oi_ratio_ma20) * 100, 1)
else:
    qqq_oi_ratio_ma20 = round(sum(qqq_valid_oi[-20:]) / 20, 2)
    if qqq_oi_ratio_current is not None and qqq_oi_ratio_ma20 > 0:
        qqq_deviation_pct = round(((qqq_oi_ratio_current - qqq_oi_ratio_ma20) / qqq_oi_ratio_ma20) * 100, 1)

spy_oi_ratio_current = spy_oi_ratio
spy_oi_ratio_ma20 = None
spy_deviation_pct = None
spy_data_status = "正常"

spy_valid_oi = [entry["oi_ratio"] for entry in pcr_history["spy"] if entry.get("oi_ratio") is not None]
spy_data_count = len(spy_valid_oi)

if spy_data_count < 5:
    spy_data_status = f"数据积累中({spy_data_count}/20天)"
    spy_deviation_pct = None
elif 5 <= spy_data_count < 20:
    spy_oi_ratio_ma20 = round(sum(spy_valid_oi) / spy_data_count, 2)
    spy_data_status = "参考值，数据不足20天"
    if spy_oi_ratio_current is not None and spy_oi_ratio_ma20 > 0:
        spy_deviation_pct = round(((spy_oi_ratio_current - spy_oi_ratio_ma20) / spy_oi_ratio_ma20) * 100, 1)
else:
    spy_oi_ratio_ma20 = round(sum(spy_valid_oi[-20:]) / 20, 2)
    if spy_oi_ratio_current is not None and spy_oi_ratio_ma20 > 0:
        spy_deviation_pct = round(((spy_oi_ratio_current - spy_oi_ratio_ma20) / spy_oi_ratio_ma20) * 100, 1)

print(f"  QQQ OI Ratio: {qqq_oi_ratio_current}, MA20: {qqq_oi_ratio_ma20}, 偏离: {qqq_deviation_pct}%, 状态: {qqq_data_status}")
print(f"  SPY OI Ratio: {spy_oi_ratio_current}, MA20: {spy_oi_ratio_ma20}, 偏离: {spy_deviation_pct}%, 状态: {spy_data_status}")


on_rrp_current, on_rrp_deviation = advanced_fetcher.get_on_rrp_data()
iwm_spy_ratio, iwm_spy_deviation = advanced_fetcher.get_iwm_spy_ratio()

# 获取基础数据用于计算
nasdaq100_data = get_nasdaq100_data()
sp500_data = get_sp500_data()
vix_data = get_vix_data()
ndx_raw_data = advanced_fetcher._get_yahoo_symbol_data('^NDX')
spx_raw_data = advanced_fetcher._get_yahoo_symbol_data('^GSPC')
ndx_spx_ratio, ndx_spx_deviation = advanced_fetcher.get_ndx_spx_ratio(ndx_raw_data, spx_raw_data)

# VIX期限结构持续性校验
vix_term_ratio = advanced_fetcher.get_vix_term_ratio()
vix_term_history = load_vix_term_history()
if vix_term_ratio is not None:
    # 检查今天是否已存在数据，存在则跳过（不覆盖，不追加）
    vix_term_already_exists = any(entry.get('date') == today_str for entry in vix_term_history)
    if not vix_term_already_exists:
        vix_term_history.append({
            'date': today_str,
            'ratio': vix_term_ratio
        })
        if len(vix_term_history) > 10:
            vix_term_history = vix_term_history[-10:]
        save_vix_term_history(vix_term_history)

vix_term_trigger_days = 0
for entry in vix_term_history[-5:]:
    if entry.get('ratio', 0) > 1.0:
        vix_term_trigger_days += 1
vix_term_valid = vix_term_trigger_days >= 3

# 其他指标
current_vix = validation_results.get('current_vix', 15.0)
credit_spread = None
try:
    credit_spread = advanced_fetcher.get_credit_spread()
except Exception as e:
    print(f"信用利差获取失败: {e}")
tnx_ma50_diff = advanced_fetcher.get_tnx_ma50_diff()

nasdaq100_result = analyze_index(nasdaq100_data, "纳斯达克100")
sp500_result = analyze_index(sp500_data, "标普500")

if nasdaq100_result:
    print(f"\n纳斯达克100分析结果:")
    print(f"  当前: {nasdaq100_result['current']}")
    print(f"  最高: {nasdaq100_result['high']}")
    print(f"  回撤: {nasdaq100_result['drawdown']}%")
    print(f"  MA200差异: {nasdaq100_result['ma200_diff']}%")
    print(f"  广度: {nasdaq100_result['breadth_200ma']}%")

if sp500_result:
    print(f"\n标普500分析结果:")
    print(f"  当前: {sp500_result['current']}")
    print(f"  最高: {sp500_result['high']}")
    print(f"  回撤: {sp500_result['drawdown']}%")
    print(f"  MA200差异: {sp500_result['ma200_diff']}%")
    print(f"  广度: {sp500_result['breadth_200ma']}%")

if nasdaq100_result:
    generate_chart(nasdaq100_data, vix_data, "纳斯达克100", "VIX恐慌指数", "nasdaq100_chart.html")

if sp500_result:
    generate_chart(sp500_data, vix_data, "标普500", "VIX恐慌指数", "sp500_chart.html")

# ========== 核心防线逻辑（调用公共规则库） ==========
nasdaq_drawdown = nasdaq100_result['drawdown'] if nasdaq100_result else 0
spx_drawdown = sp500_result['drawdown'] if sp500_result else 0
is_aaii_valid = (nasdaq_drawdown <= -5) or (spx_drawdown <= -5) or (current_vix >= 20)

is_rate_shock = tnx_ma50_diff is not None and tnx_ma50_diff > 10

nasdaq100_current = nasdaq100_result['current'] if nasdaq100_result else 15000.0
nasdaq100_ma200_diff = nasdaq100_result['ma200_diff'] if nasdaq100_result else 0.0
sp500_current = sp500_result['current'] if sp500_result else 5000.0
sp500_ma200_diff = sp500_result['ma200_diff'] if sp500_result else 0.0

sentiment_analysis, core_triggered = calc_emotion_core(
    ndx_drawdown=nasdaq_drawdown,
    spx_drawdown=spx_drawdown,
    ndx_dev_ma200=nasdaq100_ma200_diff,
    spx_dev_ma200=sp500_ma200_diff,
    vix=current_vix,
    vix_term=vix_term_ratio if vix_term_valid else None,
    credit_spread=credit_spread,
    rate_shock=is_rate_shock,
    ndx_breadth_200ma=ndx_breadth_200ma,
)

# ========== 动量拦截器（策略M核心） ==========
ndx_ma20 = nasdaq100_result['ma20'] if nasdaq100_result else None
final_emotion, momentum_blocked = apply_momentum_filter(sentiment_analysis, nasdaq100_current, ndx_ma20)
if momentum_blocked:
    print(f"\n[动量拦截] 原始情绪={sentiment_analysis}，NDX({nasdaq100_current}) > MA20({ndx_ma20})，降级为中性")
    core_triggered = [("中性", "momentum_blocked")]
sentiment_analysis = final_emotion

# ========== PCR增强逻辑（主页面独有） ==========
sentiment_conditions = []
trigger_dims = set()
pcr_bonus = False

for emotion, indicator in core_triggered:
    if indicator in ('vix', 'vix_term', 'vix_low'):
        trigger_dims.add('volatility')
    elif indicator in ('credit_spread',):
        trigger_dims.add('credit')
    elif indicator in ('ndx_drawdown', 'spx_drawdown', 'ndx_dev_ma200', 'spx_dev_ma200', 'ndx_breadth_200ma'):
        trigger_dims.add('technical')

condition_labels = {
    'vix_term': f"VIX期限结构倒挂(>1.0)，已持续{vix_term_trigger_days}天，极度恐慌" if vix_term_valid and vix_term_trigger_days >= 3 else "VIX期限结构倒挂",
    'vix': f"VIX恐慌指数>{35 if sentiment_analysis == '极度恐慌' else ''}{'在25-35' if sentiment_analysis == '恐慌' else '>35' if sentiment_analysis == '极度恐慌' else ''}",
    'credit_spread': f"高收益债信用利差>{'8%' if sentiment_analysis == '极度恐慌' else '在5.5%-8%' if sentiment_analysis == '恐慌' else '>8%'}",
    'ndx_drawdown': f"纳斯达克100回撤{'>30%' if sentiment_analysis == '极度恐慌' else '在-15%~-30%' if sentiment_analysis == '恐慌' else ''}",
    'spx_drawdown': f"标普500回撤{'>20%' if sentiment_analysis == '极度恐慌' else '在-10%~-20%' if sentiment_analysis == '恐慌' else ''}",
    'ndx_dev_ma200': f"纳指100偏离200日线{'>30%' if sentiment_analysis == '极度贪婪' else '>22%' if sentiment_analysis == '贪婪' else ''}",
    'spx_dev_ma200': f"标普500偏离200日线{'>20%' if sentiment_analysis == '极度贪婪' else '>14%' if sentiment_analysis == '贪婪' else ''}",
    'vix_low': f"VIX<12且纳指偏离200日线{'>25%' if sentiment_analysis == '极度贪婪' else '>18%' if sentiment_analysis == '贪婪' else ''}",
    'ndx_breadth_200ma': f"纳指100高于200日线比例{'<15%' if sentiment_analysis == '极度恐慌' else '在15%-25%' if sentiment_analysis == '恐慌' else ''}",
}

for emotion, indicator in core_triggered:
    label = condition_labels.get(indicator, indicator)
    if '未触发利率冲击' not in label and indicator in ('ndx_drawdown', 'spx_drawdown', 'ndx_breadth_200ma') and not is_rate_shock:
        label += "，未触发利率冲击"
    sentiment_conditions.append(label)

# PCR叠加判断
if sentiment_analysis in ("极度恐慌", "恐慌"):
    if qqq_deviation_pct is not None:
        if sentiment_analysis == "极度恐慌" and qqq_deviation_pct > 70:
            trigger_dims.add('credit')
            sentiment_conditions.append(f"QQQ OI Ratio 偏离+70%（主信号）")
            if spy_deviation_pct is not None and spy_deviation_pct > 40:
                pcr_bonus = True
                sentiment_conditions.append(f"SPY OI Ratio 偏离+40%（辅助确认）")
        elif sentiment_analysis == "恐慌" and 40 < qqq_deviation_pct <= 70:
            trigger_dims.add('credit')
            sentiment_conditions.append(f"QQQ OI Ratio 偏离+40%~+70%（主信号）")
            if spy_deviation_pct is not None and 20 < spy_deviation_pct <= 40:
                pcr_bonus = True
                sentiment_conditions.append(f"SPY OI Ratio 偏离+20%~+40%（辅助确认）")
elif sentiment_analysis in ("极度贪婪", "贪婪"):
    if qqq_deviation_pct is not None:
        if sentiment_analysis == "极度贪婪" and qqq_deviation_pct < -40:
            trigger_dims.add('credit')
            sentiment_conditions.append(f"QQQ OI Ratio 偏离-40%（主信号）")
            if spy_deviation_pct is not None and spy_deviation_pct < -25:
                pcr_bonus = True
                sentiment_conditions.append(f"SPY OI Ratio 偏离-25%（辅助确认）")
        elif sentiment_analysis == "贪婪" and -40 <= qqq_deviation_pct < -25:
            trigger_dims.add('credit')
            sentiment_conditions.append(f"QQQ OI Ratio 偏离-40%~-25%（主信号）")
            if spy_deviation_pct is not None and -40 <= spy_deviation_pct < -20:
                pcr_bonus = True
                sentiment_conditions.append(f"SPY OI Ratio 偏离-40%~-20%（辅助确认）")

# AAII增强（只加分，不独立触发）
aaii_conditions = []
if sentiment_analysis in ("极度恐慌", "恐慌"):
    if not isinstance(aaii_bearish, str) and not isinstance(aaii_bullish, str):
        if sentiment_analysis == "极度恐慌" and aaii_bearish > 50 and is_aaii_valid:
            aaii_conditions.append(f"AAII看空比例>50%")
        elif sentiment_analysis == "恐慌" and 40 < aaii_bearish <= 50 and is_aaii_valid:
            aaii_conditions.append(f"AAII看空比例在40%-50%")
    if not isinstance(aaii_sentiment_diff, str):
        if sentiment_analysis == "极度恐慌" and aaii_sentiment_diff > 35 and is_aaii_valid:
            aaii_conditions.append(f"AAII情绪差(看空-看多)>35%")
        elif sentiment_analysis == "恐慌" and 20 < aaii_sentiment_diff <= 35 and is_aaii_valid:
            aaii_conditions.append(f"AAII情绪差在20%-35%")
elif sentiment_analysis in ("极度贪婪", "贪婪"):
    if not isinstance(aaii_bullish, str):
        if sentiment_analysis == "极度贪婪" and aaii_bullish > 55 and is_aaii_valid:
            aaii_conditions.append(f"AAII看多比例>55%")
        elif sentiment_analysis == "贪婪" and 45 < aaii_bullish <= 55 and is_aaii_valid:
            aaii_conditions.append(f"AAII看多比例在45%-55%")

if aaii_conditions:
    sentiment_conditions.append(f"（AAII确认：{', '.join(aaii_conditions)}）")

# ========== 信号强度（调用公共规则库） ==========
signal_strength, trigger_dims = calc_signal_strength(sentiment_analysis, core_triggered, pcr_bonus)

# ========== 操作建议（调用公共规则库，传入MA200状态） ==========
ndx_above_ma200 = nasdaq100_ma200_diff > 0
target_position = get_target_position(sentiment_analysis, ndx_above_ma200)
current_position = target_position
position_advice = get_position_advice(sentiment_analysis, current_position, target_position, ndx_above_ma200)
daily_buy_amount = get_daily_buy_amount(sentiment_analysis)

print(f"\n最终情绪分析结果: {sentiment_analysis}")
print(f"触发条件: {sentiment_conditions}")
print(f"信号强度: {signal_strength}")
print(f"触发维度: {trigger_dims}")
print(f"PCR叠加: {pcr_bonus}")
print(f"仓位建议: {position_advice}")

# ========== 保存全部数据 ==========
output_dir = os.path.dirname(os.path.abspath(__file__))
market_data_file = os.path.join(output_dir, 'market_data.json')

indicators = {
    'current_vix': current_vix,
    'nasdaq_drawdown': nasdaq_drawdown,
    'sp500_drawdown': spx_drawdown,
    'nasdaq100_drawdown': nasdaq_drawdown,
    'buffett_indicator': buffett_indicator,
    'aaii_bullish': aaii_bullish,
    'aaii_bearish': aaii_bearish,
    'aaii_neutral': aaii_neutral,
    'aaii_sentiment_diff': aaii_sentiment_diff,
    'sentiment_analysis': sentiment_analysis,
    'sentiment_conditions': sentiment_conditions,
    'signal_strength': signal_strength,
    'position_advice': position_advice,
    'target_position': target_position,
    'daily_buy_amount': daily_buy_amount,
    'current_sp500': sp500_current,
    'current_nasdaq100': nasdaq100_current,
    'sp500_high': sp500_result['high'] if sp500_result else 0,
    'nasdaq100_high': nasdaq100_result['high'] if nasdaq100_result else 0,
    'sp500_ma200_diff': sp500_ma200_diff,
    'nasdaq100_ma200_diff': nasdaq100_ma200_diff,
    'sp500_breadth_200ma': sp500_breadth_200ma,
    'ndx_breadth_200ma': ndx_breadth_200ma,
    'sp500_deviation_200ma': sp500_ma200_diff,
    'nasdaq100_deviation_200ma': nasdaq100_ma200_diff,
    'nasdaq100_current': nasdaq100_current,
    'sp500_current': sp500_current,
    'sentiment_result': sentiment_analysis,
    'credit_spread': credit_spread,
    'vix_term_ratio': vix_term_ratio,
    'vix_term_trigger_days': vix_term_trigger_days,
    'tnx_ma50_diff': tnx_ma50_diff,
    'is_aaii_valid': is_aaii_valid,
    'is_rate_shock': is_rate_shock,
    # 新指标
    'qqq_pcr': qqq_oi_ratio_current,
    'qqq_pcr_ma20': qqq_oi_ratio_ma20,
    'qqq_pcr_deviation': qqq_deviation_pct,
    'qqq_pcr_status': qqq_data_status,
    'qqq_volume_ratio': qqq_volume_ratio,
    'spy_pcr': spy_oi_ratio_current,
    'spy_pcr_ma20': spy_oi_ratio_ma20,
    'spy_pcr_deviation': spy_deviation_pct,
    'spy_pcr_status': spy_data_status,
    'spy_volume_ratio': spy_volume_ratio,
    'on_rrp_current': on_rrp_current,
    'on_rrp_deviation': on_rrp_deviation,
    'ndx_spx_ratio': ndx_spx_ratio,
    'ndx_spx_deviation': ndx_spx_deviation,
    'iwm_spy_ratio': iwm_spy_ratio,
    'iwm_spy_deviation': iwm_spy_deviation,
    'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

with open(market_data_file, 'w', encoding='utf-8') as f:
    json.dump(indicators, f, ensure_ascii=False, indent=2)
print(f"\n数据已保存到 {market_data_file}")

market_data_js_file = os.path.join(output_dir, 'market_data.js')
with open(market_data_js_file, 'w', encoding='utf-8') as f:
    f.write('var MARKET_DATA = ')
    f.write(json.dumps(indicators, ensure_ascii=False, indent=2))
    f.write(';')
print(f"已同步生成 {market_data_js_file}")

# ----------------------------
# 每日记录与自动验证逻辑
# ----------------------------

def load_daily_log():
    log_file = Path(__file__).parent / "daily_log.json"
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_daily_log(log_data):
    log_file = Path(__file__).parent / "daily_log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    save_daily_log_to_csv(log_data)
    save_daily_log_to_js(log_data)

def save_daily_log_to_csv(log_data):
    """将 daily_log.json 数据转换为 CSV 格式保存"""
    csv_file = Path(__file__).parent / "daily_log.csv"
    
    if not log_data:
        if csv_file.exists():
            csv_file.unlink()
        return
    
    # 构建扁平化的记录列表
    csv_records = []
    for entry in log_data:
        record = {}
        # 日期
        record['date'] = entry.get('date', '')
        
        # market_data
        market_data = entry.get('market_data', {})
        record['ndx'] = market_data.get('ndx', '')
        record['spx'] = market_data.get('spx', '')
        record['ndx_drawdown'] = market_data.get('ndx_drawdown', '')
        record['spx_drawdown'] = market_data.get('spx_drawdown', '')
        record['ndx_above_ma200'] = market_data.get('ndx_above_ma200', '')
        record['spx_above_ma200'] = market_data.get('spx_above_ma200', '')
        record['ndx_deviation_ma200'] = market_data.get('ndx_deviation_ma200', '')
        record['spx_deviation_ma200'] = market_data.get('spx_deviation_ma200', '')
        record['vix'] = market_data.get('vix', '')
        record['vix_term'] = market_data.get('vix_term', '')
        record['vix_term_days'] = market_data.get('vix_term_days', '')
        record['credit_spread'] = market_data.get('credit_spread', '')
        record['rate_shock'] = market_data.get('rate_shock', '')
        record['aaii_valid'] = market_data.get('aaii_valid', '')
        record['qqq_oi_ratio'] = market_data.get('qqq_oi_ratio', '')
        record['qqq_oi_deviation'] = market_data.get('qqq_oi_deviation', '')
        record['spy_oi_ratio'] = market_data.get('spy_oi_ratio', '')
        record['spy_oi_deviation'] = market_data.get('spy_oi_deviation', '')
        record['on_rrp_deviation'] = market_data.get('on_rrp_deviation', '')
        record['ndx_spx_deviation'] = market_data.get('ndx_spx_deviation', '')
        record['iwm_spy_deviation'] = market_data.get('iwm_spy_deviation', '')
        
        # signal
        signal = entry.get('signal', {})
        record['emotion'] = signal.get('emotion', '')
        record['strength'] = signal.get('strength', '')
        record['triggered_conditions'] = ', '.join(signal.get('triggered_conditions', []))
        record['target_position'] = signal.get('target_position', '')
        record['action'] = signal.get('action', '')
        
        # verify_5d
        verify_5d = entry.get('verify_5d', {})
        record['verify_5d_status'] = verify_5d.get('status', '')
        record['verify_5d_ndx_return'] = verify_5d.get('ndx_return', '')
        record['verify_5d_spx_return'] = verify_5d.get('spx_return', '')
        record['verify_5d_weighted_return'] = verify_5d.get('weighted_return', '')
        record['verify_5d_result'] = verify_5d.get('result', '')
        record['verify_5d_divergence'] = verify_5d.get('divergence', '')
        
        # verify_20d
        verify_20d = entry.get('verify_20d', {})
        record['verify_20d_status'] = verify_20d.get('status', '')
        record['verify_20d_ndx_return'] = verify_20d.get('ndx_return', '')
        record['verify_20d_spx_return'] = verify_20d.get('spx_return', '')
        record['verify_20d_weighted_return'] = verify_20d.get('weighted_return', '')
        record['verify_20d_result'] = verify_20d.get('result', '')
        record['verify_20d_divergence'] = verify_20d.get('divergence', '')
        
        csv_records.append(record)
    
    # 使用 pandas 保存为 CSV
    df = pd.DataFrame(csv_records)
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"已同步更新 {csv_file.name}")

def save_daily_log_to_js(log_data):
    js_file = Path(__file__).parent / "daily_log.js"
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write('var DAILY_LOG_DATA = ')
        f.write(json.dumps(log_data, ensure_ascii=False, indent=2))
        f.write(';')
    print(f"已同步更新 {js_file.name}")

def append_daily_log():
    print("\n--- 保存每日快照 ---")
    log_data = load_daily_log()
    today_str = get_last_trading_date()
    
    # 检查是否已存在今日记录
    existing_dates = [entry.get('date') for entry in log_data if entry.get('date')]
    if today_str in existing_dates:
        print(f"今日 {today_str} 记录已存在，跳过追加")
        return
    
    # 构建记录
    entry = {
        "date": today_str,
        "market_data": {
            "ndx": nasdaq100_result['current'] if nasdaq100_result else 0,
            "spx": sp500_result['current'] if sp500_result else 0,
            "ndx_drawdown": nasdaq100_result['drawdown'] if nasdaq100_result else 0,
            "spx_drawdown": sp500_result['drawdown'] if sp500_result else 0,
            "ndx_above_ma200": ndx_breadth_200ma,
            "spx_above_ma200": sp500_breadth_200ma,
            "ndx_deviation_ma200": nasdaq100_result['ma200_diff'] if nasdaq100_result else 0,
            "spx_deviation_ma200": sp500_result['ma200_diff'] if sp500_result else 0,
            "vix": current_vix,
            "vix_term": vix_term_ratio,
            "vix_term_days": vix_term_trigger_days,
            "credit_spread": credit_spread,
            "rate_shock": is_rate_shock,
            "aaii_valid": is_aaii_valid,
            "qqq_oi_ratio": qqq_oi_ratio_current,
            "qqq_oi_deviation": qqq_deviation_pct,
            "spy_oi_ratio": spy_oi_ratio_current,
            "spy_oi_deviation": spy_deviation_pct,
            "on_rrp_deviation": on_rrp_deviation,
            "ndx_spx_deviation": ndx_spx_deviation,
            "iwm_spy_deviation": iwm_spy_deviation
        },
        "signal": {
            "emotion": sentiment_analysis,
            "strength": signal_strength,
            "triggered_conditions": sentiment_conditions,
            "target_position": position_advice.split(' / ')[0].replace('目标仓位 ', ''),
            "action": position_advice.split(' / ')[2] if len(position_advice.split(' / ')) > 2 else position_advice
        },
        "verify_5d": {
            "status": "pending",
            "ndx_return": None,
            "spx_return": None,
            "weighted_return": None,
            "result": None,
            "divergence": None
        },
        "verify_20d": {
            "status": "pending",
            "ndx_return": None,
            "spx_return": None,
            "weighted_return": None,
            "result": None,
            "divergence": None
        }
    }
    
    log_data.append(entry)
    save_daily_log(log_data)
    print(f"已保存 {today_str} 快照到 daily_log.json")

def auto_verify_logs():
    print("\n--- 自动验证历史信号 ---")
    log_data = load_daily_log()
    if not log_data:
        print("无历史记录可验证")
        return
    
    # 获取 NDX 和 SPX 历史数据
    ndx_data = None
    spx_data = None
    try:
        ndx_ticker = yf.Ticker('^NDX')
        ndx_hist = ndx_ticker.history(period='5y', interval='1d')
        ndx_data = ndx_hist[['Close']].copy()
        ndx_data.index = ndx_data.index.tz_localize(None)
        
        spx_ticker = yf.Ticker('^GSPC')
        spx_hist = spx_ticker.history(period='5y', interval='1d')
        spx_data = spx_hist[['Close']].copy()
        spx_data.index = spx_data.index.tz_localize(None)
    except Exception as e:
        print(f"获取历史数据失败: {e}")
        return
    
    # 统一索引，只保留两者都有的交易日
    if ndx_data is not None and spx_data is not None:
        common_dates = ndx_data.index.intersection(spx_data.index)
        ndx_data = ndx_data.loc[common_dates]
        spx_data = spx_data.loc[common_dates]
    
    modified = False
    
    for entry in log_data:
        signal_date_str = entry.get('date')
        if not signal_date_str:
            continue
        
        try:
            signal_date = datetime.strptime(signal_date_str, '%Y-%m-%d').date()
        except:
            continue
        
        # 验证 5d
        if entry.get('verify_5d', {}).get('status') == 'pending':
            result = verify_single_entry(entry, ndx_data, spx_data, signal_date, days=5)
            if result:
                entry['verify_5d'] = result
                modified = True
                print(f"[5d] 验证完成: {signal_date_str}")
        
        # 验证 20d
        if entry.get('verify_20d', {}).get('status') == 'pending':
            result = verify_single_entry(entry, ndx_data, spx_data, signal_date, days=20)
            if result:
                entry['verify_20d'] = result
                modified = True
                print(f"[20d] 验证完成: {signal_date_str}")
    
    if modified:
        save_daily_log(log_data)
        print("验证结果已保存")
    else:
        print("无待验证记录")

def verify_single_entry(entry, ndx_data, spx_data, signal_date, days):
    if ndx_data is None or spx_data is None:
        return None
    
    # 找到信号日在历史数据中的位置
    signal_date_dt = datetime.combine(signal_date, datetime.min.time())
    if signal_date_dt not in ndx_data.index:
        # 如果信号日不在数据中，尝试找前一个交易日
        valid_dates = ndx_data.index[ndx_data.index <= signal_date_dt]
        if len(valid_dates) == 0:
            return None
        signal_date_dt = valid_dates[-1]
    
    signal_idx = ndx_data.index.get_loc(signal_date_dt)
    target_idx = signal_idx + days
    
    if target_idx >= len(ndx_data):
        # 还不足 days 个交易日
        return None
    
    # 提取价格
    ndx_signal = float(ndx_data.iloc[signal_idx]['Close'])
    ndx_target = float(ndx_data.iloc[target_idx]['Close'])
    spx_signal = float(spx_data.iloc[signal_idx]['Close'])
    spx_target = float(spx_data.iloc[target_idx]['Close'])
    
    # 计算涨跌幅
    ndx_return = ((ndx_target - ndx_signal) / ndx_signal) * 100
    spx_return = ((spx_target - spx_signal) / spx_signal) * 100
    weighted_return = ndx_return * 0.75 + spx_return * 0.25
    
    # 判定结果
    emotion = entry.get('signal', {}).get('emotion', '')
    if emotion in ['恐慌', '极度恐慌']:
        if weighted_return > 3:
            verify_result = 'correct'
        elif weighted_return < -3:
            verify_result = 'wrong'
        else:
            verify_result = 'neutral'
    elif emotion in ['贪婪', '极度贪婪']:
        if weighted_return < -3:
            verify_result = 'correct'
        elif weighted_return > 3:
            verify_result = 'wrong'
        else:
            verify_result = 'neutral'
    else:  # 中性
        if -5 <= weighted_return <= 5:
            verify_result = 'correct'
        else:
            verify_result = 'wrong'
    
    # 背离标注
    if (ndx_return > spx_return + 3):
        divergence = '科技领涨'
    elif (spx_return > ndx_return + 3):
        divergence = '价值领涨'
    elif ((ndx_return > 0 and spx_return < 0) or (ndx_return < 0 and spx_return > 0)):
        divergence = '指数分化'
    else:
        divergence = '同步运行'
    
    return {
        "status": "verified",
        "ndx_return": round(ndx_return, 2),
        "spx_return": round(spx_return, 2),
        "weighted_return": round(weighted_return, 2),
        "result": verify_result,
        "divergence": divergence
    }

# 执行每日记录和验证
append_daily_log()
auto_verify_logs()
