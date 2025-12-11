"""
Customer Facing Web Server
Handles buy requests and serves HTML UI
"""
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import httpx
import json
import logging
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from confluent_kafka import Producer
from confluent_kafka import KafkaError as ConfluentKafkaError
from confluent_kafka.admin import AdminClient
from contextlib import asynccontextmanager

# Templates directory - handle both development and Docker paths
base_dir = Path(__file__).parent.parent
templates_dir = base_dir / "templates"
if not templates_dir.exists():
    # Fallback for Docker container path
    templates_dir = Path("/app/templates")
templates = Jinja2Templates(directory=str(templates_dir))

# Configuration from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").strip()
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "purchase-events")
CUSTOMER_API_URL = os.getenv("CUSTOMER_API_URL", "http://localhost:8000")
PORT = int(os.getenv("PORT", "8001"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Kafka producer instance
kafka_producer: Optional[Producer] = None


# Pydantic models
class BuyRequest(BaseModel):
    username: str
    userId: str
    price: float
    timestamp: Optional[str] = None


def get_kafka_producer() -> Optional[Producer]:
    """
    Get or create Kafka producer instance
    Returns None if Kafka is not available
    """
    global kafka_producer
    
    if kafka_producer is None:
        try:
            # Confluent Kafka configuration
            # Ensure bootstrap servers is properly formatted
            bootstrap_servers = KAFKA_BOOTSTRAP_SERVERS.strip()
            logger.info(f"Configuring Kafka producer with bootstrap servers: {bootstrap_servers}")
            
            config = {
                'bootstrap.servers': bootstrap_servers,
                'acks': 'all',  # Wait for all replicas to acknowledge
                'retries': 3,
                'max.in.flight.requests.per.connection': 1,
                'enable.idempotence': True,
                'request.timeout.ms': 30000,
                'message.timeout.ms': 30000,
                'socket.timeout.ms': 30000,
                'metadata.request.timeout.ms': 30000,
            }
            
            kafka_producer = Producer(config)
            logger.info(f"Kafka producer initialized with servers: {bootstrap_servers}")
            # Test connection by getting metadata
            try:
                metadata = kafka_producer.list_topics(timeout=10)
                logger.info(f"Kafka connection verified. Available topics: {len(metadata.topics)}")
            except Exception as e:
                logger.warning(f"Kafka metadata check failed (may be normal): {str(e)}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}")
            return None
    
    return kafka_producer


def publish_to_kafka(topic: str, key: str, value: dict) -> bool:
    """
    Publish message to Kafka topic
    Returns True if successful, False otherwise
    """
    producer = get_kafka_producer()
    if producer is None:
        logger.warning("Kafka producer not available, skipping publish")
        return False
    
    try:
        # Serialize value to JSON
        value_json = json.dumps(value).encode('utf-8')
        key_bytes = key.encode('utf-8') if key else None
        
        # Produce message with delivery callback
        delivery_status = {'delivered': False, 'error': None, 'completed': False}
        
        def delivery_callback(err, msg):
            delivery_status['completed'] = True
            if err:
                delivery_status['error'] = err
                _delivery_callback(err, msg)
            else:
                delivery_status['delivered'] = True
                _delivery_callback(None, msg)
        
        producer.produce(
            topic,
            value=value_json,
            key=key_bytes,
            callback=delivery_callback
        )
        
        # Poll to trigger delivery callbacks and wait for completion
        # Poll multiple times to ensure callback is processed
        for _ in range(100):  # Poll up to 100 times (1 second max)
            producer.poll(0.01)  # Poll with 10ms timeout
            if delivery_status['completed']:
                break
        
        # Flush to ensure message is sent (with timeout)
        producer.flush(timeout=10)
        
        # Check delivery status after flush
        if delivery_status['error']:
            logger.error(f"Message delivery failed: {delivery_status['error']}")
            return False
        
        if delivery_status['delivered']:
            logger.info(f"Message published to Kafka - Topic: {topic}, Key: {key}")
            return True
        else:
            logger.warning(f"Message delivery status unknown - Topic: {topic}, Key: {key}, Completed: {delivery_status['completed']}")
            # Still return True if flush succeeded (message might be in transit)
            return True
    except ConfluentKafkaError as e:
        logger.error(f"Kafka error while publishing: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while publishing to Kafka: {str(e)}")
        return False


def _delivery_callback(err, msg):
    """Callback for message delivery confirmation"""
    if err:
        logger.error(f"Message delivery failed: {err}")
        logger.error(f"Error details - code: {err.code()}, name: {err.name()}, str: {err.str()}")
    else:
        logger.info(
            f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown
    """
    # Startup
    logger.info("Starting Customer Web Server...")
    logger.info(f"Kafka Bootstrap Servers: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Kafka Topic: {KAFKA_TOPIC}")
    
    # Initialize Kafka producer on startup
    get_kafka_producer()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Customer Web Server...")
    global kafka_producer
    if kafka_producer is not None:
        try:
            kafka_producer.flush(timeout=10)
            # Confluent Kafka Producer doesn't have a close() method, just flush
            logger.info("Kafka producer flushed and closed")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {str(e)}")
        finally:
            kafka_producer = None


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Customer Web Server",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Serve the main UI page with Buy and GetAllUserBuys forms
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/buy")
async def buy(buy_request: BuyRequest):
    """
    Handle buy request - publish purchase event to Kafka
    """
    try:
        # Prepare event payload with timestamp
        # Use provided timestamp or generate current ISO format timestamp
        if buy_request.timestamp:
            event_timestamp = buy_request.timestamp
        else:
            event_timestamp = datetime.utcnow().isoformat() + "Z"
        
        event_payload = {
            "userId": buy_request.userId,
            "username": buy_request.username,
            "price": buy_request.price,
            "timestamp": event_timestamp,
            "eventType": "purchase_request"
        }
        
        # Publish to Kafka
        kafka_success = publish_to_kafka(
            topic=KAFKA_TOPIC,
            key=buy_request.userId,  # Use userId as key for partitioning
            value=event_payload
        )
        
        if kafka_success:
            logger.info(f"Purchase event published to Kafka for user {buy_request.userId}")
            message = "Purchase request received and published to Kafka successfully"
        else:
            logger.warning(f"Purchase event received but failed to publish to Kafka for user {buy_request.userId}")
            message = "Purchase request received, but Kafka is not available. Event may be lost."
        
        return JSONResponse(
            status_code=200,
            content={
                "message": message,
                "status": "success",
                "kafka_published": kafka_success,
                "data": {
                    "username": buy_request.username,
                    "userId": buy_request.userId,
                    "price": buy_request.price
                }
            }
        )
    except Exception as e:
        logger.error(f"Error processing purchase request: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "message": f"Error processing purchase: {str(e)}",
                "status": "error"
            }
        )


@app.get("/getAllUserBuys")
async def get_all_user_buys(request: Request, userId: str):
    """
    Get all purchases for a user
    Can return HTML page or JSON based on Accept header
    """
    try:
        # Try to fetch from Customer Management API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{CUSTOMER_API_URL}/api/purchases/{userId}"
                )
                if response.status_code == 200:
                    data = response.json()
                    # Backend returns {"purchases": [...], "userId": "..."}
                    purchases = data.get("purchases", [])
                    logger.info(f"Retrieved {len(purchases)} purchases for user {userId} from backend API")
                else:
                    logger.warning(f"Backend API returned status {response.status_code} for user {userId}")
                    purchases = []
        except Exception as e:
            # API not available yet - return empty list for UI testing
            logger.error(f"Error fetching purchases from backend API: {str(e)}", exc_info=True)
            purchases = []
        
        # Check if request wants JSON
        accept = request.headers.get("accept", "")
        if "application/json" in accept:
            return JSONResponse(content={"purchases": purchases, "userId": userId})
        
        # Return HTML page
        return templates.TemplateResponse("purchases.html", {
            "request": request,
            "purchases": purchases,
            "userId": userId
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": f"Error fetching purchases: {str(e)}",
                "status": "error"
            }
        )


@app.get("/health")
async def health():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "customer-web-server"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

