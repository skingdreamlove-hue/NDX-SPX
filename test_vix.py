
import yfinance as yf
from datetime import datetime

print("Testing get_vix_data()...")
vix = yf.Ticker("^VIX")
hist = vix.history(period="max", interval="1d")
print(f"VIX data loaded successfully, {len(hist)} days")
print(f"Latest date: {hist.index[-1]}")
print(f"Latest close: {hist['Close'].iloc[-1]}")
