#!/bin/bash

set -e

export namespace="default"

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
log_message "INFO" "Namespace set to $namespace"

export DEPLOY_TYPE="$namespace"

namespace_list=($(kubectl get namespaces -o json | jq -r .items[].metadata.name))
if [[ "${namespace_list[*]}" =~ "$namespace "* ]] || [[ "${namespace_list[*]}" =~ *" $namespace" ]] || [[ "${namespace_list[*]}" =~ *" $namespace "* ]]; then
    log_message "INFO" "$namespace already present"
else
    log_message "INFO" "$namespace not present. creating namespace $namespace"
    exit 1
fi

# Create secret to store webhooks
kubectl -n $namespace delete secret slack-webhooks --ignore-not-found
kubectl -n $namespace create secret generic slack-webhooks \
    --from-literal=stockflow="${SLACK_WEBHOOK_STOCKFLOW}"

# Delete old deployment and deploy the event-dispatcher server
kubectl -n "$namespace" delete deployment event-dispatcher --ignore-not-found
sed "s|__DEPLOY_TYPE__|${DEPLOY_TYPE}|g" kubernetes/deployments/event-dispatcher-deployment.yaml > event-dispatcher-deploy.yaml
kubectl -n "$namespace" apply -f event-dispatcher-deploy.yaml

# Verifying if the event-dispatcher is in running status
check_deployment "event-dispatcher"

# Delete the old service and deploy the signal engine service
kubectl -n "$namespace" delete service event-dispatcher-service --ignore-not-found
kubectl -n "$namespace" apply -f kubernetes/services/event-dispatcher-service.yaml