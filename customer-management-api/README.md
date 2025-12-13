# Customer Management API

FastAPI-based backend API that consumes purchase events from Kafka and stores them in MongoDB.

## Overview

The Customer Management API is a FastAPI application that:
- Consumes purchase events from Kafka
- Stores purchase records in MongoDB
- Provides REST API endpoints to retrieve purchase data
- Exposes Prometheus metrics for monitoring and autoscaling

## Application Details

**Technology Stack**:
- FastAPI (Python web framework)
- PyMongo (MongoDB driver)
- Confluent Kafka (message consumer)
- Prometheus FastAPI Instrumentator (metrics)

**Port**: 8000 (configurable via `PORT` environment variable)

## Endpoints

### API Endpoints

- `GET /api/purchases/{userId}` - Get all purchases for a specific user
  ```json
  {
    "purchases": [...],
    "userId": "user123"
  }
  ```

- `GET /api/purchases?limit=100` - Get all purchases (for testing/debugging)
  ```json
  {
    "purchases": [...],
    "count": 10
  }
  ```

- `GET /health` - Health check endpoint with MongoDB and Kafka status
  ```json
  {
    "status": "healthy",
    "service": "customer-management-api",
    "mongodb": "connected",
    "kafka": "consuming"
  }
  ```

- `GET /metrics` - Prometheus metrics endpoint

## Metrics

The application exposes Prometheus metrics at `/metrics` endpoint for monitoring and autoscaling.

### Available Metrics

**HTTP Metrics** (via `prometheus-fastapi-instrumentator`):
- `http_requests_total` - Total number of HTTP requests
  - Labels: `method`, `handler`, `status`
  - Example: `http_requests_total{method="GET",handler="/api/purchases/{userId}",status="2xx"}`
  
- `http_request_duration_seconds` - Request duration histogram
  - Labels: `method`, `handler`, `status`

**Key Metrics for Autoscaling**:
```promql
# Kafka consumer lag (used by KEDA for scaling)
# This is handled by KEDA's Kafka scaler, not Prometheus
```

### Accessing Metrics

**Local**:
```bash
curl http://localhost:8000/metrics
```

**Kubernetes**:
```bash
# Port forward
kubectl port-forward svc/backend-app -n app 8000:8000

# Access metrics
curl http://localhost:8000/metrics
```

**From within cluster**:
```bash
curl http://backend-app.app.svc.cluster.local:8000/metrics
```

### Metrics Labels

The application adds a `service` label to all metrics:
- `service="backend-app"` - Identifies metrics from this service

This label is used by:
- Prometheus for scraping and querying
- Monitoring dashboards

### Prometheus Scraping

Prometheus is configured to scrape metrics from this application:
- **Job**: `backend-app`
- **Endpoint**: `http://backend-app.app.svc.cluster.local:8000/metrics`
- **Interval**: 15 seconds

### Autoscaling

The backend uses **Kafka-based autoscaling** via KEDA:
- **Scaler**: Kafka consumer lag
- **Min replicas**: 2
- **Max replicas**: 10
- **Lag threshold**: 10 messages per pod

KEDA monitors Kafka consumer lag and scales pods based on message backlog, not HTTP metrics.

## Configuration

### Environment Variables

