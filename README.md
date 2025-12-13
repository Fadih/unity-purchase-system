# Unity Purchase System

A microservices-based purchase management system built with FastAPI, Kafka, MongoDB, and Kubernetes. The system handles purchase events, stores them in MongoDB, and provides web interfaces and APIs for managing customer purchases.

## 🏗️ Architecture

The system consists of two main applications:

1. **Customer Web Server** (`customer-web-server/`) - Frontend web application that allows users to make purchases
2. **Customer Management API** (`customer-management-api/`) - Backend API that consumes purchase events from Kafka and stores them in MongoDB

### Technology Stack

- **Frontend**: FastAPI with Jinja2 templates
- **Backend**: FastAPI with Kafka consumer and MongoDB
- **Message Queue**: Apache Kafka
- **Database**: MongoDB
- **Container Orchestration**: Kubernetes
- **GitOps**: ArgoCD
- **Autoscaling**: KEDA
- **Monitoring**: Prometheus
- **CI/CD**: GitHub Actions

### System Flow

```
User → Frontend (customer-web-server) → Kafka → Backend (customer-management-api) → MongoDB
                                      ↓
                              Prometheus Metrics
```

1. Users interact with the web server to make purchases
2. Purchase events are published to Kafka
3. The backend API consumes events from Kafka
4. Purchase data is stored in MongoDB
5. Both services expose Prometheus metrics for monitoring and autoscaling

## 📁 Project Structure

```
unity-purchase-system/
├── customer-web-server/          # Frontend web application
│   ├── app/                      # Application code
│   ├── tests/                    # Unit tests
│   ├── templates/                # HTML templates
│   ├── Dockerfile               # Container image definition
│   ├── Makefile                 # Build and test commands
│   └── README.md                # Frontend documentation
│
├── customer-management-api/      # Backend API service
│   ├── app/                      # Application code
│   ├── tests/                    # Unit tests
│   ├── Dockerfile               # Container image definition
│   ├── Makefile                 # Build and test commands
│   └── README.md                # Backend documentation
│
├── k8s/                          # Kubernetes manifests
│   ├── app/                      # Application deployments
│   │   ├── frontend/            # Frontend Kubernetes configs
│   │   ├── backend/             # Backend Kubernetes configs
│   │   └── README.md            # Application deployment guide
│   │
│   ├── argocd/                   # ArgoCD GitOps configs
│   │   ├── frontend-application.yaml
│   │   ├── backend-application.yaml
│   │   ├── apply-applications.sh
│   │   └── README.md            # ArgoCD deployment guide
│   │
│   └── infrastructure/           # Infrastructure components
│       ├── install-infrastructure.sh
│       ├── uninstall-infrastructure.sh
│       ├── kafka-deployment.yaml
│       ├── mongodb-deployment.yaml
│       ├── prometheus/           # Prometheus manifests
│       ├── helm/                 # Helm charts
│       └── README.md             # Infrastructure guide
│
└── .github/
    └── workflows/                # GitHub Actions workflows
        ├── release.yaml          # Release automation
        └── docs.yaml             # Documentation generation
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (local or cloud)
- `kubectl` configured to access your cluster
- Docker (for building images)
- Python 3.9+ (for local development)

### 1. Install Infrastructure

Deploy core infrastructure components (Kafka, MongoDB, KEDA, Prometheus, ArgoCD):

```bash
cd k8s/infrastructure
./install-infrastructure.sh
```

This script installs:
- **Kafka** - Message queue for purchase events
- **MongoDB** - Database for storing purchases
- **KEDA** - Kubernetes autoscaler
- **Prometheus** - Metrics collection and monitoring
- **ArgoCD** - GitOps continuous deployment

**Verification**:
```bash
# Check infrastructure pods
kubectl get pods -n kafka
kubectl get pods -n mongo
kubectl get pods -n keda
kubectl get pods -n prometheus
kubectl get pods -n argocd
```

📖 **Detailed Guide**: See [k8s/infrastructure/README.md](k8s/infrastructure/README.md)

### 2. Deploy Applications to ArgoCD

Apply ArgoCD Application manifests to enable GitOps deployment:

```bash
cd k8s/argocd
./apply-applications.sh
```

This creates ArgoCD Applications that:
- Monitor the Git repository for changes
- Automatically sync Kubernetes manifests
- Deploy frontend and backend applications

**Verification**:
```bash
# Check ArgoCD applications
kubectl get applications -n argocd

