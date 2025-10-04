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
    exit 1
else
    log_message "INFO" "Signal Engine Status : $signal_engine_health"
fi

stockflow_controller_health=$(curl -s -X GET https://tekpeek.duckdns.org/api/admin/health | jq -r .status)
if [[ "$stockflow_controller_health" != "OK" ]]; then
    log_message "ERROR" "Health Check API not working for Stockflow Controller!"
    exit 1
else
    log_message "INFO" "Stockflow Controller Status : $stockflow_controller_health"
fi

# Dummy Signal Generation Test
dummy_signal=$(curl -s -X GET https://tekpeek.duckdns.org/api/RELIANCE.NS | jq -r .buy)
if [[ "$dummy_signal" != "true" ]] && [[ "$dummy_signal" != "false" ]]; then
    log_message "ERROR" "API Error! Endpoint [/api] not working."
else
    log_message "INFO" "Endpoint [/api] check completed."
fi

# Maintenance API Check
maintenance_status=$(curl -s -X GET https://tekpeek.duckdns.org/api/admin/maintenance/status | jq -r .status)
if [[ "$maintenance_status" != "on" ]] && [[ "$maintenance_status" != "off" ]]; then
    log_message "ERROR" "API Error! Endpoint [/api/admin/maintenance/status] not working."
else
    log_message "INFO" "Endpoint [/api/admin/maintenance/status] check completed."
fi

log_message "INFO" "Test Deployment Execution Completed."