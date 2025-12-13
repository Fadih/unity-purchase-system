# Customer Web Server

FastAPI-based web server that handles purchase requests and serves the customer-facing UI.

## Overview

The Customer Web Server is a FastAPI application that:
- Serves HTML UI for customers to make purchases
- Publishes purchase events to Kafka
- Retrieves purchase history from the backend API
- Exposes Prometheus metrics for monitoring and autoscaling

## Application Details

**Technology Stack**:
- FastAPI (Python web framework)
- Jinja2 (HTML templating)
- Confluent Kafka (message producer)
- Prometheus FastAPI Instrumentator (metrics)

**Port**: 8001 (configurable via `PORT` environment variable)

## Endpoints

### Web Endpoints

- `GET /` - Home page with purchase form
- `GET /getAllUserBuys?userId=<userId>` - View user's purchase history (HTML or JSON)
- `POST /buy` - Submit a purchase request

### API Endpoints

- `GET /health` - Health check endpoint
  ```json
  {
    "status": "healthy",
    "service": "customer-web-server"
  }
  ```

- `GET /metrics` - Prometheus metrics endpoint

## Metrics

The application exposes Prometheus metrics at `/metrics` endpoint for monitoring and autoscaling.

### Available Metrics

**HTTP Metrics** (via `prometheus-fastapi-instrumentator`):
- `http_requests_total` - Total number of HTTP requests
  - Labels: `method`, `handler`, `status`
  - Example: `http_requests_total{method="POST",handler="/buy",status="2xx"}`
  
- `http_request_duration_seconds` - Request duration histogram
  - Labels: `method`, `handler`, `status`

**Key Metrics for Autoscaling**:
```promql
# Total requests per second (excluding health/metrics)
sum(rate(http_requests_total{service="frontend-app",handler!="/health",handler!="/metrics"}[1m]))
```

### Accessing Metrics

**Local**:
```bash
curl http://localhost:8001/metrics
```

**Kubernetes**:
```bash
# Port forward
kubectl port-forward svc/frontend-app -n app 8001:8001

# Access metrics
curl http://localhost:8001/metrics
```

**From within cluster**:
```bash
curl http://frontend-app.app.svc.cluster.local:8001/metrics
```

### Metrics Labels

The application adds a `service` label to all metrics:
- `service="frontend-app"` - Identifies metrics from this service

This label is used by:
- Prometheus for scraping and querying
- KEDA ScaledObject for autoscaling decisions

### Prometheus Scraping

Prometheus is configured to scrape metrics from this application:
- **Job**: `frontend-app`
- **Endpoint**: `http://frontend-app.app.svc.cluster.local:8001/metrics`
- **Interval**: 15 seconds

### Metrics Used for Autoscaling

The KEDA ScaledObject uses these metrics:
- **HTTP Request Rate**: Scales based on total requests/second (excluding health/metrics)
- **CPU Utilization**: Scales based on CPU usage (70% threshold)

## Configuration

### Environment Variables

- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker address (default: `localhost:9092`)
- `KAFKA_TOPIC` - Kafka topic for purchase events (default: `purchase-events`)
- `CUSTOMER_API_URL` - Backend API URL (default: `http://localhost:8000`)
- `PORT` - Application port (default: `8001`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

### Kafka Integration

The application publishes purchase events to Kafka:
- **Topic**: `purchase-events` (configurable)
- **Key**: `userId`
- **Format**: JSON

Example event:
```json
{
  "userId": "user123",
  "username": "john_doe",
  "price": 99.99,
  "timestamp": "2024-01-01T00:00:00Z",
  "eventType": "purchase_request"
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
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Run Tests

```bash
make test
```

### Build Docker Image

```bash
make build
# Or with custom tag
make build IMAGE_TAG=frontend-v1.0.0
```

## Troubleshooting

### Metrics Not Available

**Issue**: `/metrics` endpoint returns 404 or empty

**Solutions**:
```bash
# Verify prometheus-fastapi-instrumentator is installed
pip list | grep prometheus-fastapi-instrumentator

# Check application logs
kubectl logs -n app deployment/frontend-app | grep -i metric

# Verify metrics endpoint
curl http://localhost:8001/metrics
```

### Kafka Connection Issues

**Issue**: Purchase events not being published

**Solutions**:
```bash
# Check Kafka connectivity
kubectl logs -n app deployment/frontend-app | grep -i kafka

# Verify Kafka service
kubectl get svc -n kafka kafka

# Test Kafka connection
kubectl run kafka-test --rm -it --image=apache/kafka:4.0.0 --restart=Never -n kafka -- \
  /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server kafka:9092
```

### Health Check Failing

**Issue**: `/health` endpoint not responding

**Solutions**:
```bash
# Check application is running
kubectl get pods -n app -l app=frontend-app

# Check logs
kubectl logs -n app -l app=frontend-app --tail=50

# Test health endpoint
curl http://localhost:8001/health
```

## Monitoring

### Key Metrics to Monitor

1. **Request Rate**: `rate(http_requests_total{service="frontend-app"}[5m])`
2. **Error Rate**: `rate(http_requests_total{service="frontend-app",status=~"5.."}[5m])`
3. **Response Time**: `histogram_quantile(0.95, http_request_duration_seconds{service="frontend-app"})`
4. **Active Connections**: Check application logs

### Prometheus Queries

**Total requests in last hour**:
```promql
sum(increase(http_requests_total{service="frontend-app"}[1h]))
```

**Error rate percentage**:
```promql
sum(rate(http_requests_total{service="frontend-app",status=~"5.."}[5m])) / 
sum(rate(http_requests_total{service="frontend-app"}[5m])) * 100
```

**Average response time**:
```promql
rate(http_request_duration_seconds_sum{service="frontend-app"}[5m]) / 
rate(http_request_duration_seconds_count{service="frontend-app"}[5m])
```

## Deployment

See `../k8s/app/frontend/README.md` for Kubernetes deployment instructions.

