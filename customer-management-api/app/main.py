"""
Customer Management API
Consumes purchase events from Kafka and stores them in MongoDB
Provides API endpoints to retrieve purchase data
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
import json
import logging
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager
from pydantic import BaseModel
from confluent_kafka import Consumer, KafkaError as ConfluentKafkaError
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import threading
import time

# Configuration from environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/purchases")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").strip()
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "purchase-events")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "customer-management-api")
PORT = int(os.getenv("PORT", "8000"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
mongo_client: Optional[MongoClient] = None
kafka_consumer: Optional[Consumer] = None
consumer_thread: Optional[threading.Thread] = None
consumer_running = False


# Pydantic models
class Purchase(BaseModel):
    userId: str
    username: str
    price: float
    timestamp: Optional[str] = None
    eventType: Optional[str] = None
    _id: Optional[str] = None
    createdAt: Optional[str] = None


def get_mongo_client() -> MongoClient:
    """Get or create MongoDB client"""
    global mongo_client
    if mongo_client is None:
        try:
            mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            mongo_client.admin.command('ping')
            logger.info(f"MongoDB connected: {MONGODB_URI}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    return mongo_client


def get_database():
    """Get purchases database"""
    client = get_mongo_client()
    # Extract database name from URI or use default
    db_name = MONGODB_URI.split('/')[-1].split('?')[0] if '/' in MONGODB_URI else 'purchases'
    return client[db_name]


def get_collection():
    """Get purchases collection"""
    db = get_database()
    return db['purchases']


def get_kafka_consumer() -> Consumer:
    """Get or create Kafka consumer"""
    global kafka_consumer
    if kafka_consumer is None:
        try:
            config = {
                'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
                'group.id': KAFKA_GROUP_ID,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True,
                'auto.commit.interval.ms': 1000,
            }
            kafka_consumer = Consumer(config)
            logger.info(f"Kafka consumer initialized with servers: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {str(e)}")
            raise
    return kafka_consumer


def process_purchase_event(message_value: str) -> bool:
    """
    Process a purchase event from Kafka and store it in MongoDB
    Returns True if successful, False otherwise
    """
    try:
        # Parse the JSON message
        event_data = json.loads(message_value)
        logger.info(f"Processing purchase event: {event_data}")
        
        # Prepare document for MongoDB
        purchase_doc = {
            "userId": event_data.get("userId"),
            "username": event_data.get("username"),
            "price": event_data.get("price"),
            "timestamp": event_data.get("timestamp"),
            "eventType": event_data.get("eventType", "purchase_request"),
            "createdAt": datetime.utcnow().isoformat() + "Z"
        }
        
        # Insert into MongoDB
        collection = get_collection()
        result = collection.insert_one(purchase_doc)
        logger.info(f"Purchase stored in MongoDB with ID: {result.inserted_id}")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Kafka message as JSON: {str(e)}")
        return False
    except DuplicateKeyError as e:
        logger.warning(f"Duplicate purchase event (may be retry): {str(e)}")
        return True  # Consider duplicate as success
    except Exception as e:
        logger.error(f"Error processing purchase event: {str(e)}", exc_info=True)
        return False


def kafka_consumer_loop():
    """Main loop for consuming Kafka messages"""
    global consumer_running
    consumer = get_kafka_consumer()
    
    try:
        consumer.subscribe([KAFKA_TOPIC])
        logger.info(f"Subscribed to Kafka topic: {KAFKA_TOPIC}")
        consumer_running = True
        
        while consumer_running:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == ConfluentKafkaError._PARTITION_EOF:
                    # End of partition event - not an error
                    logger.debug(f"Reached end of partition {msg.partition()}")
                else:
                    logger.error(f"Kafka consumer error: {msg.error()}")
                continue
            
            # Process the message
            try:
                message_value = msg.value().decode('utf-8')
                logger.info(f"Received message from partition {msg.partition()}, offset {msg.offset()}")
                process_purchase_event(message_value)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Kafka consumer loop error: {str(e)}", exc_info=True)
    finally:
        consumer_running = False
        logger.info("Kafka consumer loop stopped")


def start_kafka_consumer():
    """Start Kafka consumer in a background thread"""
    global consumer_thread
    if consumer_thread is None or not consumer_thread.is_alive():
        consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
        consumer_thread.start()
        logger.info("Kafka consumer thread started")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown
    """
    # Startup
    logger.info("Starting Customer Management API...")
    logger.info(f"MongoDB URI: {MONGODB_URI}")
    logger.info(f"Kafka Bootstrap Servers: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Kafka Topic: {KAFKA_TOPIC}")
    logger.info(f"Kafka Group ID: {KAFKA_GROUP_ID}")
    
    # Initialize MongoDB connection
    try:
        get_mongo_client()
        # Create index on userId for faster queries
        collection = get_collection()
        collection.create_index("userId")
        logger.info("MongoDB index created on userId")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")
    
    # Start Kafka consumer
    try:
        start_kafka_consumer()
        # Give consumer a moment to start
        time.sleep(2)
    except Exception as e:
        logger.error(f"Failed to start Kafka consumer: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Customer Management API...")
    global consumer_running, kafka_consumer, mongo_client
    
    # Stop Kafka consumer
    consumer_running = False
    if kafka_consumer is not None:
        try:
            kafka_consumer.close()
            logger.info("Kafka consumer closed")
        except Exception as e:
            logger.error(f"Error closing Kafka consumer: {str(e)}")
        finally:
            kafka_consumer = None
    
    # Close MongoDB connection
    if mongo_client is not None:
        try:
            mongo_client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
        finally:
            mongo_client = None


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Customer Management API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "customer-management-api",
        "mongodb": "unknown",
        "kafka": "unknown"
    }
    
    # Check MongoDB
    try:
        get_mongo_client().admin.command('ping')
        health_status["mongodb"] = "connected"
    except Exception as e:
        health_status["mongodb"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Kafka consumer
    global consumer_running
    if consumer_running:
        health_status["kafka"] = "consuming"
    else:
        health_status["kafka"] = "not running"
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/api/purchases/{userId}")
async def get_purchases(userId: str):
    """
    Get all purchases for a specific user
    """
    try:
        collection = get_collection()
        purchases = list(collection.find({"userId": userId}).sort("createdAt", -1))
        
        # Convert ObjectId to string and format response
        result = []
        for purchase in purchases:
            purchase["_id"] = str(purchase["_id"])
            result.append(purchase)
        
        logger.info(f"Retrieved {len(result)} purchases for user {userId}")
        return JSONResponse(content={"purchases": result, "userId": userId})
        
    except Exception as e:
        logger.error(f"Error retrieving purchases for user {userId}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving purchases: {str(e)}")


@app.get("/api/purchases")
async def get_all_purchases(limit: int = 100):
    """
    Get all purchases (for testing/debugging)
    """
    try:
        collection = get_collection()
        purchases = list(collection.find().sort("createdAt", -1).limit(limit))
        
        # Convert ObjectId to string
        result = []
        for purchase in purchases:
            purchase["_id"] = str(purchase["_id"])
            result.append(purchase)
        
        logger.info(f"Retrieved {len(result)} purchases (limit: {limit})")
        return JSONResponse(content={"purchases": result, "count": len(result)})
        
    except Exception as e:
        logger.error(f"Error retrieving all purchases: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving purchases: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
