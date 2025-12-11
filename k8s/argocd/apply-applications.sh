#!/bin/bash

# Script to apply ArgoCD Application manifests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

kubectl apply -f "${SCRIPT_DIR}/frontend-application.yaml"
kubectl apply -f "${SCRIPT_DIR}/backend-application.yaml"
