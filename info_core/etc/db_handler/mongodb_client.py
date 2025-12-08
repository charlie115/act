import os
import sys
import pymongo
import threading
upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import InfoCoreLogger


class InitDBClient:
    """
    MongoDB client with connection pooling using singleton pattern.

    PyMongo's MongoClient already implements connection pooling internally.
    This class ensures we reuse the same MongoClient instance per URI
    instead of creating new connections for every operation.
    """

    # Class-level cache for MongoClient instances (keyed by URI)
    _client_cache = {}
    _cache_lock = threading.Lock()

    # Track which indexes have been created to avoid redundant calls
    _indexes_created = set()
    _index_lock = threading.Lock()

    def __init__(self, host, port, user, passwd, logging_dir=None):
        self.logger = None
        self.host = host
        self.port = port
        self.username = user
        self.password = passwd
        self.uri = f"mongodb://{user}:{passwd}@{host}:{port}/"
        if logging_dir is not None:
            self.logger = InfoCoreLogger("InitDBClient", logging_dir).logger

    def get_conn(self):
        """
        Get a MongoClient connection with connection pooling.

        Uses a class-level cache to reuse MongoClient instances.
        PyMongo's MongoClient is thread-safe and handles connection pooling internally.

        Note: Cache key includes PID to ensure each forked process gets its own
        connection pool, avoiding PyMongo's "opened before fork" warning.
        """
        # Include PID in cache key to make connections fork-safe
        # Each child process will create its own connection pool
        cache_key = f"{self.uri}:{os.getpid()}"

        with InitDBClient._cache_lock:
            if cache_key not in InitDBClient._client_cache:
                # Configure connection pool settings for high-throughput workloads
                # Note: At interval boundaries (e.g., :00, :30), multiple kline processes
                # insert simultaneously, causing insert times to spike from ~2s to ~28s.
                # Timeout values are set to handle these concurrent operation storms.
                # Pool size reduced: 24 processes × 25 max = 600 total connections
                # This reduces memory overhead and connection churn while maintaining throughput
                mongo_client = pymongo.MongoClient(
                    self.uri,
                    maxPoolSize=25,            # Reduced from 100 (24 processes share the load)
                    minPoolSize=5,             # Reduced from 10 (faster startup, lower baseline)
                    maxIdleTimeMS=60000,       # Close idle connections after 60s
                    waitQueueTimeoutMS=10000,  # Wait up to 10s for available connection
                    serverSelectionTimeoutMS=30000,  # Timeout for server selection (30s for failover)
                    connectTimeoutMS=10000,    # Connection timeout (10s for network latency)
                    socketTimeoutMS=120000,    # Socket timeout for operations (120s for large batch inserts)
                )
                InitDBClient._client_cache[cache_key] = mongo_client
                if self.logger:
                    self.logger.info(f"Created new MongoDB connection pool for {self.host}:{self.port} (PID:{os.getpid()})")
            return InitDBClient._client_cache[cache_key]

    def ensure_indexes(self, database_name, collection_name):
        """
        Ensure indexes exist on a collection for optimal query performance.
        Creates index on datetime_now (descending) if it doesn't exist.

        This is called lazily and cached to avoid redundant index creation checks.
        """
        index_key = f"{self.uri}:{database_name}:{collection_name}"

        # Quick check without lock first (for performance)
        if index_key in InitDBClient._indexes_created:
            return

        with InitDBClient._index_lock:
            # Double-check after acquiring lock
            if index_key in InitDBClient._indexes_created:
                return

            try:
                mongo_client = self.get_conn()
                db = mongo_client[database_name]
                collection = db[collection_name]

                # Check existing indexes
                existing_indexes = collection.index_information()

                # Create datetime_now descending index if not exists
                if 'datetime_now_-1' not in existing_indexes:
                    collection.create_index(
                        [("datetime_now", pymongo.DESCENDING)],
                        background=True  # Non-blocking index creation
                    )
                    if self.logger:
                        self.logger.info(f"Created index on datetime_now for {database_name}.{collection_name}")

                # Mark as created
                InitDBClient._indexes_created.add(index_key)

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to create index for {database_name}.{collection_name}: {e}")
                # Don't cache failure - allow retry

    def get_last_datetime(self, database_name, collection_name):
        """
        Get the last datetime_now value from a collection efficiently.
        Uses the datetime_now index for O(1) lookup instead of full scan.

        Returns None if collection is empty or doesn't exist.
        """
        try:
            # Ensure index exists first
            self.ensure_indexes(database_name, collection_name)

            mongo_client = self.get_conn()
            db = mongo_client[database_name]
            collection = db[collection_name]

            # Use hint to force index usage, project only what we need
            result = collection.find_one(
                {},
                {'datetime_now': 1, '_id': 0},
                sort=[("datetime_now", pymongo.DESCENDING)],
                hint=[("datetime_now", pymongo.DESCENDING)]
            )

            if result:
                return result.get('datetime_now')
            return None

        except Exception:
            # Collection might not exist yet
            return None

    def is_collection_empty(self, database_name, collection_name):
        """
        Check if a collection is empty efficiently.
        Uses estimated_document_count() which reads from collection metadata
        instead of scanning all documents.

        Returns True if collection is empty or doesn't exist.
        """
        try:
            mongo_client = self.get_conn()
            db = mongo_client[database_name]
            collection = db[collection_name]

            # estimated_document_count() uses collection metadata - O(1)
            # Much faster than count_documents({}) which scans all docs
            return collection.estimated_document_count() == 0

        except Exception:
            # Collection might not exist yet
            return True

    @classmethod
    def close_all_connections(cls):
        """
        Close all cached MongoDB connections.
        Call this during graceful shutdown.
        """
        with cls._cache_lock:
            for uri, client in cls._client_cache.items():
                try:
                    client.close()
                except Exception:
                    pass
            cls._client_cache.clear()
            cls._indexes_created.clear()
