#!/bin/bash

set -e

export namespace="default"

check_deployment() {
    deployment_name=$1
    INTERVAL=5
    TIMEOUT=250
    ELAPSED=0
    deployment_status=$(kubectl -n "$namespace" get deploy $deployment_name -o json | jq -r '.status.conditions[]' | jq -r 'select(.type == "Available").status')
    while [ $ELAPSED -lt $TIMEOUT ]; do
        deployment_status=$(kubectl -n "$namespace" get deploy $deployment_name -o json | jq -r '.status.conditions[]' | jq -r 'select(.type == "Available").status')
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

if [[ ! -z $1 ]]; then
    export namespace=$1
fi
echo "Namespace set to $namespace"
namespace_list=($(kubectl get namespaces -o json | jq -r .items[].metadata.name))
if [[ "${namespace_list[*]}" =~ "$namespace "* ]] || [[ "${namespace_list[*]}" =~ *" $namespace" ]] || [[ "${namespace_list[*]}" =~ *" $namespace "* ]]; then
    echo "$namespace already present"
else
    echo "$namespace not present. creating namespace $namespace"
    kubectl create namespace $namespace
fi

# Delete and recreate strategy related configuration secret
kubectl -n "$namespace" delete secret generic strategy-config --ignore-not-found
kubectl -n "$namespace" create secret generic strategy-config \
    --from-literal=interval="1d" \
    --from-literal=period=14 \
    --from-literal=window=20 \
    --from-literal=num_std=2

# Delete and recreate maintenance-config configmap
kubectl -n "$namespace" delete configmap maintenance-config --ignore-not-found
kubectl -n "$namespace" create configmap maintenance-config \
    --from-literal=status="off"

# Delete old deployment and deploy the signal engine server
kubectl -n "$namespace" delete deployment signal-engine --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/deployments/signal-engine-deployment.yaml

# Verifying if the signal-engine is in running status
check_deployment "signal-engine"

# Delete the old service and deploy the signal engine service
kubectl -n "$namespace" delete service signal-engine-service --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/services/signal-engine-service.yaml

# Delete and recreate smtp-credentials secret
if [[ ! -z "${SMTP_PASSWORD}" ]]; then

    kubectl -n "$namespace" delete secret smtp-credentials --ignore-not-found
    kubectl -n "$namespace" create secret generic smtp-credentials \
        --from-literal=smtp-password="${SMTP_PASSWORD}" \
        --from-literal=smtp-user="noreply.avinash.s@gmail.com" \
        --from-literal=smtp-port="587" \
        --from-literal=smtp-host="smtp.gmail.com"
fi

if [[ ! -z "${SF_API_KEY}" ]]; then
    kubectl -n "$namespace" delete secret api-credentials --ignore-not-found
    kubectl -n "$namespace" create secret generic api-credentials \
        --from-literal=api-key="${SF_API_KEY}"
fi

# Delete and recreate configmap for cronjob
kubectl -n "$namespace" delete configmap cronjob-config --ignore-not-found
kubectl -n "$namespace" create configmap cronjob-config \
 --from-file=src/core/top_500_nse_tickers.py \
 --from-file=src/core/cronjob-execution.py \
 --from-file=src/core/healthcheck-execution.py \
 --from-file=src/core/smtp_email_trigger.py

# delete and recreate the cronjob
kubectl -n "$namespace" delete cronjob signal-check-cronjob --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/cronjobs/signal-check-cronjob.yaml

# create a manual cronjob and check functioning
#kubectl create job signal-check-manual --from=cronjob/signal-check-cronjob

# delete and recreate rbac related service configuration
#kubectl -n "$namespace" delete clusterrolebinding controller-rolebinding --ignore-not-found
#kubectl delete clusterrole controller-role --ignore-not-found
kubectl -n "$namespace" delete serviceaccount controller-svc-acc --ignore-not-found

if [[ "$namespace" != "default" ]]; then
    sed "s|default|$namespace|g" kubernetes/rbac/role-binding.yaml > role-binding.yaml
    sed "s|default|$namespace|g" kubernetes/rbac/stockflow-controller-svc-acc.yaml > svc-acc.yaml
    echo "updated service account role binding with namesapce specific value"
    kubectl -n "$namespace" apply -f role-binding.yaml
    kubectl -n "$namespace" apply -f svc-acc.yaml
else
    kubectl -n "$namespace" apply -f kubernetes/rbac/stockflow-controller-svc-acc.yaml
    kubectl -n "$namespace" apply -f kubernetes/rbac/role-binding.yaml
fi
kubectl apply -f kubernetes/rbac/svc-acc-cluster-role.yaml

# Delete and recreate stockflow-controller-service
kubectl -n "$namespace" delete service sf-ctrl-service --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/services/stockflow-controller-service.yaml

# Delete and recreate stockflow-controller microservice
kubectl -n "$namespace" delete deployment stockflow-controller --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/deployments/stockflow-controller-deployment.yaml

# Verifying if the stockflow-controller is in running status
check_deployment "stockflow-controller"

# Sudo privilege task - one time task
# cat kubernetes/configmaps/traefik-config.yaml > /var/lib/rancher/k3s/server/manifests/traefik-config.yaml

# Apply ingress service
if [[ "$namespace" != "default" ]]; then
    sed -e "s|/api|/$namespace/api|g" \
        -e "s|namespace: default|namespace: $namespace|g" \
    kubernetes/services/stockflow-ingress.yaml > ingress.yaml
    echo "updated ingress with namespace specific path"
    kubectl -n "$namespace" apply -f ingress.yaml
else
    kubectl -n "$namespace" apply -f kubernetes/services/stockflow-ingress.yaml
fi

# Delete and recreate health check cronjob
kubectl -n "$namespace" delete cronjob health-check-cronjob --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/cronjobs/health-check-cronjob.yaml

# create a manual cronjob and check functioning
kubectl -n "$namespace" create job health-check-manual --from=cronjob/health-check-cronjob
