#!/bin/bash

set -e

check_deployment() {
    deployment_name=$1
    INTERVAL=5
    TIMEOUT=250
    ELAPSED=0
    deployment_status=$(kubectl get deploy $deployment_name -o json | jq -r '.status.conditions[]' | jq -r 'select(.type == "Available").status')
    while [ $ELAPSED -lt $TIMEOUT ]; do
        deployment_status=$(kubectl get deploy $deployment_name -o json | jq -r '.status.conditions[]' | jq -r 'select(.type == "Available").status')
        if [[ "${deployment_status^^}" == "TRUE" ]]; then
            break
        fi
        echo "Waiting for $deployment_name :: Elapsed - $ELAPSED"
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done

    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "Microservice deployment failed. $deployment_name not in running status!"
        exit 1
    fi
}

# Delete and recreate strategy related configuration secret
kubectl delete secret generic strategy-config --ignore-not-found
kubectl create secret generic strategy-config \
    --from-literal=interval="1d" \
    --from-literal=period=14 \
    --from-literal=window=20 \
    --from-literal=num_std=2

# Delete old deployment and deploy the signal engine server
kubectl delete deployment signal-engine --ignore-not-found
kubectl apply -f kubernetes/deployments/signal-engine-deployment.yaml

# Verifying if the signal-engine is in running status
check_deployment "signal-engine"

# Delete the old service and deploy the signal engine service
kubectl delete service signal-engine-service --ignore-not-found
kubectl apply -f kubernetes/services/signal-engine-service.yaml

# Delete and recreate smtp-credentials secret
if [[ ! -z "${SMTP_PASSWORD}" ]]; then

    kubectl delete secret smtp-credentials --ignore-not-found
    kubectl create secret generic smtp-credentials \
        --from-literal=smtp-password="${SMTP_PASSWORD}" \
        --from-literal=smtp-user="noreply.avinash.s@gmail.com" \
        --from-literal=smtp-port="587" \
        --from-literal=smtp-host="smtp.gmail.com"
fi

# Delete and recreate configmap for cronjob
kubectl delete configmap cronjob-config --ignore-not-found
kubectl create configmap cronjob-config \
 --from-file=src/core/top_500_nse_tickers.py \
 --from-file=src/core/cronjob-execution.py \
 --from-file=src/core/healthcheck-execution.py \
 --from-file=src/core/smtp_email_trigger.py

# delete and recreate the cronjob
kubectl delete cronjob signal-check-cronjob --ignore-not-found
kubectl apply -f kubernetes/cronjobs/signal-check-cronjob.yaml

# create a manual cronjob and check functioning
#kubectl create job signal-check-manual --from=cronjob/signal-check-cronjob

# delete and recreate rbac related service configuration
kubectl delete clusterrolebinding controller-rolebinding --ignore-not-found
kubectl delete clusterrole controller-role --ignore-not-found
kubectl delete serviceaccount controller-svc-acc --ignore-not-found

kubectl apply -f kubernetes/rbac/stockflow-controller-svc-acc.yaml
kubectl apply -f kubernetes/rbac/svc-acc-cluster-role.yaml
kubectl apply -f kubernetes/rbac/role-binding.yaml

# Delete and recreate stockflow-controller microservice
kubectl delete deployment stockflow-controller --ignore-not-found
kubectl apply -f kubernetes/deployments/stockflow-controller-deployment.yaml

# Verifying if the stockflow-controller is in running status
check_deployment "stockflow-controller"

# Sudo privilege task - one time task
# cat kubernetes/configmaps/traefik-config.yaml > /var/lib/rancher/k3s/server/manifests/traefik-config.yaml

# Apply ingress service
kubectl apply -f kubernetes/services/stockflow-ingress.yaml

# Delete and recreate health check cronjob
kubectl delete cronjob health-check-cronjob --ignore-not-found
kubectl apply -f kubernetes/cronjobs/health-check-cronjob.yaml

# create a manual cronjob and check functioning
kubectl create job health-check-manual --from=cronjob/health-check-cronjob