- `MONGODB_URI` - MongoDB connection string (default: `mongodb://localhost:27017/purchases`)
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker address (default: `localhost:9092`)
- `KAFKA_TOPIC` - Kafka topic to consume (default: `purchase-events`)
- `KAFKA_GROUP_ID` - Kafka consumer group ID (default: `customer-management-api`)
- `PORT` - Application port (default: `8000`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

### Kafka Consumer

The application runs a background thread that:
- Consumes messages from `purchase-events` topic
- Processes and stores purchase events in MongoDB
- Handles consumer group coordination for scaling

**Consumer Group**: `customer-management-api`
- Multiple pods share the same consumer group
- Kafka distributes partitions across pods
- Enables horizontal scaling

### MongoDB Integration

Purchase events are stored in MongoDB:
- **Database**: `purchases` (from MongoDB URI)
- **Collection**: `purchases`
- **Index**: Created on `userId` for fast queries

Purchase document structure:
```json
{
  "_id": "ObjectId",
  "userId": "user123",
  "username": "john_doe",
  "price": 99.99,
  "timestamp": "2024-01-01T00:00:00Z",
  "eventType": "purchase_request",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

## Development

### Run Locally

```bash
# Install dependencies
make install-deps

# Run application
make run

# Or directly
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Tests

```bash
make test
```

### Build Docker Image

```bash
make build
# Or with custom tag
make build IMAGE_TAG=backend-v1.0.0
```

## Troubleshooting

### Metrics Not Available

**Issue**: `/metrics` endpoint returns 404 or empty

**Solutions**:
```bash
# Verify prometheus-fastapi-instrumentator is installed
pip list | grep prometheus-fastapi-instrumentator

# Check application logs
kubectl logs -n app deployment/backend-app | grep -i metric

# Verify metrics endpoint
curl http://localhost:8000/metrics
```

### Kafka Consumer Not Running

**Issue**: Health check shows `"kafka": "not running"`

**Solutions**:
```bash
# Check application logs
kubectl logs -n app deployment/backend-app | grep -i kafka

# Verify Kafka service
kubectl get svc -n kafka kafka

# Check consumer group status
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-consumer-groups.sh \
  --describe --group customer-management-api --bootstrap-server localhost:9092
```

### MongoDB Connection Issues

**Issue**: Health check shows MongoDB error

**Solutions**:
```bash
# Check MongoDB connectivity
kubectl logs -n app deployment/backend-app | grep -i mongo

# Verify MongoDB service
kubectl get svc -n mongo mongo

# Test MongoDB connection
kubectl run mongo-test --rm -it --image=mongo:7.0 --restart=Never -n mongo -- \
  mongosh mongodb://mongo:27017/purchases
```

### No Data in MongoDB

**Issue**: API returns empty purchases

**Solutions**:
```bash
# Check if Kafka consumer is processing messages
kubectl logs -n app deployment/backend-app | grep -i "Processing purchase event"

# Verify Kafka topic has messages
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh \
  --topic purchase-events --bootstrap-server localhost:9092 --from-beginning --max-messages 5

# Check MongoDB directly
kubectl -n mongo exec -it mongo-0 -- mongosh purchases --eval "db.purchases.find().limit(5)"
```

### Health Check Failing

**Issue**: `/health` endpoint returns 503

**Solutions**:
```bash
# Check health status details
curl http://localhost:8000/health | jq

# Check MongoDB connection
kubectl logs -n app deployment/backend-app | grep -i mongo

# Check Kafka consumer status
kubectl logs -n app deployment/backend-app | grep -i "consumer"
```

## Monitoring

### Key Metrics to Monitor

1. **Request Rate**: `rate(http_requests_total{service="backend-app"}[5m])`
2. **Error Rate**: `rate(http_requests_total{service="backend-app",status=~"5.."}[5m])`
3. **Response Time**: `histogram_quantile(0.95, http_request_duration_seconds{service="backend-app"})`
4. **Kafka Consumer Lag**: Checked by KEDA ScaledObject

### Prometheus Queries

**Total API requests in last hour**:
```promql
sum(increase(http_requests_total{service="backend-app"}[1h]))
```

**Error rate percentage**:
```promql
sum(rate(http_requests_total{service="backend-app",status=~"5.."}[5m])) / 
sum(rate(http_requests_total{service="backend-app"}[5m])) * 100
```

**Average response time**:
```promql
rate(http_request_duration_seconds_sum{service="backend-app"}[5m]) / 
rate(http_request_duration_seconds_count{service="backend-app"}[5m])
```

**Requests per endpoint**:
```promql
sum by (handler) (rate(http_requests_total{service="backend-app"}[5m]))
```

### Kafka Consumer Monitoring

**Check consumer lag** (via KEDA):
```bash
kubectl describe scaledobject backend-app-scaledobject -n app
```

**Check consumer group status**:
```bash
kubectl -n kafka exec -it kafka-0 -- /opt/kafka/bin/kafka-consumer-groups.sh \
  --describe --group customer-management-api --bootstrap-server localhost:9092
```

## Deployment

See `../k8s/app/backend/README.md` for Kubernetes deployment instructions.