# Access ArgoCD UI (get admin password)
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080 (username: admin)
```

📖 **Detailed Guide**: See [k8s/argocd/README.md](k8s/argocd/README.md)

### 3. Access Applications

**Frontend Web Server**:
```bash
kubectl port-forward svc/frontend-app -n app 8080:80
# Open http://localhost:8080
```

**Backend API**:
```bash
kubectl port-forward svc/backend-app -n app 8000:8000
# API available at http://localhost:8000
```

**Prometheus**:
```bash
kubectl port-forward svc/prometheus-service -n prometheus 9090:9090
# Open http://localhost:9090
```

## 📚 Documentation

### Application Documentation

- **[Customer Web Server](customer-web-server/README.md)** - Frontend application guide, endpoints, and metrics
- **[Customer Management API](customer-management-api/README.md)** - Backend API guide, Kafka integration, and MongoDB

### Infrastructure Documentation

- **[Infrastructure Setup](k8s/infrastructure/README.md)** - Kafka, MongoDB, KEDA, Prometheus installation and management
- **[ArgoCD Deployment](k8s/argocd/README.md)** - GitOps setup, application management, and sync operations
- **[Application Manifests](k8s/app/README.md)** - Kubernetes deployment configurations, autoscaling, and troubleshooting

## 🔧 Development

### Local Development

**Frontend**:
```bash
cd customer-web-server
make install-deps
make run
# Application runs on http://localhost:8080
```

**Backend**:
```bash
cd customer-management-api
make install-deps
make run
# API runs on http://localhost:8000
```

### Running Tests

**Frontend**:
```bash
cd customer-web-server
make test
```

**Backend**:
```bash
cd customer-management-api
make test
```

### Building Docker Images

**Frontend**:
```bash
cd customer-web-server
make build IMAGE_TAG=frontend-v1.0.0
```

**Backend**:
```bash
cd customer-management-api
make build IMAGE_TAG=backend-v1.0.0
```

## 🚢 Release Process

The project uses GitHub Actions for automated releases:

1. **Create a GitHub Release** - Tag a new version (e.g., `v1.0.0`)
2. **Automated Build** - GitHub Actions builds and pushes Docker images
3. **Update Manifests** - Kustomization files are updated with new image tags
4. **ArgoCD Sync** - ArgoCD automatically deploys the new versions

**Workflow**: `.github/workflows/release.yaml`

**Documentation Generation**: `.github/workflows/docs.yaml` (generates docs on release)

## 📊 Monitoring & Autoscaling

### Metrics

Both applications expose Prometheus metrics at `/metrics`:
- HTTP request counts and durations
- Service health status
- Custom business metrics

### Autoscaling

**Frontend**: Scales based on HTTP request rate (Prometheus metrics)
- Min replicas: 2
- Max replicas: 10
- Threshold: 20 requests/second per pod

**Backend**: Scales based on Kafka consumer lag
- Min replicas: 2
- Max replicas: 10
- Lag threshold: 10 messages per pod

**Configuration**: See `k8s/app/frontend/scaledobject.yaml` and `k8s/app/backend/scaledobject.yaml`

## 🔐 Configuration

### Environment Variables

**Frontend** (`customer-web-server`):
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker address
- `KAFKA_TOPIC` - Kafka topic name (default: `purchase-events`)
- `BACKEND_API_URL` - Backend API URL

**Backend** (`customer-management-api`):
- `MONGODB_URI` - MongoDB connection string
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker address
- `KAFKA_TOPIC` - Kafka topic name (default: `purchase-events`)
- `KAFKA_GROUP_ID` - Kafka consumer group ID

See individual application READMEs for complete configuration details.

## 🛠️ Troubleshooting

### Common Issues

**Infrastructure not ready**:
```bash
# Check all infrastructure components
kubectl get pods --all-namespaces | grep -E "kafka|mongo|keda|prometheus|argocd"
```

**Applications not deploying**:
```bash
# Check ArgoCD sync status
kubectl get applications -n argocd
kubectl describe application frontend -n argocd
kubectl describe application backend -n argocd
```

**Metrics not available**:
```bash
# Check Prometheus targets
kubectl port-forward svc/prometheus-service -n prometheus 9090:9090
# Open http://localhost:9090/targets
```

**Kafka connectivity**:
```bash
# Check Kafka pods
kubectl get pods -n kafka
# Test Kafka connection
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

See individual component READMEs for detailed troubleshooting guides.

## 📝 Contributing

1. Create a feature branch
2. Make your changes
3. Add/update tests
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🔗 Links

- [Frontend Application Documentation](customer-web-server/README.md)
- [Backend API Documentation](customer-management-api/README.md)
- [Infrastructure Setup Guide](k8s/infrastructure/README.md)
- [ArgoCD Deployment Guide](k8s/argocd/README.md)
- [Application Manifests Guide](k8s/app/README.md)

