# Reads the top 500 by volume tickers and creates a list of top 300

top_300_tickers = []

with open('top_500_volume_stocks_desc.txt', 'r') as f:
    for i, line in enumerate(f):
        if i >= 50:
            break
        ticker = line.strip()
        if ticker:
            top_300_tickers.append(ticker+".NS")

# For demonstration, print the list or save it as needed
print(top_300_tickers) 