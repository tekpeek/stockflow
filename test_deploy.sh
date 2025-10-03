#!/bin/bash
log_message(){
    local time=$(date +%d-%m-%y-%T)
    local type=$1
    local message=$2
    echo "[$time]----[$type]---- $message"
}

# Health Status check for public facing services
signal_engine_health=$(curl -s -X GET https://tekpeek.duckdns.org/api/health | jq -r .status)
if [[ "$signal_engine_health" != "OK" ]]; then
    log_message "ERROR" "Health Check API not working for Signal Engine!"
else
    log_message "INFO" "Signal Engine Status : $signal_engine_health"
fi

stockflow_controller_health=$(curl -s -X GET https://tekpeek.duckdns.org/api/admin/health | jq -r .status)
if [[ "$stockflow_controller_health" != "OK" ]]; then
    log_message "ERROR" "Health Check API not working for Stockflow Controller!"
else
    log_message "INFO" "Stockflow Controller Status : $stockflow_controller_health"
fi

log_message "INFO" "Test Deployment Execution Completed."