# Application Deployment Manifests

Kubernetes manifests for deploying the frontend and backend applications.

## Overview

This directory contains Kubernetes manifests for:
- **Frontend**: Customer web server (`frontend/`)
- **Backend**: Customer management API (`backend/`)

Both applications are deployed to the `app` namespace using Kustomize.

## Quick Start

### Deploy Both Applications

```bash
# Deploy frontend
kubectl apply -k frontend/

# Deploy backend
kubectl apply -k backend/
```

### Deploy via ArgoCD

Applications are automatically managed by ArgoCD. See `../argocd/README.md` for details.

## Directory Structure

### Frontend (`frontend/`)

- `namespace.yaml` - Creates `app` namespace
- `configmap.yaml` - Application configuration
- `secret.yaml` - Sensitive configuration (Kafka, etc.)
- `deployment.yaml` - Frontend application deployment
- `service.yaml` - Service exposing frontend (NodePort 32222)
- `scaledobject.yaml` - KEDA autoscaling configuration
- `kustomization.yaml` - Kustomize configuration

### Backend (`backend/`)

- `configmap.yaml` - Application configuration
- `secret.yaml` - Sensitive configuration (MongoDB, Kafka)
- `deployment.yaml` - Backend API deployment
- `service.yaml` - Service exposing backend
- `scaledobject.yaml` - KEDA autoscaling configuration (Kafka-based)
- `kustomization.yaml` - Kustomize configuration

## Configuration

### Update Image Tags

Edit `kustomization.yaml` in each directory:

```yaml
images:
  - name: frontend-app
    newName: fadihussien/unity
    newTag: frontend-1.0.11  # Update this
```

### Environment Variables

**Frontend ConfigMap** (`frontend/configmap.yaml`):
- `KAFKA_TOPIC`: Kafka topic name
- `CUSTOMER_API_URL`: Backend API URL
- `PORT`: Application port
- `LOG_LEVEL`: Logging level

**Backend ConfigMap** (`backend/configmap.yaml`):
- `KAFKA_TOPIC`: Kafka topic name
- `KAFKA_GROUP_ID`: Kafka consumer group
- `PORT`: Application port
- `LOG_LEVEL`: Logging level

**Secrets** (create before deploying):
```bash
# Frontend secrets
kubectl create secret generic frontend-app-secrets -n app \
  --from-literal=KAFKA_BOOTSTRAP_SERVERS=kafka.kafka.svc.cluster.local:9092

# Backend secrets
kubectl create secret generic backend-app-secrets -n app \
  --from-literal=MONGODB_URI=mongodb://mongo.mongo.svc.cluster.local:27017/purchases \
  --from-literal=KAFKA_BOOTSTRAP_SERVERS=kafka.kafka.svc.cluster.local:9092
```

## Common Operations

### Check Application Status

```bash
# Frontend
kubectl get pods -n app -l app=frontend-app
kubectl get svc -n app frontend-app

# Backend
kubectl get pods -n app -l app=backend-app
kubectl get svc -n app backend-app
```

### View Logs

```bash
# Frontend logs
kubectl logs -n app -l app=frontend-app --tail=50 -f

# Backend logs
kubectl logs -n app -l app=backend-app --tail=50 -f
```

### Port Forward

```bash
# Frontend (port 8001)
kubectl port-forward svc/frontend-app -n app 8001:8001

# Backend (port 8000)
kubectl port-forward svc/backend-app -n app 8000:8000
```

### Check Autoscaling

```bash
# View ScaledObjects
kubectl get scaledobject -n app

# View HPA (created by KEDA)
kubectl get hpa -n app

# Describe scaling details
kubectl describe scaledobject frontend-app-scaledobject -n app
```

### Update Application

```bash
# After updating kustomization.yaml, apply changes
kubectl apply -k frontend/
kubectl apply -k backend/

# Or let ArgoCD sync automatically
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n app

# Check events
kubectl get events -n app --sort-by='.lastTimestamp'

# Common issues:
# - Image pull errors: Check image name/tag
# - ConfigMap/Secret missing: Create required secrets
# - Resource limits: Check node resources
```

### Application Not Accessible

```bash
# Verify service exists
kubectl get svc -n app

# Check endpoints
kubectl get endpoints -n app

# Test connectivity
kubectl run test-pod --rm -it --image=curlimages/curl --restart=Never -n app -- \
  curl http://frontend-app:8001/health
```

### Scaling Issues

```bash
# Check ScaledObject status
kubectl describe scaledobject frontend-app-scaledobject -n app

# Check HPA metrics
kubectl describe hpa keda-hpa-frontend-app-scaledobject -n app

# Verify metrics are available
kubectl top pods -n app
```

### Configuration Issues

```bash
# View current ConfigMap
kubectl get configmap frontend-app-config -n app -o yaml

# View current Secret (values are base64 encoded)
kubectl get secret frontend-app-secrets -n app -o yaml

# Update ConfigMap
kubectl edit configmap frontend-app-config -n app
```

## Autoscaling

### Frontend Scaling

- **CPU-based**: Scales when CPU > 70%
- **Prometheus-based**: Scales based on HTTP request rate (excluding health/metrics)
- **Min replicas**: 2
- **Max replicas**: 10

### Backend Scaling

- **Kafka-based**: Scales based on consumer lag
- **Min replicas**: 2
- **Max replicas**: 10
- **Lag threshold**: 10 messages per pod

## Resources

- **Frontend**: 100m CPU, 256Mi memory (requests)
- **Backend**: 100m CPU, 256Mi memory (requests)

Adjust in `deployment.yaml` if needed.

## Cleanup

```bash
# Delete frontend
kubectl delete -k frontend/

# Delete backend
kubectl delete -k backend/

# Delete namespace (removes all resources)
kubectl delete namespace app
```

