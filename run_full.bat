
@echo off
cd /d d:\web\美股情绪监测
python generate_charts.py > full_output.txt 2>&1
echo Done! Output saved to full_output.txt
type full_output.txt
pause
