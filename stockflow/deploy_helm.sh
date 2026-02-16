#!/bin/bash
ls -al
rm -rf files/*
mkdir -p files
cp -r ../src/core/*.py files/
cp ../src/prompts/market_analysis_prompt.txt files/market_analysis_prompt.txt
cp ../templates/email-template.html files/email-template.html
cp ../update_tickers/EQUITY_L.csv files/EQUITY_L.csv

export OPENAI_API_KEY=$1
export SMTP_PASSWORD=$2
export API_KEY=$3
export NAMESPACE=$4

helm lint . --set namespace=$NAMESPACE

if [ "$NAMESPACE" == "default" ]; then
    helm upgrade stockflow --install . -n $NAMESPACE \
        --set openaiApiKey=$OPENAI_API_KEY \
        --set smtpPassword=$SMTP_PASSWORD \
        --set apiKey=$API_KEY \
        --set namespace=$NAMESPACE
else
    helm upgrade stockflow --install . -n $NAMESPACE \
        --set openaiApiKey=$OPENAI_API_KEY \
        --set smtpPassword="$SMTP_PASSWORD" \
        --set apiKey=$API_KEY \
        --set namespace=$NAMESPACE \
        --set apiPrefix="/$NAMESPACE"
fi

rm -rf files/


# Execution command
### ./deploy_helm.sh "$OPENAI_API_KEY" "$SMTP_PASSWORD" "$API_KEY" "dev"