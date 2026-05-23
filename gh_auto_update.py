#!/usr/bin/env python3
"""
GitHub Actions Auto Update — 美股情绪监测数据自动抓取
在 GitHub Actions 中定时运行，自动更新 market_data.js 供手机页面使用。
"""
import os, sys, json
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import yfinance as yf
import pandas as pd
import numpy as np

# ── 导入策略规则 ──
from strategy_rules import (
    calc_emotion_core, calc_signal_strength,
    get_target_position, get_position_advice,
    get_daily_buy_amount, apply_momentum_filter
)

yf.set_tz_cache_location("/tmp/yfinance_cache")


def safe(data, *keys):
    """安全地链式取值"""
    for k in keys:
        if data is None:
            return None
        try:
            data = data[k]
        except (KeyError, IndexError, TypeError):
            return None
    return data


def fetch_index_data(ticker, period="2y"):
    """获取指数历史数据"""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        if hist.empty:
            print(f"  [WARN] {ticker} 无数据")
            return None
        closes = hist["Close"].dropna().values
        return {
            "current": float(closes[-1]),
            "high": float(hist["High"].max()),
            "closes": [round(float(c), 2) for c in closes],
        }
    except Exception as e:
        print(f"  [FAIL] {ticker}: {e}")
        return None


def compute_ma200_dev(current, closes):
    if len(closes) < 200:
        return None
    ma200 = float(np.mean(closes[-200:]))
    if ma200 == 0:
        return None
    return round((current - ma200) / ma200 * 100, 2)


def compute_drawdown(current, high):
    if high == 0:
        return None
    return round((current - high) / high * 100, 2)


def compute_ma50_dev(current, closes):
    if len(closes) < 50:
        return None
    ma50 = float(np.mean(closes[-50:]))
    if ma50 == 0:
        return None
    return round((current - ma50) / ma50 * 100, 2)


