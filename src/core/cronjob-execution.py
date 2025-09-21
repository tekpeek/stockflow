import top_500_nse_tickers
import smtp_email_trigger as email_trigger
import os
import json
import requests

def fetch_openai_analysis(url, prompt, retries=3, timeout=240):
    for attempt in range(retries):
        try:
            response = requests.post(url,json={"prompt":prompt},timeout=timeout)
            parsed_response = response.json()
            keys = list(parsed_response.keys())
            if "mie_analysis" not in keys:
                parsed_response = json.loads(parsed_response[keys[0]])
            print(parsed_response)
            status = parsed_response["mie_analysis"]
            status = status["status"]
        except Exception as e:
            print(f"Error parsing output from openai. Error : {e}")
            raise
        print(f"output for {url}: {parsed_response} : attempt: {attempt}")
        print("*****************")
        if status == "failed":
            continue
        else:
            return parsed_response # Wait 1 second before retrying
    if status == "failed":
        raise Exception(f"Analysis failed. Response : {parsed_response}")
    return parsed_response

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
    with open("/home/ubuntu/app/market_analysis_prompt.txt") as file:
        prompt = file.read()
        prompt = prompt.replace("__TICKER_LIST__",str(ticker_list))
    file.close()
    mie_analysis = fetch_openai_analysis("http://market-intel-engine-service:8000/chat",prompt)
    final_list=[]
    for i in range(len(mie_analysis["mie_analysis"]["results"])):
        if mie_analysis["mie_analysis"]["results"][i]["buy_rating"] >=5:
            final_list.append(mie_analysis["mie_analysis"]["results"][i])
    return final_list

if __name__ == "__main__":
    list_data = identify_stocks()
    final_list = perform_market_sentiment_analysis(list_data[0])
    if len(final_list)>0:
        email_trigger.send_email(final_list,[])
        print("Email Sent")