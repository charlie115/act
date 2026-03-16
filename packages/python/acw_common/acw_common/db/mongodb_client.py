import logging
import os
import threading

import pymongo


class InitDBClient:
    """
    MongoDB client with connection pooling using singleton pattern.

    PyMongo's MongoClient already implements connection pooling internally.
    This class ensures we reuse the same MongoClient instance per URI
    instead of creating new connections for every operation.

    Important: Do NOT call mongo_client.close() on connections obtained from
    get_conn(). The connection pool manages the lifecycle automatically.
    """

    # Class-level cache for MongoClient instances (keyed by URI + PID)
    _client_cache = {}
    _cache_lock = threading.Lock()

    # Track which indexes have been created to avoid redundant calls
    _indexes_created = set()
    _index_lock = threading.Lock()

    def __init__(self, host, port, user, passwd, logging_dir=None, logger=None):
        self.host = host
        self.port = port
        self.username = user
        self.password = passwd
        self.uri = f"mongodb://{user}:{passwd}@{host}:{port}/"
        self.logger = logger

    def get_conn(self):
        """
        Get a MongoClient connection with connection pooling.

        Uses a class-level cache to reuse MongoClient instances.
        PyMongo's MongoClient is thread-safe and handles connection pooling internally.

        Cache key includes PID to ensure each forked process gets its own
        connection pool, avoiding PyMongo's "opened before fork" warning.
        """
        cache_key = f"{self.uri}:{os.getpid()}"

        with InitDBClient._cache_lock:
            if cache_key not in InitDBClient._client_cache:
                mongo_client = pymongo.MongoClient(
                    self.uri,
                    maxPoolSize=25,
                    minPoolSize=5,
                    maxIdleTimeMS=60000,
                    waitQueueTimeoutMS=10000,
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=120000,
                )
                InitDBClient._client_cache[cache_key] = mongo_client
                if self.logger:
                    self.logger.info(
                        f"Created new MongoDB connection pool for {self.host}:{self.port} (PID:{os.getpid()})"
                    )
            return InitDBClient._client_cache[cache_key]

    def ensure_indexes(self, database_name, collection_name):
        """
        Ensure indexes exist on a collection for optimal query performance.
        Creates index on datetime_now (descending) if it doesn't exist.
        Cached to avoid redundant index creation checks.
        """
        index_key = f"{self.uri}:{database_name}:{collection_name}"

        if index_key in InitDBClient._indexes_created:
            return

        with InitDBClient._index_lock:
            if index_key in InitDBClient._indexes_created:
                return

            try:
                mongo_client = self.get_conn()
                collection = mongo_client[database_name][collection_name]
                existing_indexes = collection.index_information()

                if "datetime_now_-1" not in existing_indexes:
                    collection.create_index(
                        [("datetime_now", pymongo.DESCENDING)],
                        background=True,
                    )
                    if self.logger:
                        self.logger.info(
                            f"Created index on datetime_now for {database_name}.{collection_name}"
                        )

                InitDBClient._indexes_created.add(index_key)
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"Failed to create index for {database_name}.{collection_name}: {e}"
                    )

    def get_last_datetime(self, database_name, collection_name):
        """
        Get the last datetime_now value from a collection efficiently.
        Uses the datetime_now index for O(1) lookup.
        """
        try:
            self.ensure_indexes(database_name, collection_name)
            collection = self.get_conn()[database_name][collection_name]
            result = collection.find_one(
                {},
                {"datetime_now": 1, "_id": 0},
                sort=[("datetime_now", pymongo.DESCENDING)],
                hint=[("datetime_now", pymongo.DESCENDING)],
            )
            return result.get("datetime_now") if result else None
        except Exception:
            return None

    def is_collection_empty(self, database_name, collection_name):
        """
        Check if a collection is empty efficiently.
        Uses estimated_document_count() which reads from collection metadata (O(1)).
        """
        try:
            collection = self.get_conn()[database_name][collection_name]
            return collection.estimated_document_count() == 0
        except Exception:
            return True

    @classmethod
    def close_all_connections(cls):
        """Close all cached MongoDB connections. Call during graceful shutdown."""
        with cls._cache_lock:
            for _key, client in cls._client_cache.items():
                try:
                    client.close()
                except Exception:
                    pass
            cls._client_cache.clear()
            cls._indexes_created.clear()
