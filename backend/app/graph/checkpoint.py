# checkpoint.py
import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver

# Configure logging
logger = logging.getLogger(__name__)

def get_checkpointer():
    logger.info("[checkpoint] Initializing MongoDB checkpointer")
    # Load environment variables
    load_dotenv()

    # Read MongoDB connection details
    MONGODB_IP = os.getenv('MONGODB_IP')
    MONGODB_USER = os.getenv('MONGODB_USER')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')

    if not all([MONGODB_IP, MONGODB_USER, MONGODB_PASSWORD]):
        logger.error("[checkpoint] Missing MongoDB environment variables")
        raise ValueError("Missing required MongoDB environment variables")

    # Create MongoDB URI and client
    MONGODB_URI = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_IP}:27017/admin"
    try:
        client = MongoClient(MONGODB_URI)
        logger.info("[checkpoint] Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"[checkpoint] Failed to connect to MongoDB: {str(e)}")
        raise

    # Return a MongoDBSaver instance
    logger.debug("[checkpoint] Creating MongoDBSaver instance")
    return MongoDBSaver(client)
