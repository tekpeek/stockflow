#!/bin/bash

log_message(){
    local time=$(date +%d-%m-%y-%T)
    local type=$1
    local message=$2
    echo "[$time]----[$type]---- $message"
}

log_message "INFO" "Pulling Helm chart dependencies"

mkdir -p ../event-dispatcher
git clone -b release_26.3.4 https://github.com/tekpeek/event-dispatcher.git/ ../event-dispatcher

log_message "INFO" "Building Helm chart dependencies"

helm dependency build .

log_message "INFO" "Starting deployment"

export OPENAI_API_KEY=$1
export SMTP_PASSWORD=$2
export API_KEY=$3
export NAMESPACE=$4
export IMAGE_VERSION=$5
export GEMINI_API_KEY=$6
log_message "INFO" "Setting environment variables"
log_message "INFO" "NAMESPACE: $NAMESPACE"
log_message "INFO" "IMAGE_VERSION: $IMAGE_VERSION"

helm lint . --set namespace=$NAMESPACE
log_message "INFO" "Linting helm chart completed."

if [ "$NAMESPACE" == "default" ]; then
    helm upgrade stockflow --install . -n $NAMESPACE \
        --set openaiApiKey=$OPENAI_API_KEY \
        --set smtpPassword="$SMTP_PASSWORD" \
        --set apiKey=$API_KEY \
        --set namespace=$NAMESPACE \
        --set imageVersion=$IMAGE_VERSION \
        --set geminiApiKey=$GEMINI_API_KEY \
        --set event-dispatcher.namespace=$NAMESPACE \
        --set event-dispatcher.imageVersion=26.3.4 \
        --set event-dispatcher.slackWebhookStockflow=$SLACK_WEBHOOK_STOCKFLOW

else
    helm upgrade stockflow --install . -n $NAMESPACE \
        --set openaiApiKey=$OPENAI_API_KEY \
        --set smtpPassword="$SMTP_PASSWORD" \
        --set apiKey=$API_KEY \
        --set namespace=$NAMESPACE \
        --set apiPrefix="/$NAMESPACE" \
        --set imageVersion=$IMAGE_VERSION \
        --set geminiApiKey=$GEMINI_API_KEY \
        --set event-dispatcher.namespace=$NAMESPACE \
        --set event-dispatcher.imageVersion=26.3.4 \
        --set event-dispatcher.slackWebhookStockflow=$SLACK_WEBHOOK_STOCKFLOW
fi

log_message "INFO" "Deployment completed."

# Clean up
rm -rf ../event-dispatcher
rm -rf charts

log_message "INFO" "Clean up completed."

# Execution command
### ./deploy_helm.sh "$OPENAI_API_KEY" "$SMTP_PASSWORD" "$API_KEY" "dev" "dev" "$GEMINI_API_KEY"