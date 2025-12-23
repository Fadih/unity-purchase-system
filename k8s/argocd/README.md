# ArgoCD Application Management

This directory contains ArgoCD Application manifests for managing the frontend and backend applications using GitOps principles.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Adding Applications to ArgoCD](#adding-applications-to-argocd)
  - [Quick Start](#quick-start)
  - [Manual Setup](#manual-setup)
  - [Configuration](#configuration)
- [Application Management](#application-management)
- [Sync Operations](#sync-operations)
- [Monitoring Applications](#monitoring-applications)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## Overview

ArgoCD is a GitOps continuous delivery tool that:
- Monitors Git repositories for changes
- Automatically syncs Kubernetes manifests to the cluster
- Provides a UI and CLI for application management
- Enables declarative application deployment

**Applications Managed**:
- **Frontend**: Customer web server (`k8s/app/frontend`)
- **Backend**: Customer management API (`k8s/app/backend`)

## Prerequisites

1. **ArgoCD installed** in the cluster
   ```bash
   kubectl get pods -n argocd
   ```

2. **Repository access**: ArgoCD must have access to your Git repository
   - Public repository: No authentication needed
   - Private repository: Requires SSH key or token

3. **kubectl** configured and connected to cluster

## Adding Applications to ArgoCD

### Quick Start

The easiest way to add both frontend and backend applications:

```bash
cd k8s/argocd
./apply-applications.sh
```

This script applies both application manifests to ArgoCD.

### Manual Setup

#### Step 1: Update Repository Configuration

Before applying, update the repository URL in the application manifests:

**Edit `frontend-application.yaml` and `backend-application.yaml`**:
```yaml
spec:
  source:
    repoURL: https://github.com/YOUR-USERNAME/gitops-purchase-system.git  # Update this
    targetRevision: main  # Update branch if needed
```

#### Step 2: Apply Frontend Application

```bash
kubectl apply -f frontend-application.yaml
```

#### Step 3: Apply Backend Application

```bash
kubectl apply -f backend-application.yaml
```

#### Step 4: Verify Applications

```bash
# Check application status
kubectl get applications -n argocd

# View application details
kubectl get application frontend -n argocd
kubectl get application backend -n argocd
```

### Configuration

#### Application Manifest Structure

Each application manifest (`frontend-application.yaml` and `backend-application.yaml`) contains:

**Source Configuration**:
```yaml
source:
  repoURL: https://github.com/Fadih/gitops-purchase-system.git  # Git repository URL
  targetRevision: main  # Branch or tag to track
  path: k8s/app/frontend  # Path to Kubernetes manifests in repository
  directory:
    recurse: false  # Don't recurse into subdirectories
```

**Destination Configuration**:
```yaml
destination:
  server: https://kubernetes.default.svc  # Target Kubernetes cluster
  namespace: app  # Namespace where resources will be deployed
```

**Sync Policy**:
```yaml
syncPolicy:
  automated:
    prune: true  # Automatically delete resources removed from Git
    selfHeal: true  # Automatically sync if cluster state differs from Git
    allowEmpty: false  # Don't allow empty applications
  syncOptions:
    - CreateNamespace=true  # Create namespace if it doesn't exist
  retry:
    limit: 5  # Retry failed syncs up to 5 times
    backoff:
      duration: 5s  # Initial retry delay
      factor: 2  # Exponential backoff factor
      maxDuration: 3m  # Maximum retry duration
```

#### Customizing Applications

**Change Target Branch**:
```yaml
source:
  targetRevision: develop  # Track develop branch instead of main
```

**Change Target Namespace**:
```yaml
destination:
  namespace: production  # Deploy to production namespace
```

**Disable Auto-Sync**:
```yaml
syncPolicy:
  automated: null  # Remove automated sync
  # Or set syncPolicy to manual
```

**Add Sync Windows** (prevent syncs during specific times):
```yaml
syncPolicy:
  syncWindows:
    - kind: allow
      schedule: '10 1 * * *'  # Allow syncs at 1:10 AM
      duration: 1h
      applications:
        - '*'
```

## Application Management

### View Applications

```bash
# List all applications
kubectl get applications -n argocd

# Get detailed information
kubectl get application frontend -n argocd -o yaml

# Describe application
kubectl describe application frontend -n argocd
```

### Using ArgoCD CLI

**Install ArgoCD CLI**:
```bash
# macOS
brew install argocd

# Linux
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd
```

**Login to ArgoCD**:
```bash
# Port forward ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:80

# Login (get password from secret)
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
argocd login localhost:8080 --username admin --password $ARGOCD_PASSWORD
```

**List Applications**:
```bash
argocd app list
```

**Get Application Details**:
```bash
argocd app get frontend
argocd app get backend
```

**View Application Resources**:
```bash
argocd app resources frontend
argocd app resources backend
```

### Using ArgoCD UI

**Access UI**:
```bash
# Port forward
kubectl port-forward svc/argocd-server -n argocd 8080:80

# Open browser
open http://localhost:8080  # macOS
# Or visit http://localhost:8080 in your browser
```

**Login**:
- Username: `admin`
- Password: Get from secret:
  ```bash
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
  ```

## Sync Operations

### Automatic Sync

Applications are configured with **automatic sync**, meaning:
- Changes in Git are automatically detected
- Applications are automatically synced to match Git state
- Manual drift (cluster changes) is automatically corrected

### Manual Sync

**Using kubectl**:
```bash
# Trigger manual sync
kubectl patch application frontend -n argocd --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"main"}}}'
```

**Using ArgoCD CLI**:
```bash
# Sync application
argocd app sync frontend

# Sync with prune (delete resources not in Git)
argocd app sync frontend --prune

# Sync specific resources only
argocd app sync frontend --resource Service:app/frontend-app
```

**Using ArgoCD UI**:
1. Navigate to the application
2. Click "Sync" button
3. Select resources to sync
4. Click "Synchronize"

### Sync Options

**Sync with Prune**:
```bash
argocd app sync frontend --prune
```
Deletes resources that exist in cluster but not in Git.

**Sync with Replace**:
```bash
argocd app sync frontend --replace
```
Replaces resources instead of applying patches.

**Sync with Force**:
```bash
argocd app sync frontend --force
```
Forces sync even if resources are in use.

### Sync Status

**Check Sync Status**:
```bash
# Using kubectl
kubectl get application frontend -n argocd -o jsonpath='{.status.sync.status}'

# Using ArgoCD CLI
argocd app get frontend
```

**Sync Statuses**:
- `Synced`: Application matches Git state
- `OutOfSync`: Cluster state differs from Git
- `Unknown`: Sync status cannot be determined
- `Error`: Sync failed

## Monitoring Applications

### Application Health

**Check Health Status**:
```bash
# Using kubectl
kubectl get application frontend -n argocd -o jsonpath='{.status.health.status}'

# Using ArgoCD CLI
argocd app get frontend | grep Health
```

**Health Statuses**:
- `Healthy`: All resources are healthy
- `Degraded`: Some resources are degraded
- `Progressing`: Resources are being updated
- `Suspended`: Application is suspended
- `Unknown`: Health cannot be determined
- `Missing`: Required resources are missing

### View Application Logs

```bash
# View ArgoCD application controller logs
kubectl logs -n argocd deployment/argocd-application-controller --tail=50

# View repo server logs
kubectl logs -n argocd deployment/argocd-repo-server --tail=50
```

### Application Events

```bash
# View application events
kubectl get events -n argocd --field-selector involvedObject.name=frontend

# Watch application events
kubectl get events -n argocd --field-selector involvedObject.name=frontend --watch
```

## Troubleshooting

### Application Not Syncing

**Issue**: Application shows "OutOfSync" but won't sync automatically

**Solutions**:
```bash
# Check if auto-sync is enabled
kubectl get application frontend -n argocd -o jsonpath='{.spec.syncPolicy.automated}'

# Check application conditions
kubectl describe application frontend -n argocd | grep -A 10 Conditions

# Manually trigger sync
argocd app sync frontend

# Check repo server logs
kubectl logs -n argocd deployment/argocd-repo-server --tail=50
```

### Repository Access Issues

**Issue**: Cannot access Git repository

**Solutions**:
```bash
# Check repository connectivity
kubectl exec -n argocd deployment/argocd-repo-server -- \
  git ls-remote https://github.com/YOUR-USERNAME/gitops-purchase-system.git

# Verify repository URL in application
kubectl get application frontend -n argocd -o yaml | grep repoURL

# For private repositories, add repository credentials
argocd repo add https://github.com/YOUR-USERNAME/gitops-purchase-system.git \
  --username YOUR_USERNAME \
  --password YOUR_TOKEN
```

**For Private Repositories**:
```bash
# Add SSH key for private repository
argocd repo add git@github.com:YOUR-USERNAME/gitops-purchase-system.git \
  --ssh-private-key-path ~/.ssh/id_rsa

# Or add HTTPS with token
argocd repo add https://github.com/YOUR-USERNAME/gitops-purchase-system.git \
  --type git \
  --name gitops-purchase-system \
  --username YOUR_USERNAME \
  --password YOUR_GITHUB_TOKEN
```

### Application Stuck in Progressing

**Issue**: Application health shows "Progressing" for extended time

**Solutions**:
```bash
# Check application resources
argocd app resources frontend

# Check for failed resources
kubectl get all -n app -l app=frontend-app

# Check resource events
kubectl describe deployment frontend-app -n app

# Check pod status
kubectl get pods -n app -l app=frontend-app
```

### Sync Failures

**Issue**: Sync operation fails

**Solutions**:
```bash
# Check sync operation details
argocd app get frontend | grep -A 20 "Sync Policy"

# View operation history
argocd app history frontend

# Check for resource conflicts
kubectl get application frontend -n argocd -o yaml | grep -A 10 "operationState"

# Retry sync
argocd app sync frontend --retry-limit 5
```

### Resources Not Found

**Issue**: ArgoCD reports resources as "Missing"

**Solutions**:
```bash
# Verify resources exist in Git repository
git ls-tree -r main --name-only | grep k8s/app/frontend

# Check if path is correct in application manifest
kubectl get application frontend -n argocd -o jsonpath='{.spec.source.path}'

# Verify kustomization.yaml exists
kubectl exec -n argocd deployment/argocd-repo-server -- \
  cat /tmp/repos/YOUR_REPO/k8s/app/frontend/kustomization.yaml
```

### Namespace Issues

**Issue**: Cannot create resources in namespace

**Solutions**:
```bash
# Check if namespace exists
kubectl get namespace app

# Verify CreateNamespace option is set
kubectl get application frontend -n argocd -o jsonpath='{.spec.syncPolicy.syncOptions}'

# Manually create namespace if needed
kubectl create namespace app
```

## Advanced Configuration

### Multiple Environments

Create separate applications for different environments:

**Production Application** (`frontend-production.yaml`):
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: frontend-production
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/YOUR-USERNAME/gitops-purchase-system.git
    targetRevision: main
    path: k8s/app/frontend
  destination:
    server: https://kubernetes.default.svc
    namespace: production  # Different namespace
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Resource Hooks

Add hooks for pre/post sync operations:

```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true
    - PruneLast=true  # Prune resources last
  hooks:
    preSync:
      - name: pre-migration
        template: job
    postSync:
      - name: post-verification
        template: job
```

### Application Sets (Multiple Applications)

For managing multiple applications, consider using ApplicationSet:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: apps
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - name: frontend
            path: k8s/app/frontend
          - name: backend
            path: k8s/app/backend
  template:
    metadata:
      name: '{{name}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/YOUR-USERNAME/gitops-purchase-system.git
        targetRevision: main
        path: '{{path}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: app
```

### Sync Windows

Prevent syncs during maintenance windows:

```yaml
syncPolicy:
  syncWindows:
    - kind: deny
      schedule: '0 2 * * *'  # Deny syncs at 2 AM
      duration: 1h
      applications:
        - '*'
```

## Best Practices

1. **Use Automated Sync**: Enable automated sync for faster deployments
2. **Enable Self-Heal**: Automatically correct manual cluster changes
3. **Use Prune**: Keep cluster clean by removing deleted resources
4. **Monitor Applications**: Regularly check application health and sync status
5. **Version Control**: Always commit application manifests to Git
6. **Use Tags/Branches**: Track specific versions using Git tags
7. **Separate Environments**: Use different applications for dev/staging/prod

## Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- [Application Set](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/)
- [Sync Policies](https://argo-cd.readthedocs.io/en/stable/user-guide/sync_policies/)


