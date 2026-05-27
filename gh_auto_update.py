#!/usr/bin/env python3
"""
GitHub Actions Auto Update — 美股情绪监测数据自动抓取
在 GitHub Actions 中定时运行，自动更新 market_data.js 供手机页面使用。
"""
import os, sys, json, re
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import requests
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
    ndx_spx_ratio = round(ndx_price / spx_price, 4) if (ndx_price and spx_price) else None
    print(f"  NDX/SPX: {ndx_spx_ratio}")

    # IWM/SPY
    iwm_price = iwm_data["current"] if iwm_data else None
    spy_price = spy_data["current"] if spy_data else None
    iwm_spy_ratio = round(iwm_price / spy_price, 4) if (iwm_price and spy_price) else None
    print(f"  IWM/SPY: {iwm_spy_ratio}")

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

    # ── 先保存 daily_log.json ──
    today_str = datetime.now().strftime("%Y-%m-%d")
    daily_log_path = BASE_DIR / "daily_log.json"
    existing_logs = []
    if daily_log_path.exists():
        try:
            with open(daily_log_path, "r", encoding="utf-8") as f:
                existing_logs = json.load(f)
        except Exception:
            pass
    if not isinstance(existing_logs, list):
        existing_logs = []
    entry_exists = existing_logs and existing_logs[-1].get("date") == today_str
    daily_log_entry = {
        "date": today_str,
        "market_data": {
            "ndx": ndx_price, "spx": spx_price,
            "ndx_drawdown": ndx_drawdown, "spx_drawdown": spx_drawdown,
            "ndx_deviation_ma200": ndx_dev_ma200, "spx_deviation_ma200": spx_dev_ma200,
            "vix": vix, "vix_term": vix_term, "vix_term_days": 0,
            "rate_shock": is_rate_shock,
            "ndx_spx_deviation": ndx_spx_ratio, "iwm_spy_deviation": iwm_spy_ratio,
        },
        "signal": {
            "emotion": emotion, "strength": strength,
            "triggered_conditions": [],
            "target_position": "{}%".format(target_pos), "action": pos_advice,
        },
    }
    if not entry_exists:
        existing_logs.append(daily_log_entry)
        with open(daily_log_path, "w", encoding="utf-8") as f:
            json.dump(existing_logs, f, ensure_ascii=False, indent=2)
        print("  [OK] daily_log.json 新增 {}".format(today_str))
    else:
        print("  [-] daily_log.json {} 已存在".format(today_str))

    # ── 构建 recent_signals（包含今天的数据）──
    recent_signals = []
    try:
        with open(daily_log_path, "r", encoding="utf-8") as f:
            updated_logs = json.load(f)
        for entry in updated_logs[-10:]:
            signal = entry.get("signal", {})
            recent_signals.append({
                "date": entry.get("date", ""),
                "emotion": signal.get("emotion", ""),
                "position": signal.get("target_position", ""),
                "action": signal.get("action", ""),
            })
    except Exception:
        pass

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

    # 写入 docs/data/latest.json（同时输出扁平格式供手机页面消费）
    mobile_data = {
        "_generated": last_update,
        # 扁平字段（手机页面直接使用）
        "sentiment_result": emotion,
        "signal_strength": strength,
        "sentiment_conditions": [],
        "position_advice": pos_advice,
        "target_position": target_pos,
        "daily_buy_amount": daily_buy,
        "current_vix": vix,
        "vix_term_ratio": vix_term,
        "current_nasdaq100": ndx_price,
        "current_sp500": spx_price,
        "nasdaq100_drawdown": ndx_drawdown,
        "sp500_drawdown": spx_drawdown,
        "nasdaq100_dev_ma200": ndx_dev_ma200,
        "sp500_dev_ma200": spx_dev_ma200,
        "ndx_spx_ratio": ndx_spx_ratio,
        "iwm_spy_ratio": iwm_spy_ratio,
        "tnx_ma50_diff": tnx_ma50_diff,
        "rate_shock": is_rate_shock,
        "is_live": False,
        "last_update": last_update,
        # 嵌套结构（兼容 export_mobile_data.py 格式）
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
        # 历史记录
        "recent_signals": recent_signals,
    }

    mobile_dir = BASE_DIR / "docs" / "data"
    mobile_dir.mkdir(parents=True, exist_ok=True)
    mobile_path = mobile_dir / "latest.json"
    with open(mobile_path, "w", encoding="utf-8") as f:
        json.dump(mobile_data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {mobile_path}")

    # ── 同步 root real_fund_data.json ──
    fund_src = FUND_STATUS_FILE
    fund_dst = BASE_DIR / "real_fund_data.json"
    if fund_src.exists():
        try:
            with open(fund_src, "r", encoding="utf-8") as f:
                src_data = json.load(f)
            with open(fund_dst, "w", encoding="utf-8") as f:
                json.dump(src_data, f, ensure_ascii=False, indent=2)
            print(f"  [OK] 同步 root/real_fund_data.json ({len(src_data)} 条)")
        except Exception as e:
            print(f"  [WARN] 同步 root/real_fund_data.json 失败: {e}")

    # ── 5. 更新基金申购状态 ──
    update_fund_status()

    print()
    print(f"=== 完成: {last_update} ===")
    return 0


# ════════════════════════════════════════════════════════
#  基金申购状态自动更新（从天天基金网爬取）
# ════════════════════════════════════════════════════════

FUND_STATUS_FILE = BASE_DIR / "docs" / "data" / "real_fund_data.json"

# 基金列表（代码、期望的分类）
FUND_LIST = [
    # 纳斯达克100
    ("270042", "nasdaq"), ("040046", "nasdaq"), ("018043", "nasdaq"),
    ("016532", "nasdaq"), ("000834", "nasdaq"), ("160213", "nasdaq"),
    ("016452", "nasdaq"), ("019547", "nasdaq"), ("016055", "nasdaq"),
    ("539001", "nasdaq"), ("019524", "nasdaq"), ("161130", "nasdaq"),
    ("018966", "nasdaq"), ("019172", "nasdaq"), ("019736", "nasdaq"),
    ("019441", "nasdaq"), ("015299", "nasdaq"),
    # C 类
    ("006479", "nasdaq"), ("014978", "nasdaq"), ("018044", "nasdaq"),
    ("016453", "nasdaq"), ("008971", "nasdaq"), ("016533", "nasdaq"),
    ("016057", "nasdaq"), ("012752", "nasdaq"), ("019525", "nasdaq"),
    ("018967", "nasdaq"), ("019173", "nasdaq"), ("019737", "nasdaq"),
    ("019442", "nasdaq"), ("015300", "nasdaq"), ("019548", "nasdaq"),
    ("012870", "nasdaq"),
    # 标普500
    ("050025", "sp500"), ("017641", "sp500"), ("161125", "sp500"),
    ("017028", "sp500"), ("006075", "sp500"), ("019305", "sp500"),
    ("012860", "sp500"), ("017030", "sp500"), ("018064", "sp500"),
    ("018065", "sp500"),
]


def fetch_fund_page_status(code):
    """从天天基金网单个基金页面抓取申购状态"""
    url = f"https://fund.eastmoney.com/{code}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://fund.eastmoney.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = "utf-8"
        html = resp.text
        import re

        status_text = None
        limit_raw = None

        # 查找 交易状态 到 开放赎回/暂停赎回 之间的文本
        m = re.search(
            r'交易状态[：:]\s*(.+?)(?:开放赎回|暂停赎回)',
            html, re.DOTALL
        )
        if m:
            raw = m.group(1).strip()
            raw = re.sub(r'<[^>]+>', '', raw).strip()
            status_text = raw
        else:
            # 回退：找 申购状态
            m = re.search(
                r'申购状态[：:]\s*(.+?)(?:<|$)',
                html, re.DOTALL
            )
            if m:
                raw = m.group(1).strip()
                raw = re.sub(r'<[^>]+>', '', raw).strip()
                status_text = raw

        if not status_text:
            return None, None

        # 提取限购额度
        lm = re.search(r'单日累计购买上限[：:]?\s*([^<\n\r]+?)(?:<|\n|\r|$)', html)
        if lm:
            limit_raw = lm.group(1).strip()

        full_status = status_text
        if limit_raw:
            full_status = f"{status_text} (单日累计购买上限{limit_raw})"

        return status_text, full_status
    except Exception as e:
        print(f"    [FAIL] {code}: {e}")
        return None, None

def load_existing_fund_data():
    """读取现有的基金数据文件"""
    if FUND_STATUS_FILE.exists():
        try:
            with open(FUND_STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  [WARN] 读取现有基金数据失败: {e}")
    # 如果没有现有文件，创建默认数据结构
    data = []
    for code, category in FUND_LIST:
        data.append({
            "基金代码": code,
            "基金名称": "",
            "类型": "A" if code not in [
                "006479", "014978", "018044", "016453", "008971",
                "016533", "016057", "012752", "019525", "018967",
                "019173", "019737", "019442", "015300", "019548",
                "012870", "006075", "019305", "012860", "017030",
                "018065",
            ] else "C",
            "最新净值": "--",
            "日涨跌幅": "--",
            "净值日期": "N/A",
            "交易状态": "暂停申购",
            "购买手续费": "--",
            "管理费率": "--",
            "托管费率": "--",
            "销售服务费": "--",
            "合计费率": "--",
            "近1年": "--",
            "链接": f"https://fund.eastmoney.com/{code}.html",
            "分类": category,
        })
    return data


KNOWN_NAMES = {
    "270042": "广发纳斯达克100ETF联接人民币(QDII)A",
    "040046": "华安纳斯达克100ETF联接(QDII)A",
    "018043": "天弘纳斯达克100指数发起(QDII)A",
    "016532": "嘉实纳斯达克100ETF发起联接(QDII)人民币A",
    "000834": "大成纳斯达克100ETF联接(QDII)A",
    "160213": "国泰纳斯达克100指数(QDII)",
    "016452": "南方纳斯达克100指数发起(QDII)A",
    "019547": "招商纳斯达克100ETF发起式联接(QDII)A",
    "016055": "博时纳斯达克100ETF发起式联接(QDII)人民币A",
    "539001": "建信纳斯达克100指数(QDII)人民币A",
    "019524": "华泰柏瑞纳斯达克100ETF发起式联接(QDII)A",
    "161130": "易方达纳斯达克100LOF",
    "018966": "汇添富纳斯达克100ETF发起式联接(QDII)人民币A",
    "019172": "摩根纳斯达克100指数(QDII)人民币A",
    "019736": "宝盈纳斯达克100指数发起(QDII)人民币",
    "019441": "万家纳斯达克100指数发起式(QDII)A",
    "015299": "华夏纳斯达克100ETF发起式联接(QDII)A",
    "006479": "广发纳斯达克100ETF联接人民币(QDII)C",
    "014978": "华安纳斯达克100ETF联接(QDII)C",
    "018044": "天弘纳斯达克100指数发起(QDII)C",
    "016453": "南方纳斯达克100指数发起C",
    "008971": "大成纳斯达克100ETF联接(QDII)C",
    "016533": "嘉实纳斯达克100ETF发起式联接(QDII)C",
    "016057": "博时纳斯达克100ETF发起式联接(QDII)C",
    "012752": "建信纳斯达克100指数(QDII)C",
    "019525": "华泰柏瑞纳斯达克100ETF发起式联接(QDII)C",
    "018967": "汇添富纳斯达克100ETF发起式联接(QDII)C",
    "019173": "摩根纳斯达克100指数(QDII)人民币C",
    "019737": "宝盈纳斯达克100指数发起(QDII)人民币C",
    "019442": "万家纳斯达克100指数发起式(QDII)C",
    "015300": "华夏纳斯达克100ETF发起式联接(QDII)C",
    "019548": "招商纳斯达克100ETF发起式联接(QDII)C",
    "012870": "易方达纳斯达克100ETF联接(QDII-LOF)C(人民币)",
    "050025": "博时标普500ETF联接(QDII)A",
    "017641": "摩根标普500指数(QDII)A",
    "161125": "易方达标普500指数LOF",
    "017028": "国泰标普500ETF发起式联接(QDII)A",
    "006075": "博时标普500ETF联接(QDII)C",
    "019305": "摩根标普500指数(QDII)C",
    "012860": "易方达标普500指数(QDII)C",
    "017030": "国泰标普500ETF发起式联接(QDII)C",
    "018064": "华夏标普500ETF发起式联接(QDII)A(人民币)",
    "018065": "华夏标普500ETF发起式联接(QDII)C",
}


def update_fund_status():
    """更新所有基金的申购状态"""
    print()
    print(">>> 更新基金申购状态...")

    fund_data = load_existing_fund_data()
    code_to_item = {f["基金代码"]: f for f in fund_data}

    total = len(FUND_LIST)
    updated = 0
    for i, (code, category) in enumerate(FUND_LIST, 1):
        print(f"  [{i}/{total}] {code}...", end="")
        status_simple, full_status = fetch_fund_page_status(code)

        if code in code_to_item:
            item = code_to_item[code]
            if full_status:
                item["交易状态"] = full_status
                updated += 1
                print(f" {status_simple}")
            else:
                print(" 无变化")
            # 确保基金名称完整
            if not item.get("基金名称") or item["基金名称"] == "":
                if code in KNOWN_NAMES:
                    item["基金名称"] = KNOWN_NAMES[code]
            # 确保链接
            link = f"https://fund.eastmoney.com/{code}.html"
            item["链接"] = link
            item["分类"] = category
        else:
            print(" 跳过(不在列表中)")

    print(f"\n  状态更新: {updated}/{total} 只基金")

    # 保存
    FUND_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FUND_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(fund_data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {FUND_STATUS_FILE}")


if __name__ == "__main__":
    sys.exit(main())
