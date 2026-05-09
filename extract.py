import json
import re
import base64
import numpy as np

html = open('nasdaq100_chart.html', encoding='utf-8').read()
m = re.search(r'Plotly\.newPlot\(\s*"[^"]+"\s*,\s*(\[.*\])\s*,\s*(\{.*\})\s*,\s*(\{.*\})\s*\)', html, re.S)
if m:
    data = json.loads(m.group(1))
    for i, t in enumerate(data):
        x = t.get('x')
        print(f"Trace {i} {t['name']}: type(x)={type(x)}")
        if isinstance(x, dict):
            print(f"  keys={list(x.keys())}")
        elif isinstance(x, list):
            print(f"  len={len(x)}, first_x={x[:3]}")
