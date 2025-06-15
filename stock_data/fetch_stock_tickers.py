import pandas as pd
import yfinance as yf
from tqdm import tqdm

# Load the Nifty 500 CSV (already downloaded from NSE)
file_path = "ind_nifty500list.csv"
df = pd.read_csv(file_path)

# Extract symbols
symbols = df['Symbol'].unique().tolist()

# NSE uses ".NS" suffix in yfinance
symbols_ns = [sym + ".NS" for sym in symbols]

volume_data = []

# Fetch volume data from yfinance
print("Fetching volume data from Yahoo Finance...")
for symbol in tqdm(symbols_ns):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if not data.empty:
            latest_volume = data['Volume'].iloc[-1]
            volume_data.append((symbol.replace('.NS', ''), latest_volume))
    except Exception as e:
        print(f"Failed for {symbol}: {e}")
        continue

# Sort by volume descending
sorted_by_volume = sorted(volume_data, key=lambda x: x[1], reverse=True)

# Extract top 500 symbols
top_500_symbols = [s[0] for s in sorted_by_volume[:500]]

# Print result
print("\nTop Nifty 500 stocks by volume:")
print(top_500_symbols)

# Optional: Save to file
with open("top_500_volume_stocks.txt", "w") as f:
    for sym in top_500_symbols:
        f.write(sym + "\n")
print("Saved to top_500_volume_stocks.txt")
