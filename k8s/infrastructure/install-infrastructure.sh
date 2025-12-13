#!/bin/bash

# Infrastructure Installation Script
# Installs Kafka, MongoDB, KEDA, Prometheus, and Argo CD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEDA_HELM_DIR="${SCRIPT_DIR}/helm/keda"
PROMETHEUS_DIR="${SCRIPT_DIR}/prometheus"
ARGOCD_MANIFEST_URL="https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"

echo "🚀 Starting infrastructure installation..."
echo ""

# Install Kafka
echo "📦 Installing Kafka..."
kubectl apply -f "${SCRIPT_DIR}/kafka-deployment.yaml"
echo "✅ Kafka deployment applied"
echo ""

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
kubectl wait --for=condition=ready pod \
  --selector=app=kafka \
  --timeout=300s \
  --namespace=kafka || echo "⚠️  Kafka may still be starting..."
echo ""

# Install MongoDB
echo "📦 Installing MongoDB..."
kubectl apply -f "${SCRIPT_DIR}/mongodb-deployment.yaml"
echo "✅ MongoDB deployment applied"
echo ""

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to be ready..."
kubectl wait --for=condition=ready pod \
  --selector=app=mongo \
  --timeout=300s \
  --namespace=mongo || echo "⚠️  MongoDB may still be starting..."
echo ""

# Install KEDA using Helm
echo "📦 Installing KEDA via Helm..."

# Add KEDA Helm repository if not already added
if ! helm repo list | grep -q kedacore; then
  echo "➕ Adding KEDA Helm repository..."
  helm repo add kedacore https://kedacore.github.io/charts
  helm repo update
fi

# Install KEDA with default values
helm upgrade --install keda kedacore/keda \
  --namespace keda \
  --create-namespace \
  --values "${KEDA_HELM_DIR}/values.yaml" \
  --wait \
  --timeout 5m

echo "✅ KEDA installed via Helm"
echo ""

# Install Prometheus
echo "📦 Installing Prometheus..."

# Create namespace first if it doesn't exist
kubectl create namespace prometheus --dry-run=client -o yaml | kubectl apply -f -

# Install all Prometheus resources
echo "   Applying Prometheus manifests..."
kubectl apply -f "${PROMETHEUS_DIR}/"
echo "✅ Prometheus resources applied"
echo ""

# Wait for Prometheus to be ready
echo "⏳ Waiting for Prometheus to be ready..."
kubectl wait --for=condition=ready pod \
  --selector=app=prometheus \
  --timeout=300s \
  --namespace=prometheus || echo "⚠️  Prometheus may still be starting..."
echo ""

# Install Argo CD using official manifests
echo "📦 Installing Argo CD via official manifests..."

# Create namespace first if it doesn't exist
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Install Argo CD from official stable manifests
echo "   Applying Argo CD manifests from GitHub..."
kubectl apply -n argocd -f "${ARGOCD_MANIFEST_URL}"

echo "✅ Argo CD manifests applied"
echo ""

# Wait for Argo CD pods to be ready
echo "⏳ Waiting for Argo CD pods to be ready..."
kubectl wait --for=condition=ready pod \
  --selector=app.kubernetes.io/name=argocd-repo-server \
  --timeout=300s \
  --namespace=argocd || echo "⚠️  Argo CD pods may still be starting..."
echo ""

# Patch Argo CD server service to use NodePort
echo "🔧 Configuring Argo CD server service as NodePort on port 8080..."
ARGOCD_SERVICE_PATCH="${SCRIPT_DIR}/argocd-service-patch.yaml"
if [ -f "${ARGOCD_SERVICE_PATCH}" ]; then
  kubectl apply -f "${ARGOCD_SERVICE_PATCH}"
  echo "✅ Argo CD service configured as NodePort"
else
  echo "⚠️  Argo CD service patch file not found, skipping NodePort configuration"
fi
echo ""

# Get Argo CD admin password
echo "🔐 Argo CD Admin Credentials:"
echo "   Username: admin"
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d 2>/dev/null || echo "Password not available yet")
if [ -n "$ARGOCD_PASSWORD" ] && [ "$ARGOCD_PASSWORD" != "Password not available yet" ]; then
  echo "   Password: $ARGOCD_PASSWORD"
  echo ""
  echo "   💡 To access Argo CD UI:"
  echo "      Port-forward: kubectl port-forward svc/argocd-server -n argocd 8080:80"
  echo "      Then visit: https://localhost:8080"
  echo "      (Accept the self-signed certificate)"
else
  echo "   Password: (checking...)"
  echo ""
  echo "   💡 To get the password later:"
  echo "      kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"
fi
echo ""

# Verify installations
echo "📊 Verifying installations..."
echo ""
echo "Kafka pods:"
kubectl get pods -n kafka
echo ""
echo "MongoDB pods:"
kubectl get pods -n mongo
echo ""
echo "KEDA pods:"
kubectl get pods -n keda
echo ""
echo "Prometheus pods:"
kubectl get pods -n prometheus
echo ""
echo "Argo CD pods:"
kubectl get pods -n argocd
echo ""

echo "✨ Infrastructure installation complete!"
echo ""
echo "Components installed:"
echo "  - Kafka (namespace: kafka)"
echo "  - MongoDB (namespace: mongo)"
echo "  - KEDA (namespace: keda)"
echo "  - Prometheus (namespace: prometheus)"
echo "  - Argo CD (namespace: argocd)"
echo ""
echo "📚 Next steps:"
echo "  2. Visit http://localhost:32221/ (accept the self-signed certificate)"
echo "  3. Login with username 'admin' and the password shown above"

