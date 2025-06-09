#!/bin/bash

# Check if deployment name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <deployment-name>"
    exit 1
fi

DEPLOYMENT_NAME=$1
TIMEOUT=300  # 5 minutes timeout
INTERVAL=5   # Check every 5 seconds
ELAPSED=0

echo "Waiting for deployment $DEPLOYMENT_NAME to be ready..."

while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
    # Get the deployment status
    STATUS=$(kubectl get deployment "$DEPLOYMENT_NAME" -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null)
    
    if [ "$STATUS" = "True" ]; then
        echo "Deployment $DEPLOYMENT_NAME is now running!"
        exit 0
    fi
    
    # Get the current replicas and available replicas
    CURRENT_REPLICAS=$(kubectl get deployment "$DEPLOYMENT_NAME" -o jsonpath='{.status.availableReplicas}' 2>/dev/null)
    DESIRED_REPLICAS=$(kubectl get deployment "$DEPLOYMENT_NAME" -o jsonpath='{.status.replicas}' 2>/dev/null)
    
    # Handle empty values
    CURRENT_REPLICAS=${CURRENT_REPLICAS:-0}
    DESIRED_REPLICAS=${DESIRED_REPLICAS:-0}
    
    echo "Current replicas: $CURRENT_REPLICAS/$DESIRED_REPLICAS"
    
    sleep "$INTERVAL"
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "Timeout waiting for deployment $DEPLOYMENT_NAME to be ready"
exit 1 