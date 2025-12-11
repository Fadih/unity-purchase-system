# Customer Management API

FastAPI application that consumes purchase events from Kafka and stores them in MongoDB.

## Features

- 🔄 **Kafka Consumer** - Consumes purchase events from `purchase-events` topic
- 💾 **MongoDB Integration** - Stores purchase data in MongoDB
- 🔍 **Purchase Retrieval** - API endpoints to get purchase history
- 🚀 **FastAPI** - Modern, fast Python web framework
- 📦 **Docker Ready** - Containerized application

## Local Development

### Prerequisites
- Python 3.11+
- MongoDB running (local or remote)
- Kafka running (local or remote)

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

### Build Image

```bash
docker build -t customer-management-api:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e MONGODB_URI=mongodb://mongodb:27017/purchases \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  -e KAFKA_TOPIC=purchase-events \
  -e KAFKA_GROUP_ID=customer-management-api \
  customer-management-api:latest
```

## Environment Variables

- `MONGODB_URI` - MongoDB connection string (default: mongodb://localhost:27017/purchases)
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker addresses (default: localhost:9092)
- `KAFKA_TOPIC` - Kafka topic name (default: purchase-events)
- `KAFKA_GROUP_ID` - Kafka consumer group ID (default: customer-management-api)
- `PORT` - Server port (default: 8000)

## API Endpoints

- `GET /api/purchases/{userId}` - Get all purchases for a user
- `GET /api/purchases` - Get all purchases (for testing, with limit)
- `GET /health` - Health check (includes MongoDB and Kafka status)

## Kafka Consumer

The API automatically consumes messages from the `purchase-events` Kafka topic and stores them in MongoDB. The consumer runs in a background thread and processes messages asynchronously.

## MongoDB Schema

Purchases are stored in the `purchases` collection with the following structure:

```json
{
  "_id": "ObjectId",
  "userId": "string",
  "username": "string",
  "price": 0.0,
  "timestamp": "ISO8601 string",
  "eventType": "purchase_request",
  "createdAt": "ISO8601 string"
}
```

## Project Structure

```
customer-management-api/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI application with Kafka consumer
├── requirements.txt
├── Dockerfile
└── README.md
```
