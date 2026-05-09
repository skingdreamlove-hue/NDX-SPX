import json

with open('nasdaq100_chart.html', encoding='utf-8') as f:
    html = f.read()

# Plotly injects data like: Plotly.newPlot(..., [{"x": ...}], {"title": ...})
import re
m = re.search(r'Plotly\.newPlot\(\s*\'[\w\-]+\'\s*,\s*(\[.*?\])\s*,\s*(\{.*?\})\s*,\s*(\{.*?\})\s*\)', html, re.S)
if m:
    data = json.loads(m.group(1))
    for i, trace in enumerate(data):
        print(f"Trace {i}: name={trace.get('name')}, yaxis={trace.get('yaxis')}, type={trace.get('type')}, length of y={len(trace.get('y', []))}")
        print(f"First 5 y values: {trace.get('y', [])[:5]}")
else:
    print("Plotly.newPlot not found")
