import top_500_nse_tickers
import smtp_email_trigger as email_trigger
import os
import json

def fetch_openai_analysis(url, prompt, retries=3, timeout=240):
    output=""
    for attempt in range(retries):
        # Properly escape the prompt for JSON
        json_data = json.dumps({"prompt": prompt})
        print("json_data: ",json_data)
        output = os.popen(f"curl -s --max-time {timeout} -X POST -H 'Content-Type: application/json' {url} -d '{json_data}' | jq -r .").read().strip()
        print(output)
        output = json.dumps(output)
        print(output)
        result = os.popen(f"echo {output} | jq -r .result").read().strip()
        print(f"output for {url}: {output} : attempt: {attempt}")
        print("*****************")
        if result == "failed":
            continue
        else:
            return output  # Wait 1 second before retrying
    return output

def identify_stocks():
    final_buy_list = []
    error_list = []
    ticker_list= []
    for ticker in top_500_nse_tickers.top_500_nse_tickers:
        output=os.popen(f"curl -s https://tekpeek.duckdns.org/api/{ticker} | jq -r .").read().strip()
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
    with open("../prompts/market_analysis_prompt.txt") as file:
        prompt = file.read()
        prompt = prompt.replace("__TICKER_LIST__",str(ticker_list))
    file.close()
    ai_result = fetch_openai_analysis("http://10.42.0.188:8000/chat",prompt)
    print(ai_result)

if __name__ == "__main__":
    list_data = identify_stocks()
    perform_market_sentiment_analysis(list_data[2])
    exit(0)
    if len(list_data[0])>0 or len(list_data[1])>0:
        email_trigger.send_email(list_data[0],list_data[1])