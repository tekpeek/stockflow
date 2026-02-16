#!/bin/bash

log_message(){
    local time=$(date +%d-%m-%y-%T)
    local type=$1
    local message=$2
    echo "[$time]----[$type]---- $message"
}

log_message "INFO" "Starting deployment"

rm -rf files/*
mkdir -p files
log_message "INFO" "Files directory cleaned"
log_message "INFO" "Copying files to files directory"
cp -r ../src/core/*.py files/
cp ../src/prompts/market_analysis_prompt.txt files/market_analysis_prompt.txt
cp ../templates/email-template.html files/email-template.html
cp ../update_tickers/EQUITY_L.csv files/EQUITY_L.csv
log_message "INFO" "Files copied to files directory"

export OPENAI_API_KEY=$1
export SMTP_PASSWORD=$2
export API_KEY=$3
export NAMESPACE=$4
export IMAGE_VERSION=$5
log_message "INFO" "Setting environment variables"
log_message "INFO" "NAMESPACE: $NAMESPACE"
log_message "INFO" "IMAGE_VERSION: $IMAGE_VERSION"

helm lint . --set namespace=$NAMESPACE
log_message "INFO" "Linting helm chart completed."

if [ "$NAMESPACE" == "default" ]; then
    helm upgrade stockflow --install . -n $NAMESPACE \
        --set openaiApiKey=$OPENAI_API_KEY \
        --set smtpPassword=$SMTP_PASSWORD \
        --set apiKey=$API_KEY \
        --set namespace=$NAMESPACE \
        --set imageVersion=$IMAGE_VERSION
else
    helm upgrade stockflow --install . -n $NAMESPACE \
        --set openaiApiKey=$OPENAI_API_KEY \
        --set smtpPassword="$SMTP_PASSWORD" \
        --set apiKey=$API_KEY \
        --set namespace=$NAMESPACE \
        --set apiPrefix="/$NAMESPACE" \
        --set imageVersion=$IMAGE_VERSION
fi

rm -rf files/
log_message "INFO" "Files directory cleaned. Deployment completed."

# Execution command
### ./deploy_helm.sh "$OPENAI_API_KEY" "$SMTP_PASSWORD" "$API_KEY" "dev"