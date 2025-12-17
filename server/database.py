"""
Database configuration and connection management using pymongo
"""

import logging
import os
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional


logger = logging.getLogger("app")


class DatabaseManager:
    """Singleton database manager using pymongo"""

    _instance: Optional["DatabaseManager"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def connect(self) -> Database:
        """Connect to MongoDB and return database instance"""
        if self._client is None:
            user = os.getenv("MONGODB_USER", "admin")
            password = os.getenv("MONGODB_PASSWORD", "admin123")
            domain = os.getenv("MONGODB_DOMAIN", "localhost")
            port = os.getenv("MONGODB_PORT", "27017")

            # Check if it's MongoDB Atlas (contains .mongodb.net)
            if "mongodb.net" in domain:
                # MongoDB Atlas requires +srv and query parameters
                mongodb_url = f"mongodb+srv://{user}:{password}@{domain}/?retryWrites=true&w=majority"
            elif domain == "localhost":
                mongodb_url = f"mongodb://{user}:{password}@{domain}:{port}"
            else:
                mongodb_url = f"mongodb://{user}:{password}@{domain}"

            logger.info(f"Connecting to MongoDB at {mongodb_url}...")
            database_name = os.getenv("MONGODB_DATABASE", "lbs_hackathon")

            self._client = MongoClient(mongodb_url, maxPoolSize=150)
            self._db = self._client[database_name]
            # Test connection
            self._client.server_info()
            logger.info(f"✅ Connected to MongoDB at {domain}")
            logger.info(f"✅ Using database: {database_name}")

        return self._db

    def get_database(self) -> Database:
        """Get database instance, connecting if necessary"""
        if self._db is None:
            return self.connect()
        return self._db

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection from the database"""
        db = self.get_database()
        return db[collection_name]

    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("✅ Closed MongoDB connection")

    def is_connected(self) -> bool:
        """Check if database is connected"""
        try:
            if self._client:
                self._client.server_info()
                return True
        except:
            pass
        return False


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Database:
    """Dependency function to get database instance"""
    return db_manager.get_database()


def get_collection(collection_name: str) -> Collection:
    """Helper function to get a collection"""
    return db_manager.get_collection(collection_name)
