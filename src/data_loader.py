import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from pymongo import UpdateOne
from pymongo.errors import PyMongoError

from src.config import (
    CLEAN_MOVIES_JSON,
    CLEAN_RATINGS_JSON,
    CLEAN_STATS_JSON,
    COLL_MOVIES,
    COLL_RATINGS,
    COLL_STATS,
    COLL_RECOMMENDATIONS,
    BATCH_SIZE,
)
from src.database import get_collection, MongoDBManager

logger = logging.getLogger("MovieRecBDA.DataLoader")

def save_clean_data_to_disk(movies: List[Dict[str, Any]], ratings: List[Dict[str, Any]], stats: List[Dict[str, Any]]):
    """
    Saves cleaned datasets to local JSON files for offline testing and fast re-ingestion.
    """
    CLEAN_MOVIES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(CLEAN_MOVIES_JSON, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2)

    with open(CLEAN_RATINGS_JSON, "w", encoding="utf-8") as f:
        json.dump(ratings, f, indent=2)

    with open(CLEAN_STATS_JSON, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    logger.info("Saved cleaned datasets to data/ directory.")

def load_clean_data_from_disk() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Loads preprocessed datasets from local JSON files.
    """
    if not CLEAN_MOVIES_JSON.exists() or not CLEAN_RATINGS_JSON.exists():
        raise FileNotFoundError("Clean dataset files not found. Run prepare_dataset.py first.")

    with open(CLEAN_MOVIES_JSON, "r", encoding="utf-8") as f:
        movies = json.load(f)

    with open(CLEAN_RATINGS_JSON, "r", encoding="utf-8") as f:
        ratings = json.load(f)

    stats = []
    if CLEAN_STATS_JSON.exists():
        with open(CLEAN_STATS_JSON, "r", encoding="utf-8") as f:
            stats = json.load(f)

    return movies, ratings, stats

def batch_upsert_movies(movies: List[Dict[str, Any]], batch_size: int = BATCH_SIZE) -> int:
    """
    Upserts movies into MongoDB collection in batches using UpdateOne bulk operations.
    """
    coll = get_collection(COLL_MOVIES)
    total_upserted = 0

    operations = [
        UpdateOne({"movieId": m["movieId"]}, {"$set": m}, upsert=True)
        for m in movies
    ]

    for i in range(0, len(operations), batch_size):
        chunk = operations[i : i + batch_size]
        res = coll.bulk_write(chunk, ordered=False)
        total_upserted += (res.upserted_count + res.modified_count + res.matched_count)
        logger.info(f"Movies batch {i // batch_size + 1}: processed {len(chunk)} records.")

    return total_upserted

def batch_upsert_ratings(ratings: List[Dict[str, Any]], batch_size: int = BATCH_SIZE) -> int:
    """
    Upserts ratings into MongoDB collection in batches.
    """
    coll = get_collection(COLL_RATINGS)
    total_upserted = 0

    operations = [
        UpdateOne(
            {"userId": r["userId"], "movieId": r["movieId"]},
            {"$set": r},
            upsert=True
        )
        for r in ratings
    ]

    for i in range(0, len(operations), batch_size):
        chunk = operations[i : i + batch_size]
        res = coll.bulk_write(chunk, ordered=False)
        total_upserted += (res.upserted_count + res.modified_count + res.matched_count)
        logger.info(f"Ratings batch {i // batch_size + 1}: processed {len(chunk)} records.")

    return total_upserted

def batch_upsert_movie_stats(stats: List[Dict[str, Any]], batch_size: int = BATCH_SIZE) -> int:
    """
    Upserts movie_stats into MongoDB collection.
    """
    coll = get_collection(COLL_STATS)
    total_upserted = 0

    operations = [
        UpdateOne({"movieId": s["movieId"]}, {"$set": s}, upsert=True)
        for s in stats
    ]

    for i in range(0, len(operations), batch_size):
        chunk = operations[i : i + batch_size]
        res = coll.bulk_write(chunk, ordered=False)
        total_upserted += (res.upserted_count + res.modified_count + res.matched_count)
        logger.info(f"Movie Stats batch {i // batch_size + 1}: processed {len(chunk)} records.")

    return total_upserted
