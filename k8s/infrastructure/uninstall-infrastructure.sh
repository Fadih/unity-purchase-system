#!/bin/bash

# Infrastructure Uninstallation Script
# Removes Kafka, MongoDB, KEDA, and Argo CD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARGOCD_MANIFEST_URL="https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"

echo "🗑️  Starting infrastructure uninstallation..."
echo ""

# Uninstall Argo CD
echo "📦 Uninstalling Argo CD..."
if kubectl get namespace argocd &>/dev/null; then
  echo "   Deleting Argo CD resources..."
  kubectl delete -n argocd -f "${ARGOCD_MANIFEST_URL}" 2>/dev/null || echo "   ⚠️  Some Argo CD resources may have already been deleted"
  
  # Wait a bit for resources to be deleted
  sleep 5
  
  # Delete namespace if it still exists
  if kubectl get namespace argocd &>/dev/null; then
    echo "   Deleting argocd namespace..."
    kubectl delete namespace argocd --timeout=60s || echo "   ⚠️  Namespace deletion may take time due to finalizers"
  fi
  echo "✅ Argo CD uninstalled"
else
  echo "   ℹ️  Argo CD namespace not found, skipping..."
fi
echo ""

# Uninstall KEDA
echo "📦 Uninstalling KEDA..."
if helm list -n keda 2>/dev/null | grep -q keda; then
  echo "   Uninstalling KEDA Helm release..."
  helm uninstall keda -n keda 2>/dev/null || echo "   ⚠️  KEDA Helm release may have already been deleted"
  
  # Wait a bit for resources to be deleted
  sleep 5
  
  # Delete namespace if it still exists
  if kubectl get namespace keda &>/dev/null; then
    echo "   Deleting keda namespace..."
    kubectl delete namespace keda --timeout=60s || echo "   ⚠️  Namespace deletion may take time due to finalizers"
  fi
  echo "✅ KEDA uninstalled"
else
  echo "   ℹ️  KEDA Helm release not found, skipping..."
fi
echo ""

# Uninstall MongoDB
echo "📦 Uninstalling MongoDB..."
if kubectl get namespace mongo &>/dev/null; then
  echo "   Deleting MongoDB resources..."
  kubectl delete -f "${SCRIPT_DIR}/mongodb-deployment.yaml" 2>/dev/null || echo "   ⚠️  Some MongoDB resources may have already been deleted"
  
  # Wait a bit for resources to be deleted
  sleep 5
  
  # Delete namespace if it still exists
  if kubectl get namespace mongo &>/dev/null; then
    echo "   Deleting mongo namespace..."
    kubectl delete namespace mongo --timeout=60s || echo "   ⚠️  Namespace deletion may take time due to finalizers"
  fi
  echo "✅ MongoDB uninstalled"
else
  echo "   ℹ️  MongoDB namespace not found, skipping..."
fi
echo ""

# Uninstall Kafka
echo "📦 Uninstalling Kafka..."
if kubectl get namespace kafka &>/dev/null; then
  echo "   Deleting Kafka resources..."
  kubectl delete -f "${SCRIPT_DIR}/kafka-deployment.yaml" 2>/dev/null || echo "   ⚠️  Some Kafka resources may have already been deleted"
  
  # Wait a bit for resources to be deleted
  sleep 5
  
  # Delete namespace if it still exists
  if kubectl get namespace kafka &>/dev/null; then
    echo "   Deleting kafka namespace..."
    kubectl delete namespace kafka --timeout=60s || echo "   ⚠️  Namespace deletion may take time due to finalizers"
  fi
  echo "✅ Kafka uninstalled"
else
  echo "   ℹ️  Kafka namespace not found, skipping..."
fi
echo ""

# Verify uninstallation
echo "📊 Verifying uninstallation..."
echo ""

# Check namespaces
echo "Remaining namespaces:"
if kubectl get namespace kafka mongo keda argocd 2>/dev/null | grep -v NAME; then
  echo "   ⚠️  Some namespaces still exist (may be in terminating state)"
else
  echo "   ✅ All infrastructure namespaces removed"
fi
echo ""

echo "✨ Infrastructure uninstallation complete!"
echo ""
echo "Components removed:"
echo "  - Kafka (namespace: kafka)"
echo "  - MongoDB (namespace: mongo)"
echo "  - KEDA (namespace: keda)"
echo "  - Argo CD (namespace: argocd)"
echo ""
echo "💡 Note: If namespaces are stuck in 'Terminating' state, you may need to:"
echo "   1. Remove finalizers: kubectl patch namespace <namespace> -p '{\"metadata\":{\"finalizers\":[]}}' --type=merge"
echo "   2. Or force delete: kubectl delete namespace <namespace> --grace-period=0 --force"
