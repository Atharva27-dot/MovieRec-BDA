import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from src.config import COLL_MOVIES, COLL_RATINGS, COLL_STATS
from src.database import get_collection, MongoDBManager

logger = logging.getLogger("MovieRecBDA.Analytics")

def get_kpi_summary() -> Dict[str, Any]:
    """
    Computes overall KPI summary using MongoDB aggregation.
    Returns:
    {
        "total_movies": 9742,
        "total_ratings": 100836,
        "average_rating": 3.5,
        "total_genres": 20
    }
    """
    try:
        movies_coll = get_collection(COLL_MOVIES)
        ratings_coll = get_collection(COLL_RATINGS)

        total_movies = movies_coll.count_documents({})
        total_ratings = ratings_coll.count_documents({})

        # Aggregation for overall average rating
        avg_pipeline = [
            {"$group": {"_id": None, "overall_avg": {"$avg": "$rating"}}}
        ]
        avg_res = list(ratings_coll.aggregate(avg_pipeline))
        overall_avg = round(avg_res[0]["overall_avg"], 2) if avg_res else 0.0

        # Aggregation for total distinct genres
        genre_pipeline = [
            {"$unwind": "$genres"},
            {"$group": {"_id": "$genres"}},
            {"$count": "total_genres"}
        ]
        genre_res = list(movies_coll.aggregate(genre_pipeline))
        total_genres = genre_res[0]["total_genres"] if genre_res else 0

        return {
            "total_movies": total_movies,
            "total_ratings": total_ratings,
            "average_rating": overall_avg,
            "total_genres": total_genres,
        }
    except Exception as e:
        logger.warning(f"Failed to query MongoDB KPIs, returning fallback data: {e}")
        return {
            "total_movies": 0,
            "total_ratings": 0,
            "average_rating": 0.0,
            "total_genres": 0,
        }

def get_rating_distribution() -> List[Dict[str, Any]]:
    """
    MongoDB Aggregation Pipeline: Count of ratings for each rating value (0.5 to 5.0).
    Pipeline: $group -> $sort
    """
    try:
        ratings_coll = get_collection(COLL_RATINGS)
        pipeline = [
            {
                "$group": {
                    "_id": "$rating",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}},
            {
                "$project": {
                    "rating": "$_id",
                    "count": 1,
                    "_id": 0
                }
            }
        ]
        return list(ratings_coll.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error in get_rating_distribution: {e}")
        return []

def get_most_rated_movies(limit: int = 10) -> List[Dict[str, Any]]:
    """
    MongoDB Aggregation Pipeline: Top N movies with the highest number of ratings.
    Pipeline: $group -> $sort -> $limit -> $lookup (movies) -> $unwind -> $project
    """
    try:
        ratings_coll = get_collection(COLL_RATINGS)
        pipeline = [
            {
                "$group": {
                    "_id": "$movieId",
                    "rating_count": {"$sum": 1},
                    "average_rating": {"$avg": "$rating"}
                }
            },
            {"$sort": {"rating_count": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": COLL_MOVIES,
                    "localField": "_id",
                    "foreignField": "movieId",
                    "as": "movie_info"
                }
            },
            {"$unwind": "$movie_info"},
            {
                "$project": {
                    "movieId": "$_id",
                    "title": "$movie_info.title",
                    "genres": "$movie_info.genres",
                    "rating_count": 1,
                    "average_rating": {"$round": ["$average_rating", 2]},
                    "_id": 0
                }
            }
        ]
        return list(ratings_coll.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error in get_most_rated_movies: {e}")
        return []

def get_highest_rated_movies(min_ratings: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
    """
    MongoDB Aggregation Pipeline: Top N highest rated movies with a minimum rating count filter.
    Pipeline: $group -> $match (rating_count >= min_ratings) -> $sort -> $limit -> $lookup -> $unwind -> $project
    """
    try:
        ratings_coll = get_collection(COLL_RATINGS)
        pipeline = [
            {
                "$group": {
                    "_id": "$movieId",
                    "rating_count": {"$sum": 1},
                    "average_rating": {"$avg": "$rating"}
                }
            },
            {"$match": {"rating_count": {"$gte": min_ratings}}},
            {"$sort": {"average_rating": -1, "rating_count": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": COLL_MOVIES,
                    "localField": "_id",
                    "foreignField": "movieId",
                    "as": "movie_info"
                }
            },
            {"$unwind": "$movie_info"},
            {
                "$project": {
                    "movieId": "$_id",
                    "title": "$movie_info.title",
                    "genres": "$movie_info.genres",
                    "rating_count": 1,
                    "average_rating": {"$round": ["$average_rating", 2]},
                    "_id": 0
                }
            }
        ]
        return list(ratings_coll.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error in get_highest_rated_movies: {e}")
        return []

def get_genre_distribution() -> List[Dict[str, Any]]:
    """
    MongoDB Aggregation Pipeline: Number of movies per genre.
    Pipeline: $unwind (genres) -> $group -> $sort -> $project
    """
    try:
        movies_coll = get_collection(COLL_MOVIES)
        pipeline = [
            {"$unwind": "$genres"},
            {
                "$group": {
                    "_id": "$genres",
                    "movie_count": {"$sum": 1}
                }
            },
            {"$sort": {"movie_count": -1}},
            {
                "$project": {
                    "genre": "$_id",
                    "movie_count": 1,
                    "_id": 0
                }
            }
        ]
        return list(movies_coll.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error in get_genre_distribution: {e}")
        return []

def get_average_rating_by_genre() -> List[Dict[str, Any]]:
    """
    MongoDB Aggregation Pipeline: Average rating by movie genre.
    Pipeline: $unwind (genres) -> $lookup (ratings) -> $unwind (ratings) -> $group (by genre) -> $sort
    """
    try:
        movies_coll = get_collection(COLL_MOVIES)
        pipeline = [
            {"$unwind": "$genres"},
            {
                "$lookup": {
                    "from": COLL_RATINGS,
                    "localField": "movieId",
                    "foreignField": "movieId",
                    "as": "rating_docs"
                }
            },
            {"$unwind": "$rating_docs"},
            {
                "$group": {
                    "_id": "$genres",
                    "average_rating": {"$avg": "$rating_docs.rating"},
                    "total_ratings": {"$sum": 1}
                }
            },
            {"$sort": {"average_rating": -1}},
            {
                "$project": {
                    "genre": "$_id",
                    "average_rating": {"$round": ["$average_rating", 2]},
                    "total_ratings": 1,
                    "_id": 0
                }
            }
        ]
        return list(movies_coll.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error in get_average_rating_by_genre: {e}")
        return []

def get_user_rating_behavior(limit: int = 10) -> List[Dict[str, Any]]:
    """
    MongoDB Aggregation Pipeline: Most active users by rating count.
    Pipeline: $group (by userId) -> $sort -> $limit -> $project
    """
    try:
        ratings_coll = get_collection(COLL_RATINGS)
        pipeline = [
            {
                "$group": {
                    "_id": "$userId",
                    "ratings_given": {"$sum": 1},
                    "avg_user_rating": {"$avg": "$rating"}
                }
            },
            {"$sort": {"ratings_given": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "userId": "$_id",
                    "ratings_given": 1,
                    "avg_user_rating": {"$round": ["$avg_user_rating", 2]},
                    "_id": 0
                }
            }
        ]
        return list(ratings_coll.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error in get_user_rating_behavior: {e}")
        return []
