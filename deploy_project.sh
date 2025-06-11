#!/bin/bash

# Delete and recreate strategy related configuration secret
kubectl delete secret generic strategy-config --ignore-not-found
kubectl create secret generic strategy-config \
    --from-literal=interval="1d" \
    --from-literal=period=14 \
    --from-literal=window=20 \
    --from-literal=num_std=2

# Delete old deployment and deploy the signal engine server
kubectl delete deployment signal-engine --ignore-not-found
kubectl apply -f signal-engine-deployment.yaml

# Verifying if the signal-engine is in running status
INTERVAL=5
TIMEOUT=250
ELAPSED=0
deployment_status=$(kubectl get deploy signal-engine -o json | jq -r '.status.conditions[]' | jq -r 'select(.type == "Available").status')
while [ $ELAPSED -lt $TIMEOUT ]; do
    deployment_status=$(kubectl get deploy signal-engine -o json | jq -r '.status.conditions[]' | jq -r 'select(.type == "Available").status')
    if [[ "${deployment_status^^}" == "TRUE" ]]; then
        break
    fi
    echo "Waiting for signal-engine :: Elapsed - $ELAPSED"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "Microservice deployment failed. signal-engine not in running status!"
    exit 1
fi

# Delete the old service and deploy the signal engine service
kubectl delete service signal-engine-service --ignore-not-found
kubectl apply -f signal-engine-service.yaml

# Delete and recreate smtp-credentials secret
kubectl delete secret smtp-credentials --ignore-not-found
kubectl create secret generic smtp-credentials \
    --from-literal=smtp-password="${SMTP_PASSWORD}" \
    --from-literal=smtp-user="noreply.avinash.s@gmail.com" \
    --from-literal=smtp-port="587" \
    --from-literal=smtp-host="smtp.gmail.com"

# Delete and recreate configmap for cronjob
kubectl delete configmap cronjob-config --ignore-not-found
kubectl create configmap cronjob-config \
 --from-file=top_300_nse_tickers.py \
 --from-file=cronjob-execution.py \
 --from-file=smtp_email_trigger.py

# delete and recreate the cronjob
kubectl delete cronjob signal-check-cronjob --ignore-not-found
kubectl apply -f signal-check-cronjob.yaml

# create a manual cronjob and check functioning
kubectl create job signal-check-manual --from=cronjob/signal-check-cronjob