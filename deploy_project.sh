#!/bin/bash

# Build and push image to repository
docker build -t kingaiva/signal-engine:dev . --no-cache
docker image push kingaiva/signal-engine:dev

# Delete old deployment and deploy the signal engine server
kubectl delete deployment signal-engine --ignore-not-found
kubectl apply -f signal-engine-deployment.yaml

# Delete the old service and deploy the signal engine service
kubectl delete service signal-engine-service --ignore-not-found
kubectl apply -f signal-engine-service.yaml

# Delete and recreate smtp-credentials secret
#kubectl delete secret smtp-credentials --ignore-not-found
#kubectl create secret generic smtp-credentials \
#    --from-literal=smtp-password="<Gmail App Password>" \
#    --from-literal=smtp-user="noreply.avinash.s@gmail.com" \
#    --from-literal=smtp-port="587" \
#    --from-literal=smtp-host="smtp.gmail.com"

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