def main():
    print(f"=== GitHub Actions Auto Update ===")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ── 1. 获取基础指数数据 ──
    print(">>> 获取指数数据...")
    ndx = fetch_index_data("^NDX", "2y")
    gspc = fetch_index_data("^GSPC", "2y")
    vix_data = fetch_index_data("^VIX", "1y")
    vix3m_data = fetch_index_data("^VIX3M", "1y")
    tnx_data = fetch_index_data("^TNX", "1y")
    qqq_data = fetch_index_data("QQQ", "1y")
    spy_data = fetch_index_data("SPY", "1y")
    iwm_data = fetch_index_data("IWM", "1y")

    # ── 2. 计算核心指标 ──
    print()
    print(">>> 计算核心指标...")

    # NDX
    ndx_price = ndx["current"] if ndx else (qqq_data["current"] * 10 if qqq_data else None)
    ndx_high = ndx["high"] if ndx else None
    ndx_drawdown = compute_drawdown(ndx_price, ndx_high) if ndx else None
    ndx_dev_ma200 = compute_ma200_dev(ndx_price, ndx["closes"]) if ndx else None
    ndx_ma20 = float(np.mean(ndx["closes"][-20:])) if ndx and len(ndx["closes"]) >= 20 else None
    print(f"  NDX: {ndx_price}, 回撤: {ndx_drawdown}%, MA200偏离: {ndx_dev_ma200}%")

    # SPX
    spx_price = gspc["current"] if gspc else (spy_data["current"] if spy_data else None)
    spx_high = gspc["high"] if gspc else None
    spx_drawdown = compute_drawdown(spx_price, spx_high) if gspc else None
    spx_dev_ma200 = compute_ma200_dev(spx_price, gspc["closes"]) if gspc else None
    print(f"  SPX: {spx_price}, 回撤: {spx_drawdown}%, MA200偏离: {spx_dev_ma200}%")

    # VIX
    vix = vix_data["current"] if vix_data else None
    vix_term = (vix_data["current"] / vix3m_data["current"]) if (vix_data and vix3m_data and vix3m_data["current"]) else None
    print(f"  VIX: {vix}, VIX期限比: {vix_term}")

    # TNX
    tnx_current = tnx_data["current"] if tnx_data else None
    tnx_ma50_diff = compute_ma50_dev(tnx_current, tnx_data["closes"]) if tnx_data else None
    is_rate_shock = tnx_ma50_diff is not None and tnx_ma50_diff > 10
    print(f"  TNX: {tnx_current}, MA50偏离: {tnx_ma50_diff}%")

    # NDX/SPX Ratio
    ndx_spx_ratio = round(spx_price / ndx_price, 4) if (ndx_price and spx_price) else None
    print(f"  NDX/SPX: {ndx_spx_ratio}")

    # IWM/SPY
    iwm_price = iwm_data["current"] if iwm_data else None
    iwm_spy_ratio = round(iwm_price / spx_price, 4) if (iwm_price and spx_price) else None
    print(f"  IWM/SPX: {iwm_spy_ratio}")

    # ── 3. 情绪计算 ──
    print()
    print(">>> 情绪计算...")
    emotion, triggered = calc_emotion_core(
        ndx_drawdown=ndx_drawdown,
        spx_drawdown=spx_drawdown,
        ndx_dev_ma200=ndx_dev_ma200,
        spx_dev_ma200=spx_dev_ma200,
        vix=vix,
        vix_term=vix_term,
        credit_spread=None,
        rate_shock=is_rate_shock,
        ndx_breadth_200ma=None,
    )
    print(f"  原始情绪: {emotion}, 触发: {triggered}")

    # 动量拦截
    final_emotion, momentum_blocked = apply_momentum_filter(emotion, ndx_price, ndx_ma20)
    if momentum_blocked:
        print(f"  [动量拦截] NDX({ndx_price}) > MA20({ndx_ma20}), 降级为中性")
        emotion = "中性"
        triggered = [("中性", "momentum_blocked")]

    # 信号强度
    strength, _ = calc_signal_strength(emotion, triggered, False)

    # 仓位建议
    ndx_above_ma200 = ndx_dev_ma200 is not None and ndx_dev_ma200 > 0
    target_pos = get_target_position(emotion, ndx_above_ma200)
    pos_advice = get_position_advice(emotion, 100, target_pos, ndx_above_ma200)
    daily_buy = get_daily_buy_amount(emotion)

    print(f"  最终情绪: {emotion}")
    print(f"  信号强度: {strength}")
    print(f"  目标仓位: {target_pos}%")
    print(f"  操作建议: {pos_advice}")

    # ── 4. 构建输出数据 ──
    print()
    print(">>> 保存数据...")

    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    indicators = {
        "current_vix": vix,
        "nasdaq100_drawdown": ndx_drawdown,
        "sp500_drawdown": spx_drawdown,
        "sentiment_analysis": emotion,
        "sentiment_conditions": [],
        "signal_strength": strength,
        "position_advice": pos_advice,
        "target_position": target_pos,
        "daily_buy_amount": daily_buy,
        "current_sp500": spx_price,
        "current_nasdaq100": ndx_price,
        "sp500_high": spx_high,
        "nasdaq100_high": ndx_high,
        "sp500_deviation_200ma": spx_dev_ma200,
        "nasdaq100_deviation_200ma": ndx_dev_ma200,
        "sentiment_result": emotion,
        "vix_term_ratio": vix_term,
        "tnx_ma50_diff": tnx_ma50_diff,
        "is_rate_shock": is_rate_shock,
        "ndx_spx_ratio": ndx_spx_ratio,
        "iwm_spy_ratio": iwm_spy_ratio,
        "is_aaii_valid": False,
        "credit_spread": None,
        "qqq_pcr": None,
        "spy_pcr": None,
        "on_rrp_current": None,
        "on_rrp_deviation": None,
        "sp500_breadth_200ma": None,
        "ndx_breadth_200ma": None,
        "last_update": last_update,
    }

    # 写入 market_data.json（用于 export_mobile_data.py）
    json_path = BASE_DIR / "market_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(indicators, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {json_path}")

    # 写入 market_data.js
    js_path = BASE_DIR / "market_data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("var MARKET_DATA = ")
        json.dump(indicators, f, ensure_ascii=False, indent=2)
        f.write(";\n")
    print(f"  [OK] {js_path}")

    # 写入 docs/market_data.js
    docs_js_path = BASE_DIR / "docs" / "market_data.js"
    with open(docs_js_path, "w", encoding="utf-8") as f:
        f.write("var MARKET_DATA = ")
        json.dump(indicators, f, ensure_ascii=False, indent=2)
        f.write(";\n")
    print(f"  [OK] {docs_js_path}")

    # 写入 docs/data/latest.json
    mobile_data = {
        "_generated": last_update,
        "sentiment": {
            "level": emotion,
            "strength": strength,
            "conditions": [],
        },
        "position": {
            "advice": pos_advice,
            "target": target_pos,
            "daily_buy": daily_buy,
        },
        "indices": {
            "nasdaq100": ndx_price,
            "sp500": spx_price,
            "nasdaq100_drawdown": ndx_drawdown,
            "sp500_drawdown": spx_drawdown,
            "nasdaq100_dev_ma200": ndx_dev_ma200,
            "sp500_dev_ma200": spx_dev_ma200,
        },
        "indicators": {
            "vix": vix,
            "vix_term_ratio": vix_term,
            "tnx_ma50_diff": tnx_ma50_diff,
            "ndx_spx_ratio": ndx_spx_ratio,
            "iwm_spy_ratio": iwm_spy_ratio,
        },
        "last_update": last_update,
    }

    mobile_dir = BASE_DIR / "docs" / "data"
    mobile_dir.mkdir(parents=True, exist_ok=True)
    mobile_path = mobile_dir / "latest.json"
    with open(mobile_path, "w", encoding="utf-8") as f:
        json.dump(mobile_data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {mobile_path}")

    print()
    print(f"=== 完成: {last_update} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
