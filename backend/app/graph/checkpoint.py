# checkpoint.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver

def get_checkpointer():
    # Load environment variables
    load_dotenv()

    # Read MongoDB connection details
    MONGODB_IP = os.getenv('MONGODB_IP')
    MONGODB_USER = os.getenv('MONGODB_USER')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')

    # Create MongoDB URI and client
    MONGODB_URI = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_IP}:27017/admin"
    client = MongoClient(MONGODB_URI)

    # Return a MongoDBSaver instance
    return MongoDBSaver(client)
