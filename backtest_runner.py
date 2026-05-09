import sys
import json
import io
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super().default(obj)


def progress_callback(pct, msg):
    print(f"PROGRESS:{json.dumps({'progress': pct, 'message': msg})}", flush=True)

def main():
    if len(sys.argv) < 3:
        print("Usage: python backtest_runner.py <start_date> <end_date> [options]", file=sys.stderr)
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]

    kwargs = {}
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--initial-capital' and i + 1 < len(sys.argv):
            kwargs['initial_capital'] = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--initial-position' and i + 1 < len(sys.argv):
            kwargs['initial_position'] = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--daily-sip' and i + 1 < len(sys.argv):
            kwargs['daily_sip'] = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--cash-yield' and i + 1 < len(sys.argv):
            kwargs['cash_yield'] = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--buy-cap' and i + 1 < len(sys.argv):
            kwargs['buy_cap'] = float(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    try:
        from backtest import run_backtest
        report = run_backtest(start_date, end_date, progress_callback=progress_callback, **kwargs)
        print("REPORT_START", end="", flush=True)
        print(json.dumps(report, ensure_ascii=False, cls=NumpyEncoder), end="", flush=True)
        print("REPORT_END", flush=True)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
