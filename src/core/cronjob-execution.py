import top_500_nse_tickers
import smtp_email_trigger as email_trigger
import os

def check_service_health(url, file, retries=3, timeout=240):
    for attempt in range(retries):
        output = os.popen(f"curl -s --max-time {timeout} -X POST -H 'Content-Type: application/json' {url} -d @{file} | jq -r .").read().strip()
        print(f"output for {url}: {output} : attempt: {attempt}")
        print("*****************")
        if status == "OK":
            return True
        time.sleep(1)  # Wait 1 second before retrying
    return False

def identify_stocks():
    final_buy_list = []
    error_list = []
    ticket_list= []
    for ticker in top_500_nse_tickers.top_500_nse_tickers:
        output=os.popen(f"curl -s http://signal-engine-service:8000/api/{ticker} | jq -r .").read().strip()
        signals = os.popen(f"echo '{output}' | jq -r .signals").read().strip()
        strength = os.popen(f"echo '{output}' | jq -r .strength").read().strip()
        reasons = os.popen(f"echo '{output}' | jq -r .reason").read().strip()
        
        if "true" not in output and "false" not in output:
            error_list.append(ticker)
        if "true" in output:
            print(f"{ticker}")
            ticker_list.append(ticker)
            final_buy_list.append([ticker, signals, strength, reasons])

    return [final_buy_list, error_list, ticker_list]

def perform_market_sentiment_analysis(ticker_list):
    prompt=""
    if len(ticker_list) == 0:
        ticker_list="""NULL.
As the technical analysis microservice has returned empty list, analyse the current indian stock market and suggest some stocks
that will grow in the coming 2-7 days."""
    with open("market_analysis_prompt.txt") as file:
        prompt = file.read()
        prompt = prompt.replace("__TICKER_LIST__",ticker_list)
    



    

if __name__ == "__main__":
    list_data = identify_stocks()
    perform_market_sentiment_analysis(list_data[2])
    if len(list_data[0])>0 or len(list_data[1])>0:
        email_trigger.send_email(list_data[0],list_data[1])