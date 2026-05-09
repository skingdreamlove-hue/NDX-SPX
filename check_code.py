
with open('generate_charts.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Looking for save part...")
for i, line in enumerate(lines):
    if 'qqq_pcr_ma20' in line:
        print(f"Line {i+1}: {line.strip()}")
    if 'qqq_volume_ratio' in line:
        print(f"Line {i+1}: {line.strip()}")
