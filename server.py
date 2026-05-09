import os
import sys
import json
import subprocess
import socket
import threading
import uuid
import csv as builtin_csv
from flask import Flask, jsonify, send_from_directory, request
from datetime import datetime

app = Flask(__name__, static_folder='.')

# 动态端口查找
def find_available_port(start_port=5000):
    port = start_port
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:
            return port
        port += 1
        if port > start_port + 100:
            print(f"警告: 端口 {start_port}-{start_port+100} 都已被占用，尝试使用 {start_port}")
            return start_port

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/update-data', methods=['POST'])
def update_data():
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行数据更新...")
        
        project_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(project_dir, 'generate_charts.py')
        
        # 执行数据抓取脚本
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=project_dir
        )
        
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 数据更新成功")
            try:
                sync_daily_log_to_csv()
            except Exception:
                pass
            return jsonify({
                'success': True,
                'message': '数据更新成功',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            error_msg = result.stderr or result.stdout or '未知错误'
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 数据更新失败: {error_msg}")
            return jsonify({
                'success': False,
                'message': f'数据更新失败: {error_msg[:200]}'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': '数据更新超时，请检查网络连接'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@app.route('/market_data.js')
def market_data_js():
    return send_from_directory('.', 'market_data.js')

@app.route('/nasdaq100_chart.html')
def nasdaq100_chart():
    return send_from_directory('.', 'nasdaq100_chart.html')

@app.route('/sp500_chart.html')
def sp500_chart():
    return send_from_directory('.', 'sp500_chart.html')

@app.route('/daily_log.js')
def daily_log_js():
    return send_from_directory('.', 'daily_log.js')

@app.route('/review.html')
def review_page():
    return send_from_directory('.', 'review.html')

@app.route("/backtest")
def backtest_page():
    return send_from_directory('.', 'backtest.html')

@app.route("/restriction")
def restriction_page():
    return send_from_directory('.', 'restriction.html')

backtest_tasks = {}

@app.route('/api/backtest', methods=['POST'])
def api_start_backtest():
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    if start_date < '2007-10-01':
        return jsonify({"status": "error", "message": "开始时间不能早于2007年10月1日"}), 400
    initial_capital = data.get('initial_capital', 100000)
    initial_position = data.get('initial_position', 0.40)
    daily_sip = data.get('daily_sip', 300)
    cash_yield = data.get('cash_yield', 0.02)
    buy_cap = data.get('buy_cap', 1500)

    task_id = str(uuid.uuid4())
    backtest_tasks[task_id] = {"status": "running", "progress": 0, "message": "初始化..."}

    def progress_cb(pct, msg):
        backtest_tasks[task_id]["progress"] = pct
        backtest_tasks[task_id]["message"] = msg

    def run_task():
        try:
            from backtest import run_backtest
            report = run_backtest(
                start_date, end_date,
                progress_callback=progress_cb,
                initial_capital=initial_capital,
                initial_position=initial_position,
                daily_sip=daily_sip,
                cash_yield=cash_yield,
                buy_cap=buy_cap,
            )
            backtest_tasks[task_id] = {"status": "done", "report": report}
        except Exception as e:
            backtest_tasks[task_id] = {"status": "error", "message": str(e)}

    thread = threading.Thread(target=run_task)
    thread.start()

    return jsonify({"status": "running", "task_id": task_id})

@app.route('/api/backtest/progress')
def api_backtest_progress():
    task_id = request.args.get('task_id')
    task = backtest_tasks.get(task_id)
    if not task:
        return jsonify({"status": "error", "message": "任务不存在"}), 404
    try:
        return jsonify(task)
    except (TypeError, ValueError):
        import json
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                try:
                    import numpy as np
                    if isinstance(obj, (np.integer,)):
                        return int(obj)
                    if isinstance(obj, (np.floating,)):
                        return float(obj)
                    if isinstance(obj, (np.ndarray,)):
                        return obj.tolist()
                except ImportError:
                    pass
                return super().default(obj)
        return app.response_class(
            response=json.dumps(task, ensure_ascii=False, cls=NumpyEncoder),
            status=200,
            mimetype='application/json'
        )

CSV_COLUMNS = ['date','sentiment','ndx_5d','spx_5d','ndx_10d','spx_10d','ndx_20d','spx_20d','verified_5d','verified_10d','verified_20d','accuracy']

_OLD_CSV_MAP = {
    'emotion': 'sentiment',
    'verify_5d_ndx_return': 'ndx_5d',
    'verify_5d_spx_return': 'spx_5d',
    'verify_20d_ndx_return': 'ndx_20d',
    'verify_20d_spx_return': 'spx_20d',
    'verify_5d_result': 'verified_5d',
    'verify_20d_result': 'verified_20d',
}

_OLD_VALUE_MAP = {
    'correct': '正确',
    'wrong': '误判',
    'pending': '待验证',
    'verified': '待验证',
}

def _migrate_csv_row(row):
    mapped = {}
    for k, v in row.items():
        new_k = _OLD_CSV_MAP.get(k, k)
        if new_k in ('verified_5d', 'verified_10d', 'verified_20d') and v in _OLD_VALUE_MAP:
            v = _OLD_VALUE_MAP[v]
        mapped[new_k] = v
    if 'ndx_10d' not in mapped or not mapped.get('ndx_10d'):
        mapped['ndx_10d'] = ''
    if 'spx_10d' not in mapped or not mapped.get('spx_10d'):
        mapped['spx_10d'] = ''
    if 'verified_10d' not in mapped or not mapped.get('verified_10d'):
        mapped['verified_10d'] = ''
    if 'accuracy' not in mapped or not mapped.get('accuracy'):
        mapped['accuracy'] = ''
    for old_key in _OLD_CSV_MAP:
        if old_key in mapped:
            del mapped[old_key]
    return mapped

def read_daily_csv(filepath):
    rows = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = builtin_csv.DictReader(f)
            for row in reader:
                clean_row = {}
                for k, v in row.items():
                    clean_k = k.replace('\ufeff', '').strip()
                    clean_row[clean_k] = v.strip() if v else ''
                needs_migration = any(k in clean_row for k in _OLD_CSV_MAP)
                if needs_migration:
                    clean_row = _migrate_csv_row(clean_row)
                rows.append(clean_row)
    return rows

def write_daily_csv(filepath, rows):
    import csv as csv_module
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv_module.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            out = {}
            for k in CSV_COLUMNS:
                out[k] = row.get(k, '')
            writer.writerow(out)

def append_daily_csv_row(filepath, row):
    rows = read_daily_csv(filepath)
    rows.append(row)
    write_daily_csv(filepath, rows)

def compute_verification(sentiment, ndx_ret, spx_ret, neutral_threshold):
    """
    sentiment: 当日情绪标签
    ndx_ret / spx_ret: 后续 N 日收益率（分别传入5/10/20日）
    neutral_threshold: 动态中性阈值（0.5 × 20日滚动标准差）
    返回: True=判断正确, False=判断错误, None=无法判定
    """
    if ndx_ret is None or spx_ret is None:
        return None
    if sentiment in ('恐慌', '极度恐慌'):
        return (ndx_ret > 0) and (spx_ret > 0)
    elif sentiment in ('贪婪', '极度贪婪'):
        return (ndx_ret < 0) and (spx_ret < 0)
    elif sentiment == '中性':
        return (abs(ndx_ret) < neutral_threshold) and (abs(spx_ret) < neutral_threshold)
    else:
        return None

def compute_single_accuracy(correct_5d, verified_5d,
                             correct_10d, verified_10d,
                             correct_20d, verified_20d):
    """
    correct_Nd: 该周期是否判断正确（True/False），未到期为 None
    verified_Nd: 该周期是否已可验证（bool）
    权重: 5日=0.2, 10日=0.3, 20日=0.5
    """
    weights = {5: 0.2, 10: 0.3, 20: 0.5}
    score = 0.0
    total_weight = 0.0

    for result, verified, w in [
        (correct_5d,  verified_5d,  weights[5]),
        (correct_10d, verified_10d, weights[10]),
        (correct_20d, verified_20d, weights[20]),
    ]:
        if verified and result is not None:
            total_weight += w
            if result:
                score += w

    if total_weight == 0:
        return None

    return round(score / total_weight * 100, 2)


def compute_period_accuracy(signals):
    """
    signals: 所有历史情绪信号列表，每条含 correct_5d/10d/20d 字段
    返回: acc_5d, acc_10d, acc_20d（百分比，样本不足返回 None）
    """
    MIN_SAMPLE = 30

    result = {}
    for days in [5, 10, 20]:
        key = 'correct_{}d'.format(days)
        verified = [s[key] for s in signals if s[key] is not None]
        if len(verified) < MIN_SAMPLE:
            result['acc_{}d'.format(days)] = None
        else:
            result['acc_{}d'.format(days)] = round(sum(verified) / len(verified) * 100, 2)

    return result


def compute_overall_accuracy(acc_5d, acc_10d, acc_20d):
    """
    仅使用已有足够样本的周期参与加权，权重归一化处理
    """
    weights = {5: 0.2, 10: 0.3, 20: 0.5}
    available = []

    for days, acc in [(5, acc_5d), (10, acc_10d), (20, acc_20d)]:
        if acc is not None:
            available.append((acc, weights[days]))

    if not available:
        return None

    total_weight = sum(w for _, w in available)
    overall = sum(acc * w for acc, w in available) / total_weight

    return round(overall, 2)

def update_daily_log_csv():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(project_dir, 'daily_log.csv')
    daily_log_path = os.path.join(project_dir, 'daily_log.json')

    rows = read_daily_csv(csv_path)
    if not rows:
        return

    daily_logs = []
    if os.path.exists(daily_log_path):
        with open(daily_log_path, 'r', encoding='utf-8') as f:
            daily_logs = json.load(f)

    log_by_date = {}
    for entry in daily_logs:
        log_by_date[entry.get('date')] = entry

    modified = False
    today = datetime.now().date()

    import pandas as pd
    spx_returns = pd.Series(dtype=float)
    try:
        import yfinance as yf
        spx_cache = os.path.join(project_dir, 'backtest_data', 'spx.csv')
        if os.path.exists(spx_cache):
            spx_df = pd.read_csv(spx_cache, index_col=0, parse_dates=True)
            spx_close = spx_df.iloc[:, 0] if spx_df.shape[1] > 0 else None
            if spx_close is not None:
                spx_returns = spx_close.pct_change().dropna() * 100
        if spx_returns.empty:
            spx_df = yf.download('^GSPC', start='2010-01-01', auto_adjust=True, progress=False)
            if not spx_df.empty:
                spx_returns = pd.Series(spx_df['Close'].pct_change().dropna() * 100)
    except Exception:
        spx_returns = pd.Series(dtype=float)

    for row in rows:
        date = row.get('date', '')
        sentiment = row.get('sentiment', '')
        if not date:
            continue

        log_entry = log_by_date.get(date)
        if not log_entry:
            continue

        try:
            signal_date = datetime.strptime(date, '%Y-%m-%d').date()
        except Exception:
            continue
        days_passed = (today - signal_date).days

        v5 = log_entry.get('verify_5d') or {}
        correct_5d = None
        verified_5d = False
        existing_v5 = row.get('verified_5d', '')
        if existing_v5 == '正确':
            correct_5d = True
            verified_5d = True
        elif existing_v5 == '误判':
            correct_5d = False
            verified_5d = True

        v10 = log_entry.get('verify_10d') or {}
        correct_10d = None
        verified_10d = False
        existing_v10 = row.get('verified_10d', '')
        if existing_v10 == '正确':
            correct_10d = True
            verified_10d = True
        elif existing_v10 == '误判':
            correct_10d = False
            verified_10d = True

        v20 = log_entry.get('verify_20d') or {}
        correct_20d = None
        verified_20d = False
        existing_v20 = row.get('verified_20d', '')
        if existing_v20 == '正确':
            correct_20d = True
            verified_20d = True
        elif existing_v20 == '误判':
            correct_20d = False
            verified_20d = True

        try:
            signal_dt = pd.Timestamp(date)
            if not spx_returns.empty:
                hist = spx_returns.loc[:signal_dt].tail(20)
                nt = float(hist.std() * 0.5) if len(hist) >= 10 else 0.02
            else:
                nt = 0.02
        except Exception:
            nt = 0.02

        if days_passed >= 5 and row.get('verified_5d') in ('', '--', None, '不适用'):
            ndx_r = v5.get('ndx_return')
            spx_r = v5.get('spx_return')
            row['ndx_5d'] = ('%+.2f%%' % ndx_r) if ndx_r is not None else '--'
            row['spx_5d'] = ('%+.2f%%' % spx_r) if spx_r is not None else '--'
            result = compute_verification(sentiment, ndx_r, spx_r, nt)
            if result is True:
                row['verified_5d'] = '正确'
                correct_5d = True
                verified_5d = True
            elif result is False:
                row['verified_5d'] = '误判'
                correct_5d = False
                verified_5d = True
            else:
                row['verified_5d'] = '待验证'
            modified = True

        if days_passed >= 10 and row.get('verified_10d') in ('', '--', None, '不适用'):
            ndx_r = v10.get('ndx_return')
            spx_r = v10.get('spx_return')
            row['ndx_10d'] = ('%+.2f%%' % ndx_r) if ndx_r is not None else '--'
            row['spx_10d'] = ('%+.2f%%' % spx_r) if spx_r is not None else '--'
            result = compute_verification(sentiment, ndx_r, spx_r, nt)
            if result is True:
                row['verified_10d'] = '正确'
                correct_10d = True
                verified_10d = True
            elif result is False:
                row['verified_10d'] = '误判'
                correct_10d = False
                verified_10d = True
            else:
                row['verified_10d'] = '待验证'
            modified = True

        if days_passed >= 20 and row.get('verified_20d') in ('', '--', None, '不适用'):
            ndx_r = v20.get('ndx_return')
            spx_r = v20.get('spx_return')
            row['ndx_20d'] = ('%+.2f%%' % ndx_r) if ndx_r is not None else '--'
            row['spx_20d'] = ('%+.2f%%' % spx_r) if spx_r is not None else '--'
            result = compute_verification(sentiment, ndx_r, spx_r, nt)
            if result is True:
                row['verified_20d'] = '正确'
                correct_20d = True
                verified_20d = True
            elif result is False:
                row['verified_20d'] = '误判'
                correct_20d = False
                verified_20d = True
            else:
                row['verified_20d'] = '待验证'
            modified = True

        acc = compute_single_accuracy(correct_5d, verified_5d, correct_10d, verified_10d, correct_20d, verified_20d)
        row['accuracy'] = ('%.0f%%' % acc) if acc is not None else '--'

    if modified:
        write_daily_csv(csv_path, rows)

def sync_daily_log_to_csv():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(project_dir, 'daily_log.csv')
    daily_log_path = os.path.join(project_dir, 'daily_log.json')

    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline().strip()
        if 'sentiment' not in first_line and 'ndx_5d' not in first_line:
            migrated = migrate_old_csv(csv_path)
            write_daily_csv(csv_path, migrated)

    existing_rows = read_daily_csv(csv_path)
    existing_dates = set(r.get('date', '') for r in existing_rows)

    daily_logs = []
    if os.path.exists(daily_log_path):
        with open(daily_log_path, 'r', encoding='utf-8') as f:
            daily_logs = json.load(f)

    new_count = 0
    for entry in daily_logs:
        date = entry.get('date', '')
        if date in existing_dates:
            continue
        signal = entry.get('signal') or {}
        emotion = signal.get('emotion', '')
        new_row = {
            'date': date,
            'sentiment': emotion,
            'ndx_5d': '--', 'spx_5d': '--',
            'ndx_10d': '--', 'spx_10d': '--',
            'ndx_20d': '--', 'spx_20d': '--',
            'verified_5d': '不适用' if emotion == '中性' else '待验证',
            'verified_10d': '不适用' if emotion == '中性' else '待验证',
            'verified_20d': '不适用' if emotion == '中性' else '待验证',
            'accuracy': '--'
        }
        existing_rows.append(new_row)
        existing_dates.add(date)
        new_count += 1

    if new_count > 0:
        write_daily_csv(csv_path, existing_rows)
    update_daily_log_csv()

def migrate_old_csv(csv_path):
    rows = []
    if not os.path.exists(csv_path):
        return rows
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = builtin_csv.DictReader(f)
        for row in reader:
            date = row.get('date', '')
            emotion = row.get('emotion', '')
            new_row = {
                'date': date,
                'sentiment': emotion,
                'ndx_5d': '--', 'spx_5d': '--',
                'ndx_10d': '--', 'spx_10d': '--',
                'ndx_20d': '--', 'spx_20d': '--',
                'verified_5d': '不适用',
                'verified_10d': '不适用',
                'verified_20d': '不适用',
                'accuracy': '--'
            }
            v5_status = row.get('verify_5d_status', '')
            v5_result = row.get('verify_5d_result', '')
            if v5_status == 'verified':
                if v5_result == 'correct':
                    new_row['verified_5d'] = '正确'
                elif v5_result == 'wrong':
                    new_row['verified_5d'] = '误判'
                else:
                    new_row['verified_5d'] = '待验证'
                ndx_r = row.get('verify_5d_ndx_return', '')
                if ndx_r and ndx_r != '':
                    try:
                        new_row['ndx_5d'] = '%+.2f%%' % float(ndx_r)
                    except Exception:
                        new_row['ndx_5d'] = '--'
                spx_r = row.get('verify_5d_spx_return', '')
                if spx_r and spx_r != '':
                    try:
                        new_row['spx_5d'] = '%+.2f%%' % float(spx_r)
                    except Exception:
                        new_row['spx_5d'] = '--'
            elif v5_status == 'pending':
                if emotion != '中性':
                    new_row['verified_5d'] = '待验证'

            v20_status = row.get('verify_20d_status', '')
            v20_result = row.get('verify_20d_result', '')
            if v20_status == 'verified':
                if v20_result == 'correct':
                    new_row['verified_20d'] = '正确'
                elif v20_result == 'wrong':
                    new_row['verified_20d'] = '误判'
                else:
                    new_row['verified_20d'] = '待验证'
                ndx_r = row.get('verify_20d_ndx_return', '')
                if ndx_r and ndx_r != '':
                    try:
                        new_row['ndx_20d'] = '%+.2f%%' % float(ndx_r)
                    except Exception:
                        new_row['ndx_20d'] = '--'
                spx_r = row.get('verify_20d_spx_return', '')
                if spx_r and spx_r != '':
                    try:
                        new_row['spx_20d'] = '%+.2f%%' % float(spx_r)
                    except Exception:
                        new_row['spx_20d'] = '--'
            elif v20_status == 'pending':
                if emotion != '中性':
                    new_row['verified_20d'] = '待验证'

            def _mig_bool_from_str(val):
                if val == '正确': return (True, True)
                elif val == '误判': return (False, True)
                else: return (None, False)
            mc5, mv5 = _mig_bool_from_str(new_row.get('verified_5d', ''))
            mc10, mv10 = _mig_bool_from_str(new_row.get('verified_10d', ''))
            mc20, mv20 = _mig_bool_from_str(new_row.get('verified_20d', ''))
            mig_acc = compute_single_accuracy(mc5, mv5, mc10, mv10, mc20, mv20)
            new_row['accuracy'] = ('%.0f%%' % mig_acc) if mig_acc is not None else '--'
            if emotion == '中性':
                new_row['verified_5d'] = '不适用'
                new_row['verified_10d'] = '不适用'
                new_row['verified_20d'] = '不适用'
                new_row['accuracy'] = '--'
            rows.append(new_row)
    return rows

@app.route('/api/review-data')
def api_review_data():
    print("[ReviewData] 路由被调用", flush=True)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    result = {
        "strategy_text": "",
        "signal_records": [],
        "daily_logs": [],
        "summary": {
            "total_signals": 0,
            "verified_count": 0,
            "correct_count": 0,
            "pending_count": 0
        }
    }

    strategy_path = os.path.join(project_dir, 'strategy_rules.py')
    if os.path.exists(strategy_path):
        with open(strategy_path, 'r', encoding='utf-8') as f:
            result["strategy_text"] = f.read()

    csv_path = os.path.join(project_dir, 'daily_log.csv')
    all_rows = read_daily_csv(csv_path)
    all_rows_sorted = sorted(all_rows, key=lambda r: r.get('date', ''))

    result["signal_records"] = all_rows_sorted[-30:]

    daily_log_path = os.path.join(project_dir, 'daily_log.json')
    if os.path.exists(daily_log_path):
        try:
            with open(daily_log_path, 'r', encoding='utf-8') as f:
                result["daily_logs"] = json.load(f)
                if not isinstance(result["daily_logs"], list):
                    result["daily_logs"] = []
        except Exception:
            pass

    effective_rows = [r for r in all_rows if r.get('sentiment', '') not in ('', '中性')]

    def _bool_from_csv_str(val):
        if val == '正确': return (True, True)
        elif val == '误判': return (False, True)
        else: return (None, False)

    bool_signals_all = []
    for row in all_rows:
        c5, v5 = _bool_from_csv_str(row.get('verified_5d', ''))
        c10, v10 = _bool_from_csv_str(row.get('verified_10d', ''))
        c20, v20 = _bool_from_csv_str(row.get('verified_20d', ''))
        bool_signals_all.append({
            'sentiment': row.get('sentiment', ''),
            'correct_5d': c5 if v5 else None,
            'correct_10d': c10 if v10 else None,
            'correct_20d': c20 if v20 else None,
        })

    bool_signals_effective = [s for s in bool_signals_all if s['sentiment'] not in ('', '中性')]

    period_acc = compute_period_accuracy(bool_signals_all)
    acc_5d = period_acc['acc_5d']
    acc_10d = period_acc['acc_10d']
    acc_20d = period_acc['acc_20d']
    overall_acc = compute_overall_accuracy(acc_5d, acc_10d, acc_20d)

    verified_5d = sum(1 for s in bool_signals_all if s['correct_5d'] is not None)
    correct_5d = sum(1 for s in bool_signals_all if s['correct_5d'] is True)
    pending_count = sum(1 for s in bool_signals_all if s['correct_5d'] is None and s['sentiment'] not in ('', '中性'))
    verified_10d = sum(1 for s in bool_signals_all if s['correct_10d'] is not None)
    correct_10d = sum(1 for s in bool_signals_all if s['correct_10d'] is True)
    verified_20d = sum(1 for s in bool_signals_all if s['correct_20d'] is not None)
    correct_20d = sum(1 for s in bool_signals_all if s['correct_20d'] is True)

    s_verified_5d = sum(1 for s in bool_signals_effective if s['correct_5d'] is not None)
    s_correct_5d = sum(1 for s in bool_signals_effective if s['correct_5d'] is True)
    s_verified_10d = sum(1 for s in bool_signals_effective if s['correct_10d'] is not None)
    s_correct_10d = sum(1 for s in bool_signals_effective if s['correct_10d'] is True)
    s_verified_20d = sum(1 for s in bool_signals_effective if s['correct_20d'] is not None)
    s_correct_20d = sum(1 for s in bool_signals_effective if s['correct_20d'] is True)

    signal_basis = "暂无"
    s_verified = 0
    s_correct = 0
    if s_verified_20d > 0:
        s_verified = s_verified_20d
        s_correct = s_correct_20d
        signal_basis = "20日"
    elif s_verified_10d > 0:
        s_verified = s_verified_10d
        s_correct = s_correct_10d
        signal_basis = "10日"
    elif s_verified_5d > 0:
        s_verified = s_verified_5d
        s_correct = s_correct_5d
        signal_basis = "5日"

    signal_total = len(effective_rows)
    signal_acc = (s_correct / s_verified * 100) if s_verified > 0 else None

    result["summary"]["effective_count"] = signal_total
    result["summary"]["verified_count"] = verified_5d
    result["summary"]["correct_count"] = correct_5d
    result["summary"]["pending_count"] = pending_count
    result["summary"]["accuracy_5d"] = ("%.1f%%" % acc_5d) if acc_5d is not None else "--"
    result["summary"]["verified_10d"] = verified_10d
    result["summary"]["correct_10d"] = correct_10d
    result["summary"]["accuracy_10d"] = ("%.1f%%" % acc_10d) if acc_10d is not None else "--"
    result["summary"]["verified_20d"] = verified_20d
    result["summary"]["correct_20d"] = correct_20d
    result["summary"]["accuracy_20d"] = ("%.1f%%" % acc_20d) if acc_20d is not None else "--"
    result["summary"]["overall_accuracy"] = ("%.1f%%" % overall_acc) if overall_acc is not None else "--"
    result["summary"]["signal_accuracy"] = ("%.1f%%" % signal_acc) if signal_acc is not None else "--"
    result["summary"]["signal_total"] = signal_total
    result["summary"]["signal_verified"] = s_verified
    result["summary"]["signal_correct"] = s_correct
    result["summary"]["signal_basis"] = signal_basis

    emotions_order = ['极度恐慌', '恐慌', '中性', '贪婪', '极度贪婪']
    emotion_hitrates = {}
    for em in emotions_order:
        rows_e = [r for r in all_rows if r.get('sentiment', '') == em]
        total_e = len(rows_e)
        v5 = sum(1 for r in rows_e if r.get('verified_5d', '') in ('正确', '误判'))
        c5 = sum(1 for r in rows_e if r.get('verified_5d', '') == '正确')
        v10 = sum(1 for r in rows_e if r.get('verified_10d', '') in ('正确', '误判'))
        c10 = sum(1 for r in rows_e if r.get('verified_10d', '') == '正确')
        v20 = sum(1 for r in rows_e if r.get('verified_20d', '') in ('正确', '误判'))
        c20 = sum(1 for r in rows_e if r.get('verified_20d', '') == '正确')
        emotion_hitrates[em] = {
            'total': total_e,
            'verified_5d': v5, 'correct_5d': c5,
            'verified_10d': v10, 'correct_10d': c10,
            'verified_20d': v20, 'correct_20d': c20
        }
    result["emotion_hitrates"] = emotion_hitrates

    indicator_keys = [
        ('vix', 'VIX恐慌指数'),
        ('vix_term', 'VIX期限结构'),
        ('credit_spread', '信用利差'),
        ('ndx_drawdown', 'NDX回撤'),
        ('spx_drawdown', 'SPX回撤'),
        ('ndx_above_ma200', 'NDX站上MA200占比'),
        ('spx_above_ma200', 'SPX站上MA200占比'),
        ('ndx_deviation_ma200', 'NDX偏离MA200'),
        ('spx_deviation_ma200', 'SPX偏离MA200'),
        ('qqq_oi_deviation', 'QQQ持仓偏差'),
        ('spy_oi_deviation', 'SPY持仓偏差'),
        ('on_rrp_deviation', 'ON RRP偏离'),
        ('ndx_spx_deviation', 'NDX/SPX背离'),
        ('iwm_spy_deviation', '小盘背离'),
        ('rate_shock', '利率冲击'),
    ]
    indicator_contributions = []
    if result["daily_logs"]:
        for key, label in indicator_keys:
            values = []
            triggered_count = 0
            for entry in result["daily_logs"]:
                md = entry.get('market_data', {})
                v = md.get(key)
                if v is not None:
                    if isinstance(v, bool):
                        values.append(1 if v else 0)
                        if v:
                            triggered_count += 1
                    elif isinstance(v, (int, float)):
                        values.append(v)
                trig = entry.get('signal', {}).get('triggered_conditions', [])
                for tc in trig:
                    if key in str(tc):
                        triggered_count += 1
            if values:
                avg_val = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
            else:
                avg_val = min_val = max_val = None
            indicator_contributions.append({
                'key': key,
                'label': label,
                'avg': round(avg_val, 2) if avg_val is not None else None,
                'min': round(min_val, 2) if min_val is not None else None,
                'max': round(max_val, 2) if max_val is not None else None,
                'sample_count': len(values),
                'triggered_count': triggered_count
            })
    result["indicator_contributions"] = indicator_contributions

    return jsonify(result)


@app.route('/api/call-gemini', methods=['POST'])
def api_call_gemini():
    print("[Gemini] 路由被调用", flush=True)
    data = request.json
    api_key = data.get('api_key', '')
    model_id = data.get('model_id', '') or 'gemini-2.0-flash'
    base_url = data.get('base_url', '')
    prompt = data.get('prompt', '')

    if not api_key or not prompt:
        return jsonify({"error": "缺少 API Key 或 Prompt"}), 200

    try:
        import requests
        if base_url:
            url = f"{base_url.rstrip('/')}/models/{model_id}:generateContent?key={api_key}"
        else:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        resp = requests.post(url, json=payload, timeout=60)
        resp_json = resp.json()

        if "candidates" in resp_json and len(resp_json["candidates"]) > 0:
            candidate = resp_json["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                text_parts = []
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        text_parts.append(part["text"])
                return jsonify({"result": "\n".join(text_parts)})

        if "error" in resp_json:
            return jsonify({"error": resp_json["error"].get("message", "Gemini API 返回错误")}), 200

        return jsonify({"error": "Gemini 返回格式异常"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 200


@app.route('/api/save-review-result', methods=['POST'])
def api_save_review_result():
    print("[SaveReviewResult] 路由被调用", flush=True)
    data = request.json
    strategy_code = data.get('strategy_code', '')
    analysis_result = data.get('analysis_result', '')
    action = data.get('action', '')
    summary = data.get('summary', '')
    full_analysis = data.get('full_analysis', '')

    project_dir = os.path.dirname(os.path.abspath(__file__))
    from datetime import datetime
    today_str = datetime.now().strftime('%Y-%m-%d')

    if analysis_result == '优化' and action == '采纳':
        if not strategy_code:
            return jsonify({"success": False, "error": "缺少策略代码"}), 200
        strategy_path = os.path.join(project_dir, 'strategy_rules.py')
        try:
            with open(strategy_path, 'w', encoding='utf-8') as f:
                f.write(strategy_code)
            print(f"[SaveReviewResult] 策略已写入 strategy_rules.py", flush=True)
        except Exception as e:
            return jsonify({"success": False, "error": f"写入策略文件失败: {str(e)}"}), 200

    csv_path = os.path.join(project_dir, 'review_log.csv')
    REVIEW_CSV_COLUMNS = ['date', 'result', 'action', 'summary', 'full_analysis']

    rows = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = builtin_csv.DictReader(f)
            for row in reader:
                clean_row = {}
                for k, v in row.items():
                    clean_k = k.replace('\ufeff', '').strip()
                    clean_row[clean_k] = v
                rows.append(clean_row)

    existing_idx = None
    for i, row in enumerate(rows):
        if row.get('date', '').startswith(today_str):
            existing_idx = i
            break

    entry = {
        'date': today_str,
        'result': analysis_result,
        'action': action,
        'summary': summary,
        'full_analysis': full_analysis
    }

    if existing_idx is not None:
        rows[existing_idx] = entry
        print(f"[SaveReviewResult] 覆盖同日复盘记录 idx={existing_idx}", flush=True)
    else:
        rows.append(entry)

    try:
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = builtin_csv.DictWriter(f, fieldnames=REVIEW_CSV_COLUMNS)
            writer.writeheader()
            for row in rows:
                out = {}
                for k in REVIEW_CSV_COLUMNS:
                    out[k] = row.get(k, '')
                writer.writerow(out)
    except Exception as e:
        return jsonify({"success": False, "error": f"保存复盘记录失败: {str(e)}"}), 200

    updated = analysis_result == '优化' and action == '采纳'
    return jsonify({"success": True, "message": "复盘记录已保存", "strategy_updated": updated})


@app.route('/api/review-history')
def api_review_history():
    print("[ReviewHistory] 路由被调用", flush=True)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(project_dir, 'review_log.csv')
    history = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = builtin_csv.DictReader(f)
            for row in reader:
                clean_row = {}
                for k, v in row.items():
                    clean_k = k.replace('\ufeff', '').strip()
                    clean_row[clean_k] = v
                history.append({
                    'date': clean_row.get('date', ''),
                    'result': clean_row.get('result', ''),
                    'action': clean_row.get('action', ''),
                    'summary': clean_row.get('summary', '')
                })
    return jsonify(history)


if __name__ == '__main__':
    port = find_available_port()
    
    # 将端口信息写入文件供启动脚本读取
    port_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.server_port')
    with open(port_file, 'w') as f:
        f.write(str(port))
    
    print("=" * 50)
    print("  美股情绪监测系统 - 服务器启动")
    print("=" * 50)
    print(f"  服务地址: http://127.0.0.1:{port}")
    print(f"  端口: {port}")
    print("=" * 50)
    print()
    app.run(host='127.0.0.1', port=port, debug=False)
