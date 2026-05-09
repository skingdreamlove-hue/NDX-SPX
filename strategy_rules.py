# 美股情绪监测系统 - 策略规则定义
# 此文件定义情绪级别判定阈值、仓位建议、定投倍数
# 包含：基准策略A（无脑定投）+ 策略M（趋势动量过滤版）

# ═══════════════════════════════════════════════════════════════════════════════
# 通用参数
# ═══════════════════════════════════════════════════════════════════════════════

# 每日买入上限（限购约束，所有策略共用）
BUY_CAP = 1500.0

# 赎回约束：每日赎回上限1500元，每月赎回上限33000元
SELL_CAP_DAILY   = 1500.0
SELL_CAP_MONTHLY = 33000.0

# 缓卖每日卖出比例
SLOW_SELL_DAILY = 0.00095

# 定投基准金额
DAILY_DCA = 300.0

# 期初配置
INIT_CAPITAL   = 100_000.0
INIT_EQ_RATIO  = 0.40

# 现金日利率
CASH_RATE_D    = 0.02 / 365

# ═══════════════════════════════════════════════════════════════════════════════
# 基准策略A：无脑定投
# ═══════════════════════════════════════════════════════════════════════════════

# 每日定投金额
A_DAILY_INVEST = 300.0

# 无目标仓位调整，不做择时
A_TARGET_POSITION = 1.0
A_SLOW_SELL = False

# ═══════════════════════════════════════════════════════════════════════════════
# 策略M：趋势动量过滤版（情绪驱动 + MA20动量拦截器）
# ═══════════════════════════════════════════════════════════════════════════════

# ── 情绪判断指标 ──

# 极度恐慌阈值（满足任一即可）
M_EXTREME_FEAR_THRESHOLDS = {
    "vix_term": 1.0,
    "vix": 35,
    "credit_spread": 8.0,
    "ndx_drawdown": -30.0,
    "spx_drawdown": -20.0,
    "ndx_breadth_200ma": 15.0,
}

# 恐慌阈值（满足任一即可）
M_FEAR_THRESHOLDS = {
    "vix": (25.0, 35.0),
    "credit_spread": (5.5, 8.0),
    "ndx_drawdown": (-30.0, -15.0),
    "spx_drawdown": (-20.0, -10.0),
    "ndx_breadth_200ma": (15.0, 25.0),
}

# 极度贪婪阈值（满足任一即可）
M_EXTREME_GREED_THRESHOLDS = {
    "ndx_dev_ma200": 28.0,
    "spx_dev_ma200": 18.0,
    "vix_low_ndx_dev": {"vix": 13.0, "ndx_dev": 22.0},
}

# 贪婪阈值（满足任一即可）
M_GREED_THRESHOLDS = {
    "ndx_dev_ma200": 20.0,
    "spx_dev_ma200": 12.0,
    "vix_low_ndx_dev": {"vix": (12.0, 16.0), "ndx_dev": 15.0},
}

# ── 目标仓位（NDX上方 / NDX下方）──
M_POSITION_MAP = {
    ("极度恐慌", True): 100,
    ("极度恐慌", False): 100,
    ("恐慌", True): 100,
    ("恐慌", False): 100,
    ("中性", True): 100,
    ("中性", False): 88,
    ("贪婪", True): 90,
    ("贪婪", False): 70,
    ("极度贪婪", True): 65,
    ("极度贪婪", False): 55,
}

# ── 日定投金额（DAILY_DCA × 倍数）──
M_SIP_MULTIPLIER = {
    "极度恐慌": 5.0,   # 1500元/日
    "恐慌": 3.0,       # 900元/日
    "中性": 1.0,       # 300元/日
    "贪婪": 0.0,       # 0元/日
    "极度贪婪": 0.0,   # 0元/日
}

# ── 动量拦截规则 ──
# 当原始情绪为贪婪/极度贪婪时：
#   - 若 NDX 收盘价 > NDX MA20 → 情绪降级为中性（拦截卖出，让利润奔跑）
#   - 若 NDX 收盘价 <= NDX MA20 → 维持原情绪（趋势破位，落袋为安）

# ── 约束条件 ──
# 买入：DCA + 调仓买入 ≤ 1500元/日
# 卖出：≤ 1500元/日 且 ≤ 33000元/月


# ═══════════════════════════════════════════════════════════════════════════════
# 公共函数库（供 generate_charts.py、backtest.py 等调用）
# ═══════════════════════════════════════════════════════════════════════════════

def calc_rate_shock(tnx_ma50_diff):
    """判断是否触发利率冲击（10年期美债偏离MA50超10%）"""
    if tnx_ma50_diff is None:
        return False
    return tnx_ma50_diff > 10


