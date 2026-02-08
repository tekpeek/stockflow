#!/bin/bash

set -e

export namespace="default"
source ./src/env/services.env

log_message(){
    local time=$(date +%d-%m-%y-%T)
    local type=$1
    local message=$2
    echo "[$time]----[$type]---- $message"
}

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
        log_message "INFO" "Waiting for $deployment_name :: Elapsed - $ELAPSED"
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done

    if [ $ELAPSED -ge $TIMEOUT ]; then
        log_message "ERROR" "Microservice deployment failed. $deployment_name not in running status!"
        exit 1
    fi
}

if [[ ! -z $1 ]]; then
    export namespace=$1
    if [[ ! -z $2 ]]; then
    log_message "INFO" "Shifting to dev deployment"
    fi
fi

# If namespace is not default, then add "/$namespace" at the end of variables 
# STOCKFLOW_CONTROLLER,SIGNAL_ENGINE,MARKET_INTEL_ENGINE,EVENT_DISPATCHER
if [[ "$namespace" != "default" ]]; then
    STOCKFLOW_CONTROLLER="$STOCKFLOW_CONTROLLER/$namespace"
    SIGNAL_ENGINE="$SIGNAL_ENGINE/$namespace"
fi

log_message "INFO" "Loaded Variables"
log_message "INFO" "STOCKFLOW_CONTROLLER: $STOCKFLOW_CONTROLLER"
log_message "INFO" "SIGNAL_ENGINE: $SIGNAL_ENGINE"
log_message "INFO" "MARKET_INTEL_ENGINE: $MARKET_INTEL_ENGINE"
log_message "INFO" "KUBESNAP: $KUBESNAP"
log_message "INFO" "EVENT_DISPATCHER: $EVENT_DISPATCHER"
log_message "INFO" "Namespace: $namespace"

export DEPLOY_TYPE="$namespace"

namespace_list=($(kubectl get namespaces -o json | jq -r .items[].metadata.name))
if [[ "${namespace_list[*]}" =~ "$namespace "* ]] || [[ "${namespace_list[*]}" =~ *" $namespace" ]] || [[ "${namespace_list[*]}" =~ *" $namespace "* ]]; then
    log_message "INFO" "Namespace: $namespace already present"
else
    log_message "INFO" "Namespace: $namespace not present. creating namespace $namespace"
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
sed "s|__DEPLOY_TYPE__|${DEPLOY_TYPE}|g" kubernetes/deployments/signal-engine-deployment.yaml > signal-engine-deploy.yaml
kubectl -n "$namespace" apply -f signal-engine-deploy.yaml

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
        --from-literal=api-key="${SF_API_KEY}" \
        --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY}"
fi

# Delete and recreate service-urls configmap
kubectl -n "$namespace" delete configmap service-urls --ignore-not-found
kubectl -n "$namespace" create configmap service-urls \
    --from-literal=STOCKFLOW_CONTROLLER="${STOCKFLOW_CONTROLLER}" \
    --from-literal=SIGNAL_ENGINE="${SIGNAL_ENGINE}" \
    --from-literal=MARKET_INTEL_ENGINE="${MARKET_INTEL_ENGINE}" \
    --from-literal=EVENT_DISPATCHER="${EVENT_DISPATCHER}" \
    --from-literal=KUBESNAP="${KUBESNAP}"

# Delete and recreate configmap for cronjob
kubectl -n "$namespace" delete configmap cronjob-config --ignore-not-found
kubectl -n "$namespace" create configmap cronjob-config \
 --from-file=update_tickers/EQUITY_L.csv \
 --from-file=src/core/cronjob-execution.py \
 --from-file=src/core/healthcheck-execution.py \
 --from-file=src/core/smtp_email_trigger.py \
 --from-file=src/prompts/market_analysis_prompt.txt \
 --from-file=templates/email-template.html \
 --from-file=src/core/discovery-engine.py

# delete and recreate the cronjob
kubectl -n "$namespace" delete cronjob signal-check-cronjob --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/cronjobs/signal-check-cronjob.yaml

# Ensure market-data configmap exists for mounting (prevent pod start failure)
if ! kubectl -n "$namespace" get configmap top-stocks-cm > /dev/null 2>&1; then
    log_message "INFO" "Creating empty top-stocks-cm configmap"
    kubectl -n "$namespace" create configmap top-stocks-cm --from-literal=tickers=""
fi

# delete and recreate the discovery cronjob
kubectl -n "$namespace" delete cronjob stock-discovery-cronjob --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/cronjobs/discovery-engine-cronjob.yaml

# create a manual cronjob and check functioning
#kubectl create job signal-check-manual --from=cronjob/signal-check-cronjob

# delete and recreate rbac related service configuration
#kubectl -n "$namespace" delete clusterrolebinding controller-rolebinding --ignore-not-found
#kubectl delete clusterrole controller-role --ignore-not-found
kubectl -n "$namespace" delete serviceaccount controller-svc-acc --ignore-not-found

if [[ "$namespace" != "default" ]]; then
    sed "s|default|$namespace|g" kubernetes/rbac/role-binding.yaml > role-binding.yaml
    sed "s|default|$namespace|g" kubernetes/rbac/stockflow-controller-svc-acc.yaml > svc-acc.yaml
    log_message "INFO" "updated service account role binding with namesapce specific value"
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
sed "s|__DEPLOY_TYPE__|${DEPLOY_TYPE}|g" kubernetes/deployments/stockflow-controller-deployment.yaml > controller-deploy.yaml
kubectl -n "$namespace" apply -f controller-deploy.yaml

# Verifying if the stockflow-controller is in running status
check_deployment "stockflow-controller"

# Sudo privilege task - one time task
# cat kubernetes/configmaps/traefik-config.yaml > /var/lib/rancher/k3s/server/manifests/traefik-config.yaml

# Apply ingress service
if [[ "$namespace" != "default" ]]; then
    sed -e "s|/api|/$namespace/api|g" \
        -e "s|namespace: default|namespace: $namespace|g" \
    kubernetes/services/stockflow-ingress.yaml > ingress.yaml
    log_message "INFO" "updated ingress with namespace specific path"
    kubectl -n "$namespace" apply -f ingress.yaml
else
    kubectl -n "$namespace" apply -f kubernetes/services/stockflow-ingress.yaml
fi

# Delete and recreate market-intel-engine microservice
kubectl -n "$namespace" delete deployment market-intel-engine --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/deployments/market-intel-engine.deployment.yaml

# Delete and recreate market-intel-engine-service
kubectl -n "$namespace" delete service market-intel-engine-service --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/services/market-intel-engine-service.yaml

check_deployment "market-intel-engine"

# Delete and recreate health check cronjob
kubectl -n "$namespace" delete cronjob health-check-cronjob --ignore-not-found
sed -e "s|__DEPLOY_TYPE__|${DEPLOY_TYPE}|g" \
    kubernetes/cronjobs/health-check-cronjob.yaml > health-check-cronjob.yaml
kubectl -n "$namespace" apply -f health-check-cronjob.yaml

# create a manual cronjob and check functioning
kubectl -n "$namespace" create job health-check-manual --from=cronjob/health-check-cronjob

# Deleting junk yaml files
rm *.yaml
log_message "INFO" "Deleted junk yaml files"
