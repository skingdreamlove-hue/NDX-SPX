import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOBILE_DATA_DIR = os.path.join(BASE_DIR, "docs", "data")
MOBILE_DATA_FILE = os.path.join(MOBILE_DATA_DIR, "latest.json")

def safe_read_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def export():
    os.makedirs(MOBILE_DATA_DIR, exist_ok=True)

    market = safe_read_json(os.path.join(BASE_DIR, "market_data.json"))
    daily_log = safe_read_json(os.path.join(BASE_DIR, "daily_log.json"))
    pcr_history = safe_read_json(os.path.join(BASE_DIR, "pcr_history.json"))
    vix_term_history = safe_read_json(os.path.join(BASE_DIR, "vix_term_history.json"))

    recent_signals = []
    if isinstance(daily_log, list) and len(daily_log) > 0:
        for entry in daily_log[-10:]:
            signal = entry.get("signal", {})
            recent_signals.append({
                "date": entry.get("date", ""),
                "emotion": signal.get("emotion", ""),
                "position": signal.get("target_position", ""),
                "action": signal.get("action", ""),
            })

    pcr_trend = []
    if isinstance(pcr_history, list) and len(pcr_history) > 0:
        for entry in pcr_history[-10:]:
            pcr_trend.append({
                "date": entry.get("date", ""),
                "qqq_pcr": entry.get("qqq_pcr"),
                "spy_pcr": entry.get("spy_pcr"),
            })

    vix_term_trend = []
    if isinstance(vix_term_history, list) and len(vix_term_history) > 0:
        for entry in vix_term_history[-10:]:
            vix_term_trend.append({
                "date": entry.get("date", ""),
                "ratio": entry.get("ratio"),
            })

    mobile_data = {
        "_generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sentiment": {
            "level": market.get("sentiment_result", "未知"),
            "strength": market.get("signal_strength", ""),
            "conditions": market.get("sentiment_conditions", []),
        },
        "position": {
            "advice": market.get("position_advice", ""),
            "target": market.get("target_position", ""),
            "daily_buy": market.get("daily_buy_amount", 300),
        },
        "indices": {
            "nasdaq100": market.get("current_nasdaq100"),
            "sp500": market.get("current_sp500"),
            "nasdaq100_drawdown": market.get("nasdaq100_drawdown"),
            "sp500_drawdown": market.get("sp500_drawdown"),
            "nasdaq100_dev_ma200": market.get("nasdaq100_ma200_diff"),
            "sp500_dev_ma200": market.get("sp500_ma200_diff"),
        },
        "indicators": {
            "vix": market.get("current_vix"),
            "vix_term_ratio": market.get("vix_term_ratio"),
            "credit_spread": market.get("credit_spread"),
            "tnx_ma50_diff": market.get("tnx_ma50_diff"),
            "qqq_pcr": market.get("qqq_pcr"),
            "spy_pcr": market.get("spy_pcr"),
            "ndx_spx_ratio": market.get("ndx_spx_ratio"),
            "iwm_spy_ratio": market.get("iwm_spy_ratio"),
            "sp500_breadth_200ma": market.get("sp500_breadth_200ma"),
            "ndx_breadth_200ma": market.get("ndx_breadth_200ma"),
            "on_rrp_current": market.get("on_rrp_current"),
            "on_rrp_deviation": market.get("on_rrp_deviation"),
            "buffett_indicator": market.get("buffett_indicator"),
        },
        "recent_signals": recent_signals,
        "pcr_trend": pcr_trend,
        "vix_term_trend": vix_term_trend,
        "last_update": market.get("last_update", ""),
    }

    with open(MOBILE_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(mobile_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Mobile data exported to {MOBILE_DATA_FILE}")
    print(f"     Sentiment: {mobile_data['sentiment']['level']}")
    print(f"     VIX: {mobile_data['indicators']['vix']}")
    print(f"     Position: {mobile_data['position']['advice']}")

if __name__ == "__main__":
    export()