def calc_emotion_core(ndx_drawdown, spx_drawdown, ndx_dev_ma200, spx_dev_ma200,
                       vix, vix_term, credit_spread, rate_shock, ndx_breadth_200ma):
    """
    核心防线情绪判断（不含PCR/AAII增强）
    返回: (sentiment_str, core_triggered_list)
    """
    triggered = []

    # 利率冲击时，恐慌条件需额外满足
    def fear_ok(indicator, val, thresholds):
        if indicator in ('ndx_drawdown', 'spx_drawdown', 'ndx_breadth_200ma'):
            if not rate_shock:
                return False
        t = thresholds.get(indicator)
        if t is None:
            return False
        if isinstance(t, tuple):
            return t[0] <= val < t[1]
        if isinstance(t, (int, float)):
            return val <= t
        return False

    # ── 极度恐慌 ──
    def extreme_fear_check():
        checks = [
            ("vix_term", vix_term, lambda v: v is not None and v > 1.0),
            ("vix", vix, lambda v: v is not None and v > 35),
            ("credit_spread", credit_spread, lambda v: v is not None and v > 8.0),
            ("ndx_drawdown", ndx_drawdown, lambda v: v <= -30.0),
            ("spx_drawdown", spx_drawdown, lambda v: v <= -20.0),
            ("ndx_breadth_200ma", ndx_breadth_200ma, lambda v: v is not None and v < 15.0),
        ]
        for indicator, val, fn in checks:
            if indicator == 'ndx_drawdown' and rate_shock:
                if fn(val):
                    triggered.append(("极度恐慌", indicator))
                    return True
            elif indicator == 'spx_drawdown' and rate_shock:
                if fn(val):
                    triggered.append(("极度恐慌", indicator))
                    return True
            elif indicator == 'ndx_breadth_200ma' and rate_shock:
                if fn(val):
                    triggered.append(("极度恐慌", indicator))
                    return True
            elif fn(val):
                triggered.append(("极度恐慌", indicator))
                return True
        return False

    # ── 恐慌 ──
    def fear_check():
        checks = [
            ("vix", vix, lambda v: v is not None and 25.0 <= v < 35.0),
            ("credit_spread", credit_spread, lambda v: v is not None and 5.5 <= v < 8.0),
            ("ndx_drawdown", ndx_drawdown, lambda v: -30.0 < v <= -15.0),
            ("spx_drawdown", spx_drawdown, lambda v: -20.0 < v <= -10.0),
            ("ndx_breadth_200ma", ndx_breadth_200ma, lambda v: v is not None and 15.0 <= v < 25.0),
        ]
        for indicator, val, fn in checks:
            if indicator in ('ndx_drawdown', 'spx_drawdown', 'ndx_breadth_200ma') and not rate_shock:
                continue
            if fn(val):
                triggered.append(("恐慌", indicator))
                return True
        return False

    # ── 极度贪婪 ──
    def extreme_greed_check():
        if ndx_dev_ma200 is not None and ndx_dev_ma200 > 28.0:
            triggered.append(("极度贪婪", "ndx_dev_ma200"))
            return True
        if spx_dev_ma200 is not None and spx_dev_ma200 > 18.0:
            triggered.append(("极度贪婪", "spx_dev_ma200"))
            return True
        if (vix is not None and vix < 13.0 and ndx_dev_ma200 is not None and ndx_dev_ma200 > 22.0):
            triggered.append(("极度贪婪", "vix_low_ndx_dev"))
            return True
        return False

    # ── 贪婪 ──
    def greed_check():
        if ndx_dev_ma200 is not None and ndx_dev_ma200 > 20.0:
            triggered.append(("贪婪", "ndx_dev_ma200"))
            return True
        if spx_dev_ma200 is not None and spx_dev_ma200 > 12.0:
            triggered.append(("贪婪", "spx_dev_ma200"))
            return True
        if vix is not None and 12.0 <= vix < 16.0 and ndx_dev_ma200 is not None and ndx_dev_ma200 > 15.0:
            triggered.append(("贪婪", "vix_low_ndx_dev"))
            return True
        return False

    # 优先级：极度恐慌 > 恐慌 > 极度贪婪 > 贪婪 > 中性
    if extreme_fear_check():
        return "极度恐慌", triggered
    if fear_check():
        return "恐慌", triggered
    if extreme_greed_check():
        return "极度贪婪", triggered
    if greed_check():
        return "贪婪", triggered
    return "中性", triggered


def calc_signal_strength(sentiment, core_triggered, pcr_bonus):
    """
    计算信号强度（星星数）
    返回: (strength_str, trigger_dims)
    """
    dims = set()
    for emotion, indicator in core_triggered:
        if indicator in ('vix', 'vix_term', 'vix_low'):
            dims.add('volatility')
        elif indicator in ('credit_spread',):
            dims.add('credit')
        elif indicator in ('ndx_drawdown', 'spx_drawdown', 'ndx_dev_ma200', 'spx_dev_ma200', 'ndx_breadth_200ma'):
            dims.add('technical')

    n = len(dims)
    if pcr_bonus:
        n += 1

    if n >= 3:
        return "★★★★★ 极强", dims
    elif n >= 2:
        return "★★★★ 强", dims
    elif n >= 1:
        return "★★★ 中等", dims
    else:
        return "★ 弱", dims


def get_target_position(sentiment, ndx_above_ma200):
    """
    根据情绪和NDX是否在MA200上方，返回目标仓位百分比
    """
    key = (sentiment, ndx_above_ma200)
    return M_POSITION_MAP.get(key, 100)


def get_position_advice(sentiment, current_position, target_position, ndx_above_ma200):
    """
    生成仓位操作建议字符串
    """
    target = get_target_position(sentiment, ndx_above_ma200)
    diff = target - current_position
    action = "持有"
    if diff > 1:
        action = "加仓"
    elif diff < -1:
        action = "减仓"
    return f"目标仓位 {target}% / 当前仓位 {current_position}% / {action}"


def get_daily_buy_amount(sentiment):
    """
    根据情绪返回每日定投金额（元）
    """
    multiplier = M_SIP_MULTIPLIER.get(sentiment, 1.0)
    return DAILY_DCA * multiplier


def apply_momentum_filter(raw_emotion, ndx_close, ndx_ma20):
    """
    动量拦截器：当原始情绪为贪婪/极度贪婪时，
    如果NDX收盘价 > MA20，降级为中性（取消减仓计划）
    """
    if raw_emotion in ("贪婪", "极度贪婪"):
        if ndx_close is not None and ndx_ma20 is not None and ndx_close > ndx_ma20:
            return "中性", True
    return raw_emotion, False
