import os
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "animal_atc")

# Global variables for database connection
_client: Optional[MongoClient] = None
_database: Optional[Database] = None

def get_client() -> MongoClient:
    """Get MongoDB client instance"""
    global _client
    if _client is None:
        # Fail fast if Mongo isn't reachable to avoid request stalls
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=2000,
        )
    return _client

def get_db() -> Database:
    """Get database instance"""
    global _database
    if _database is None:
        client = get_client()
        _database = client[DB_NAME]
    return _database

def get_animals_collection() -> Collection:
    """Get animals collection with indexes"""
    db = get_db()
    collection = db.animals
    
    # Create indexes if they don't exist
    try:
        collection.create_index("animalID", unique=True)
        collection.create_index("timestamp")
        collection.create_index([("animalID", 1), ("timestamp", -1)])
    except Exception as e:
        # Indexes might already exist, ignore error
        pass
    
    return collection

def close_connection():
    """Close MongoDB connection"""
    global _client
    if _client:
        _client.close()
        _client = None
