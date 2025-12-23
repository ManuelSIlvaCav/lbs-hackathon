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
                # Add readPreference to allow reading from secondaries if primary is unavailable
                mongodb_url = f"mongodb+srv://{user}:{password}@{domain}/?retryWrites=true&w=1&readPreference=primaryPreferred&appName=lbs-hackathon&tls=true&tlsAllowInvalidCertificates=false"
            elif domain == "localhost":
                mongodb_url = f"mongodb://{user}:{password}@{domain}:{port}"
            else:
                mongodb_url = f"mongodb://{user}:{password}@{domain}"

            logger.info(f"Connecting to MongoDB...")
            database_name = os.getenv("MONGODB_DATABASE", "lbs_hackathon")

            self._client = MongoClient(
                mongodb_url,
                maxPoolSize=150,
                minPoolSize=10,
                serverSelectionTimeoutMS=60000,  # Increase timeout to 60s
                connectTimeoutMS=60000,  # Connection timeout
                socketTimeoutMS=60000,  # Socket timeout
                retryWrites=True,
                retryReads=True,
                maxIdleTimeMS=45000,
                waitQueueTimeoutMS=10000,
                directConnection=False,  # Required for replica sets
            )
            self._db = self._client[database_name]

            # Test connection with retry logic using ping (works with secondaries)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Use ping command which works with secondaries
                    self._client.admin.command("ping")
                    logger.info(f"Connected to MongoDB")
                    logger.info(f"Using database: {database_name}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Connection attempt {attempt + 1} failed, retrying... Error: {e}"
                        )
                        import time

                        time.sleep(2)
                    else:
                        logger.error(
                            f"Failed to connect to MongoDB after {max_retries} attempts"
                        )
                        raise

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
                # Use ping command which works with secondaries
                self._client.admin.command("ping")
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
