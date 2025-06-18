import top_500_nse_tickers
import smtp_email_trigger as email_trigger
import os

def identify_stocks():
    final_buy_list = []
    error_list = []
    for ticker in top_500_nse_tickers.top_500_nse_tickers:
        output=os.popen(f"curl -s http://signal-engine-service:8000/{ticker} | jq -r .").read().strip()
        signals = os.popen(f"echo '{output}' | jq -r .signals").read().strip()
        strength = os.popen(f"echo '{output}' | jq -r .strength").read().strip()
        reasons = os.popen(f"echo '{output}' | jq -r .reason").read().strip()
        
        if "true" not in output and "false" not in output:
            error_list.append(ticker)
        if "true" in output:
            print(f"{ticker}")
            final_buy_list.append([ticker, signals, strength, reasons])

    return [final_buy_list, error_list]

if __name__ == "__main__":
    list_data = identify_stocks()
    if len(list_data[0])>0 or len(list_data[1])>0:
        email_trigger.send_email(list_data[0],list_data[1])