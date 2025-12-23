# Kubernetes Infrastructure Documentation

This directory contains the infrastructure components required for the gitops Purchase System, including Kafka, MongoDB, KEDA, Prometheus, and ArgoCD.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Components](#components)
  - [Kafka](#kafka)
  - [MongoDB](#mongodb)
  - [KEDA](#keda)
  - [Prometheus](#prometheus)
  - [ArgoCD](#argocd)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## Overview

The infrastructure stack consists of:

- **Kafka**: Message broker for event-driven architecture (purchase events)
- **MongoDB**: Database for storing purchase records
- **KEDA**: Kubernetes Event-Driven Autoscaler for dynamic pod scaling
- **Prometheus**: Metrics collection and monitoring
- **ArgoCD**: GitOps continuous delivery tool

## Prerequisites

Before installing the infrastructure, ensure you have:

1. **Kubernetes cluster** (v1.24+)
   ```bash
   kubectl cluster-info
   ```

2. **kubectl** configured and connected to your cluster
   ```bash
   kubectl get nodes
   ```

3. **Helm** (v3.0+) for KEDA installation
   ```bash
   helm version
   ```

4. **Sufficient cluster resources**:
   - Minimum 4 CPU cores
   - Minimum 8GB RAM
   - Storage for MongoDB and Prometheus

## Installation

### Quick Start

Install all infrastructure components:

```bash
cd k8s/infrastructure
./install-infrastructure.sh
```

This script will:
1. Install Kafka in the `kafka` namespace
2. Install MongoDB in the `mongo` namespace
3. Install KEDA in the `keda` namespace
4. Install Prometheus in the `prometheus` namespace
5. Install ArgoCD in the `argocd` namespace

### Installation Time

The complete installation typically takes 5-10 minutes, depending on:
- Cluster resources
- Network speed (for pulling images)
- Storage provisioning

### Verify Installation

Check all components are running:

```bash
# Check Kafka
kubectl get pods -n kafka

# Check MongoDB
kubectl get pods -n mongo

# Check KEDA
kubectl get pods -n keda

# Check Prometheus
kubectl get pods -n prometheus

# Check ArgoCD
kubectl get pods -n argocd
```

## Components

### Kafka

**Purpose**: Message broker for handling purchase events asynchronously.

**Namespace**: `kafka`

**Configuration**:
- Single Kafka broker (StatefulSet)
- Service: `kafka.kafka.svc.cluster.local:9092`
- Storage: Persistent volume for message retention

**Key Files**:
- `kafka-deployment.yaml`: Kafka StatefulSet and Service

**Access Kafka**:
```bash
# Port forward to access Kafka locally
kubectl port-forward svc/kafka -n kafka 9092:9092

# List topics (from within cluster)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

**Common Kafka Commands**:

```bash
# Create a topic
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-topics.sh \
  --create \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

# List all topics
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-topics.sh \
  --list \
  --bootstrap-server localhost:9092

# Describe a topic (shows partitions, replication, etc.)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-topics.sh \
  --describe \
  --topic purchase-events \
  --bootstrap-server localhost:9092

# Delete a topic
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-topics.sh \
  --delete \
  --topic purchase-events \
  --bootstrap-server localhost:9092

# Produce messages to a topic
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-producer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092

# Consume messages from a topic (from beginning)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --from-beginning

# Consume messages from a topic (latest only)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092

# Consume with consumer group
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --group my-consumer-group \
  --from-beginning

# List consumer groups
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-consumer-groups.sh \
  --list \
  --bootstrap-server localhost:9092

# Describe consumer group (show lag, offsets, etc.)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-consumer-groups.sh \
  --describe \
  --group customer-management-api \
  --bootstrap-server localhost:9092

# Reset consumer group offsets (to beginning)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-consumer-groups.sh \
  --reset-offsets \
  --to-earliest \
  --group customer-management-api \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --execute

# Get topic partition information
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-topics.sh \
  --describe \
  --topic purchase-events \
  --bootstrap-server localhost:9092 | grep Partition

# Check message count in a topic (approximate)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-run-class.sh \
  kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic purchase-events \
  --time -1

# View broker configuration
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-configs.sh \
  --bootstrap-server localhost:9092 \
  --entity-type brokers \
  --entity-name 0 \
  --describe

# View topic configuration
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-configs.sh \
  --bootstrap-server localhost:9092 \
  --entity-type topics \
  --entity-name purchase-events \
  --describe
```

**Viewing Topics and Topic Data**:

```bash
# List all topics with details
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-topics.sh \
  --list \
  --bootstrap-server localhost:9092

# Show detailed information about a topic (partitions, replicas, leaders)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-topics.sh \
  --describe \
  --topic purchase-events \
  --bootstrap-server localhost:9092

# View messages in a topic (from beginning, formatted)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --from-beginning \
  --property print.key=true \
  --property print.value=true \
  --property print.timestamp=true

# View messages in a topic (latest messages only)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --property print.key=true \
  --property print.value=true

# View messages from a specific partition
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --partition 0 \
  --from-beginning

# View last N messages from a topic (using offset)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --offset latest \
  --max-messages 10

# View messages with timestamps (human-readable)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --from-beginning \
  --property print.timestamp=true \
  --property print.key=true \
  --property print.value=true \
  --property print.partition=true

# View messages as JSON (pretty print if messages are JSON)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --from-beginning \
  --property print.value=true | jq .

# Count messages in a topic (approximate - shows offsets per partition)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-run-class.sh \
  kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic purchase-events \
  --time -1

# Get earliest and latest offsets for a topic
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-run-class.sh \
  kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic purchase-events \
  --time -2

# View messages from a specific offset
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --partition 0 \
  --offset 100 \
  --max-messages 5

# View messages with key-value separator
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --from-beginning \
  --property print.key=true \
  --property print.value=true \
  --property key.separator=" -> " \
  --property print.timestamp=true

# View messages and save to file
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --from-beginning \
  --max-messages 100 > /tmp/kafka-messages.txt

# View topic data with consumer group (won't affect other consumers)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --group kafka-viewer \
  --from-beginning \
  --property print.timestamp=true \
  --property print.key=true \
  --property print.value=true
```

**Quick Topic Data Viewing**:

```bash
# Quick view: Show last 10 messages from purchase-events topic
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --offset latest \
  --max-messages 10 \
  --property print.timestamp=true \
  --property print.value=true

# Quick view: Show all messages from beginning (one-time)
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events \
  --bootstrap-server localhost:9092 \
  --from-beginning \
  --max-messages 50 \
  --property print.timestamp=true \
  --property print.value=true | head -20
```

**Using Kafka from External Pod** (if Kafka service is accessible):

```bash
# Create a temporary pod to run Kafka commands
kubectl run kafka-client --rm -it --restart=Never \
  --image=apache/kafka:4.0.0 \
  --namespace=kafka \
  -- /bin/bash

# Then inside the pod:
kafka-topics.sh --list --bootstrap-server kafka:9092
kafka-console-producer.sh --topic purchase-events --bootstrap-server kafka:9092
kafka-console-consumer.sh --topic purchase-events --bootstrap-server kafka:9092 --from-beginning
```

**Troubleshooting**:

**Issue**: Kafka pod not starting
```bash
# Check pod status
kubectl describe pod kafka-0 -n kafka

# Check logs
kubectl logs kafka-0 -n kafka

# Common causes:
# - Insufficient resources (CPU/Memory)
# - Storage not provisioned
# - Port conflicts
```

**Issue**: Cannot connect to Kafka
```bash
# Verify service exists
kubectl get svc -n kafka

# Test connectivity from another pod
kubectl run kafka-test --rm -it --image=apache/kafka:4.0.0 --restart=Never -n kafka -- \
  /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server kafka:9092
```

**Issue**: Messages not persisting
```bash
# Check persistent volume
kubectl get pvc -n kafka

# Check storage class
kubectl get storageclass
```

### MongoDB

**Purpose**: Database for storing purchase records and customer data.

**Namespace**: `mongo`

**Configuration**:
- Single MongoDB instance (StatefulSet)
- Service: `mongo.mongo.svc.cluster.local:27017`
- Storage: Persistent volume for data persistence

**Key Files**:
- `mongodb-deployment.yaml`: MongoDB StatefulSet and Service

**Access MongoDB**:
```bash
# Port forward to access MongoDB locally
kubectl port-forward svc/mongo -n mongo 27017:27017

# Connect using MongoDB client with authentication
mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin"

# Or from within cluster (with authentication)
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin"
```

**Common MongoDB Commands**:

**Note**: MongoDB requires authentication. Default credentials: `root` / `changeme`

```bash
# Connect to MongoDB shell with authentication
kubectl -n mongo exec -it mongo-0 -- mongosh -u root -p changeme --authenticationDatabase admin

# Or connect directly to purchases database
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin"
```

**Database Operations**:

```bash
# List all databases
kubectl -n mongo exec -it mongo-0 -- mongosh -u root -p changeme --authenticationDatabase admin --eval "show dbs"

# Switch to purchases database
kubectl -n mongo exec -it mongo-0 -- mongosh -u root -p changeme --authenticationDatabase admin --eval "use purchases"

# Show collections in current database
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "show collections"
```

**Viewing Purchase Data**:

```bash
# Count total purchases
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.countDocuments()"

# View all purchases (first 10)
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.find().limit(10).pretty()"

# View all purchases for a specific user
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.find({userId: 'user123'}).pretty()"

# View purchases sorted by creation date (newest first)
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.find().sort({createdAt: -1}).limit(10).pretty()"

# View purchases with specific fields only
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.find({}, {userId: 1, username: 1, price: 1, createdAt: 1}).limit(10).pretty()"

# Count purchases by user
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.aggregate([{$group: {_id: '$userId', count: {$sum: 1}}}, {$sort: {count: -1}}]).pretty()"

# Find purchases above a certain price
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.find({price: {$gt: 100}}).pretty()"

# View purchase statistics
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.aggregate([{$group: {_id: null, total: {$sum: '$price'}, count: {$sum: 1}, avg: {$avg: '$price'}, min: {$min: '$price'}, max: {$max: '$price'}}}]).pretty()"
```

**Deleting Data**:

```bash
# Delete all purchases (⚠️ WARNING: This deletes all data)
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.deleteMany({})"

# Delete purchases for a specific user
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.deleteMany({userId: 'user123'})"

# Delete purchases older than a specific date
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.deleteMany({createdAt: {$lt: '2024-01-01T00:00:00Z'}})"

# Delete a single purchase by ID
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.deleteOne({_id: ObjectId('YOUR_ID_HERE')})"
```

**Useful MongoDB Operations**:

```bash
# Create an index on userId for faster queries
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.createIndex({userId: 1})"

# List all indexes
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.getIndexes()"

# Drop the purchases collection (⚠️ WARNING: Deletes collection and all data)
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.drop()"

# Drop the entire purchases database (⚠️ WARNING: Deletes database and all data)
kubectl -n mongo exec -it mongo-0 -- mongosh -u root -p changeme --authenticationDatabase admin --eval "use purchases; db.dropDatabase()"

# Export purchases to backup file (requires authentication)
kubectl -n mongo exec -it mongo-0 -- mongodump --uri="mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --out=/tmp/backup

# Import data from backup file (requires authentication)
kubectl -n mongo exec -it mongo-0 -- mongorestore --uri="mongodb://root:changeme@localhost:27017/purchases?authSource=admin" /tmp/backup/purchases/purchases.bson

# Get database stats
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.stats()"

# Get collection stats
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin" --eval "db.purchases.stats()"

# Check MongoDB server status
kubectl -n mongo exec -it mongo-0 -- mongosh -u root -p changeme --authenticationDatabase admin --eval "db.serverStatus()"

# View current operations
kubectl -n mongo exec -it mongo-0 -- mongosh -u root -p changeme --authenticationDatabase admin --eval "db.currentOp()"
```

**Interactive MongoDB Shell**:

```bash
# Open interactive MongoDB shell with authentication
kubectl -n mongo exec -it mongo-0 -- mongosh "mongodb://root:changeme@localhost:27017/purchases?authSource=admin"

# Or connect and then switch to purchases database
kubectl -n mongo exec -it mongo-0 -- mongosh -u root -p changeme --authenticationDatabase admin
# Then in the shell:
# > use purchases
# > db.purchases.find().limit(5)
# > db.purchases.countDocuments()
# > db.purchases.findOne({userId: "user123"})
# > exit
```

**Troubleshooting**:

**Issue**: MongoDB pod not starting
```bash
# Check pod status
kubectl describe pod mongo-0 -n mongo

# Check logs
kubectl logs mongo-0 -n mongo

# Common causes:
# - Insufficient memory (MongoDB needs at least 512MB)
# - Storage not provisioned
# - Init container failures
```

**Issue**: Cannot connect to MongoDB
```bash
# Verify service
kubectl get svc -n mongo

# Test connection
kubectl run mongo-test --rm -it --image=mongo:7.0 --restart=Never -n mongo -- \
  mongosh mongodb://mongo:27017
```

**Issue**: Data not persisting after pod restart
```bash
# Check persistent volume claim
kubectl get pvc -n mongo

# Verify data directory
kubectl exec -it mongo-0 -n mongo -- ls -la /data/db
```

### KEDA

**Purpose**: Kubernetes Event-Driven Autoscaler for scaling pods based on metrics (CPU, Prometheus, Kafka lag, etc.).

**Namespace**: `keda`

**Installation**: Installed via Helm chart

**Configuration**:
- `helm/keda/values.yaml`: KEDA Helm values

**Verify KEDA**:
```bash
# Check KEDA operator
kubectl get pods -n keda

# Check KEDA metrics server
kubectl get deployment keda-operator -n keda
kubectl get deployment keda-metrics-apiserver -n keda
```

**Troubleshooting**:

**Issue**: KEDA not scaling applications
```bash
# Check ScaledObject status
kubectl get scaledobject -n app

# Describe ScaledObject for details
kubectl describe scaledobject frontend-app-scaledobject -n app

# Check KEDA operator logs
kubectl logs -n keda deployment/keda-operator --tail=50

# Verify HPA was created
kubectl get hpa -n app
```

**Issue**: Metrics not available
```bash
# Check if metrics server is running
kubectl get pods -n keda -l app=keda-metrics-apiserver

# Check metrics API
kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1" | jq

# Verify scaler configuration
kubectl get scaledobject -n app -o yaml
```

**Issue**: CPU scaler not working
```bash
# Ensure CPU requests are set in deployment
kubectl get deployment frontend-app -n app -o yaml | grep -A 5 resources

# Check if metrics-server is installed (required for CPU metrics)
kubectl get deployment metrics-server -n kube-system

# Verify CPU metrics
kubectl top pods -n app
```

### Prometheus

**Purpose**: Metrics collection and monitoring system for applications and infrastructure.

**Namespace**: `prometheus`

**Configuration**:
- `prometheus/prometheus-deployment.yaml`: Prometheus deployment
- `prometheus/prometheus-service.yaml`: Service exposing Prometheus on port 9090
- `prometheus/prometheus-configmap.yaml`: Scrape configuration
- `prometheus/prometheus-rbac.yaml`: RBAC permissions

**Access Prometheus**:
```bash
# Port forward to access Prometheus UI
kubectl port-forward svc/prometheus-service -n prometheus 9090:9090

# Then visit: http://localhost:9090
```

**Scrape Targets**:
Prometheus is configured to scrape:
- Frontend application (`frontend-app`) at `/metrics`
- Backend application (`backend-app`) at `/metrics`
- Kubernetes API server
- Kubernetes nodes

**Troubleshooting**:

**Issue**: Prometheus not scraping targets
```bash
# Check Prometheus targets
kubectl exec -n prometheus deployment/prometheus -- \
  wget -qO- http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Check Prometheus logs
kubectl logs -n prometheus deployment/prometheus --tail=50

# Verify scrape configuration
kubectl get configmap prometheus-config -n prometheus -o yaml
```

**Issue**: Applications not exposing metrics
```bash
# Test if metrics endpoint is accessible
kubectl port-forward svc/frontend-app -n app 8001:8001
curl http://localhost:8001/metrics

# Verify prometheus-fastapi-instrumentator is installed
kubectl exec -n app deployment/frontend-app -- pip list | grep prometheus

# Check application logs for metrics initialization
kubectl logs -n app deployment/frontend-app | grep -i metric
```

**Issue**: Prometheus running out of memory
```bash
# Check Prometheus memory usage
kubectl top pod -n prometheus

# Check retention settings
kubectl get configmap prometheus-config -n prometheus -o yaml | grep retention

# Adjust retention in prometheus-deployment.yaml:
# --storage.tsdb.retention.time=15d  # Reduce if needed
```

**Issue**: Cannot access Prometheus service from other namespaces
```bash
# Verify service exists
kubectl get svc prometheus-service -n prometheus

# Test connectivity from app namespace
kubectl run prometheus-test --rm -it --image=curlimages/curl --restart=Never -n app -- \
  curl http://prometheus-service.prometheus.svc.cluster.local:9090/api/v1/status/config
```

### ArgoCD

**Purpose**: GitOps continuous delivery tool for managing Kubernetes applications.

**Namespace**: `argocd`

**Installation**: Installed from official ArgoCD manifests, then patched to use NodePort

**Configuration**:
- Service type: `NodePort` (configured via `argocd-service-patch.yaml`)
- NodePort: `32221` (for both HTTP and HTTPS)
- Service: `argocd-server.argocd.svc.cluster.local`

**Key Files**:
- `argocd-service-patch.yaml`: Service patch to configure NodePort access

**Access ArgoCD**:

**Via NodePort** (recommended):
```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Get admin password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

echo "ArgoCD UI: https://${NODE_IP}:32221"
echo "Username: admin"
echo "Password: ${ARGOCD_PASSWORD}"
# Note: Accept the self-signed certificate when accessing

# Login via CLI
argocd login ${NODE_IP}:8080 --username admin --password ${ARGOCD_PASSWORD} --insecure
```

**Via Port Forward** (alternative):
```bash
# Port forward to access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:80

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Login via CLI
argocd login localhost:8080 --username admin --password <password>
```

**Troubleshooting**:

**Issue**: ArgoCD server not accessible
```bash
# Check ArgoCD server pod
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-server

# Check server logs
kubectl logs -n argocd deployment/argocd-server --tail=50

# Verify service
kubectl get svc argocd-server -n argocd
```

**Issue**: Applications not syncing
```bash
# Check application status
kubectl get applications -n argocd

# Describe application for details
kubectl describe application frontend -n argocd

# Check repo server logs
kubectl logs -n argocd deployment/argocd-repo-server --tail=50

# Verify repository access
kubectl get applications frontend -n argocd -o yaml | grep repoURL
```

**Issue**: Cannot connect to Git repository
```bash
# Check repository connectivity
kubectl exec -n argocd deployment/argocd-repo-server -- \
  git ls-remote https://github.com/your-org/your-repo.git

# Verify repository URL in Application manifest
kubectl get application frontend -n argocd -o yaml | grep -A 5 repoURL

# Check for authentication issues
kubectl get secrets -n argocd | grep repo
```

## Configuration

### Kafka Configuration

Edit `kafka-deployment.yaml` to modify:
- Replica count
- Resource limits
- Storage size
- Kafka configuration options

### MongoDB Configuration

Edit `mongodb-deployment.yaml` to modify:
- Resource limits
- Storage size
- MongoDB configuration

### KEDA Configuration

Edit `helm/keda/values.yaml` to customize:
- Resource limits
- Replica count
- Metrics server configuration

### Prometheus Configuration

Edit `prometheus/prometheus-configmap.yaml` to:
- Add new scrape targets
- Modify scrape intervals
- Configure alerting rules

## Troubleshooting

### General Issues

**Issue**: Components not starting after installation
```bash
# Check all pods across all namespaces
kubectl get pods --all-namespaces | grep -E "kafka|mongo|keda|prometheus|argocd"

# Check for resource constraints
kubectl describe nodes | grep -A 5 "Allocated resources"

# Check events
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -20
```

**Issue**: Namespace creation fails
```bash
# Check if namespaces exist
kubectl get namespaces | grep -E "kafka|mongo|keda|prometheus|argocd"

# Create manually if needed
kubectl create namespace kafka
kubectl create namespace mongo
kubectl create namespace keda
kubectl create namespace prometheus
kubectl create namespace argocd
```

**Issue**: Image pull errors
```bash
# Check if images are accessible
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 Events

# Common solutions:
# - Check internet connectivity
# - Verify image names and tags
# - Check for private registry authentication
```

### Storage Issues

**Issue**: Persistent volumes not provisioning
```bash
# Check storage classes
kubectl get storageclass

# Check PVC status
kubectl get pvc --all-namespaces

# Check for default storage class
kubectl get storageclass | grep default
```

**Issue**: Out of disk space
```bash
# Check node disk usage
kubectl top nodes

# Check PVC usage
kubectl get pvc --all-namespaces -o wide

# Clean up unused resources
kubectl delete pvc --all-namespaces --field-selector status.phase!=Bound
```

### Network Issues

**Issue**: Services not accessible
```bash
# Verify service endpoints
kubectl get endpoints --all-namespaces

# Test service connectivity
kubectl run test-pod --rm -it --image=curlimages/curl --restart=Never -- \
  curl <service-name>.<namespace>.svc.cluster.local:<port>

# Check DNS resolution
kubectl run test-pod --rm -it --image=busybox --restart=Never -- \
  nslookup <service-name>.<namespace>.svc.cluster.local
```

## Uninstallation

To remove all infrastructure components:

```bash
cd k8s/infrastructure
./uninstall-infrastructure.sh
```

Or manually remove components:

```bash
# Remove ArgoCD
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Remove Prometheus
kubectl delete -f prometheus/

# Remove KEDA
helm uninstall keda -n keda

# Remove MongoDB
kubectl delete -f mongodb-deployment.yaml

# Remove Kafka
kubectl delete -f kafka-deployment.yaml

# Remove namespaces (this will delete all resources)
kubectl delete namespace argocd prometheus keda mongo kafka
```


