import logging
from typing import Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError

from src.config import (
    MONGODB_URI,
    MONGODB_DATABASE,
    COLL_MOVIES,
    COLL_RATINGS,
    COLL_STATS,
    COLL_RECOMMENDATIONS,
    validate_config,
)

logger = logging.getLogger("MovieRecBDA.Database")

class MongoDBManager:
    """
    Singleton-style manager for MongoDB Atlas connection.
    """
    _client: Optional[MongoClient] = None

    @classmethod
    def get_client(cls, uri: Optional[str] = None) -> MongoClient:
        """
        Returns a connected PyMongo client instance.
        """
        target_uri = uri or MONGODB_URI
        is_valid, err_msg = validate_config() if not uri else (True, "")
        if not is_valid and not uri:
            raise ValueError(err_msg)

        if cls._client is None or uri is not None:
            try:
                # 5-second server selection timeout for quick fail in UI/tests if offline
                cls._client = MongoClient(target_uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
                # Force ping test
                cls._client.admin.command("ping")
                logger.info("Successfully established connection to MongoDB Atlas.")
            except (ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError) as e:
                logger.error(f"MongoDB Connection failed: {e}")
                raise ConnectionError(f"Failed to connect to MongoDB Atlas: {e}")
        return cls._client

    @classmethod
    def get_database(cls, uri: Optional[str] = None, db_name: Optional[str] = None):
        """
        Returns PyMongo database object.
        """
        client = cls.get_client(uri=uri)
        target_db = db_name or MONGODB_DATABASE
        return client[target_db]

    @classmethod
    def close_connection(cls):
        """
        Closes active client connection.
        """
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            logger.info("Closed MongoDB client connection.")

def ping_database(uri: Optional[str] = None) -> tuple[bool, str, Dict[str, Any]]:
    """
    Pings MongoDB Atlas server and returns status, message, and info dict.
    """
    is_valid, msg = validate_config()
    if not is_valid and not uri:
        return False, msg, {}

    try:
        db = MongoDBManager.get_database(uri=uri)
        ping_res = db.command("ping")
        server_info = db.client.server_info()
        return True, "MongoDB connection successful.", {
            "database_name": db.name,
            "version": server_info.get("version", "Unknown"),
            "ping": ping_res,
        }
    except Exception as e:
        return False, f"MongoDB connection error: {str(e)}", {}

def get_collection(coll_name: str, uri: Optional[str] = None):
    """
    Helper function to get a specific MongoDB collection.
    """
    db = MongoDBManager.get_database(uri=uri)
    return db[coll_name]

def create_indexes(db=None) -> Dict[str, list]:
    """
    Creates indexes on collections to optimize queries as per requirements:
    - movies: movieId (unique), title, genres
    - ratings: movieId, userId, rating, (movieId, userId) composite
    - movie_stats: movieId (unique), average_rating, rating_count
    - recommendations: source_movie_id
    """
    if db is None:
        db = MongoDBManager.get_database()

    results = {}

    # 1. Movies collection indexes
    movies_coll = db[COLL_MOVIES]
    idx1 = movies_coll.create_index([("movieId", ASCENDING)], unique=True, name="idx_movies_movieId")
    idx2 = movies_coll.create_index([("title", ASCENDING)], name="idx_movies_title")
    idx3 = movies_coll.create_index([("genres", ASCENDING)], name="idx_movies_genres")
    results[COLL_MOVIES] = [idx1, idx2, idx3]

    # 2. Ratings collection indexes
    ratings_coll = db[COLL_RATINGS]
    r_idx1 = ratings_coll.create_index([("movieId", ASCENDING)], name="idx_ratings_movieId")
    r_idx2 = ratings_coll.create_index([("userId", ASCENDING)], name="idx_ratings_userId")
    r_idx3 = ratings_coll.create_index([("rating", DESCENDING)], name="idx_ratings_rating")
    r_idx4 = ratings_coll.create_index([("movieId", ASCENDING), ("userId", ASCENDING)], unique=True, name="idx_ratings_movie_user")
    results[COLL_RATINGS] = [r_idx1, r_idx2, r_idx3, r_idx4]

    # 3. Movie stats collection indexes
    stats_coll = db[COLL_STATS]
    s_idx1 = stats_coll.create_index([("movieId", ASCENDING)], unique=True, name="idx_stats_movieId")
    s_idx2 = stats_coll.create_index([("average_rating", DESCENDING)], name="idx_stats_avg_rating")
    s_idx3 = stats_coll.create_index([("rating_count", DESCENDING)], name="idx_stats_rating_count")
    results[COLL_STATS] = [s_idx1, s_idx2, s_idx3]

    # 4. Recommendations collection indexes
    recs_coll = db[COLL_RECOMMENDATIONS]
    rec_idx1 = recs_coll.create_index([("source_movie_id", ASCENDING)], name="idx_recs_source_id")
    results[COLL_RECOMMENDATIONS] = [rec_idx1]

    return results
