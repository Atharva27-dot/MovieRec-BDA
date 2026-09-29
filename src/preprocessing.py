import logging
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("MovieRecBDA.Preprocessing")

def clean_movies(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Validates and cleans movies DataFrame.
    Returns (cleaned_movie_documents, statistics_summary).
    """
    total_read = len(df)
    invalid_count = 0
    duplicate_count = 0

    valid_movies: List[Dict[str, Any]] = []
    seen_ids = set()

    for _, row in df.iterrows():
        try:
            # 1. Validate movieId
            raw_id = row.get("movieId")
            if pd.isna(raw_id):
                invalid_count += 1
                continue
            movie_id = int(raw_id)
            if movie_id <= 0:
                invalid_count += 1
                continue

            # 2. Check duplicates
            if movie_id in seen_ids:
                duplicate_count += 1
                continue

            # 3. Validate title
            raw_title = str(row.get("title", "")).strip()
            if not raw_title or raw_title.lower() == "nan":
                invalid_count += 1
                continue

            # 4. Parse genres
            raw_genres = str(row.get("genres", "")).strip()
            if raw_genres and raw_genres != "(no genres listed)":
                genres_list = [g.strip() for g in raw_genres.split("|") if g.strip()]
            else:
                genres_list = []

            movie_doc = {
                "movieId": movie_id,
                "title": raw_title,
                "genres": genres_list
            }
            valid_movies.append(movie_doc)
            seen_ids.add(movie_id)

        except (ValueError, TypeError) as e:
            logger.debug(f"Row parsing failed: {e}")
            invalid_count += 1

    stats = {
        "read": total_read,
        "valid": len(valid_movies),
        "invalid": invalid_count,
        "duplicates_skipped": duplicate_count,
    }
    logger.info(f"Movie cleaning summary: {stats}")
    return valid_movies, stats

def clean_ratings(df: pd.DataFrame, valid_movie_ids: Optional[set] = None) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Validates and cleans ratings DataFrame.
    Returns (cleaned_rating_documents, statistics_summary).
    """
    total_read = len(df)
    invalid_count = 0
    duplicate_count = 0

    valid_ratings: List[Dict[str, Any]] = []
    seen_user_movie_pairs = set()

    for _, row in df.iterrows():
        try:
            # 1. Validate userId & movieId
            user_id = int(row["userId"])
            movie_id = int(row["movieId"])

            if user_id <= 0 or movie_id <= 0:
                invalid_count += 1
                continue

            if valid_movie_ids is not None and movie_id not in valid_movie_ids:
                invalid_count += 1
                continue

            # 2. Check duplicate (userId, movieId)
            pair = (user_id, movie_id)
            if pair in seen_user_movie_pairs:
                duplicate_count += 1
                continue

            # 3. Validate rating range (0.5 to 5.0)
            rating = float(row["rating"])
            if rating < 0.5 or rating > 5.0 or np.isnan(rating):
                invalid_count += 1
                continue

            # 4. Validate timestamp
            timestamp = int(row.get("timestamp", 0))

            rating_doc = {
                "userId": user_id,
                "movieId": movie_id,
                "rating": rating,
                "timestamp": timestamp
            }
            valid_ratings.append(rating_doc)
            seen_user_movie_pairs.add(pair)

        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"Rating row invalid: {e}")
            invalid_count += 1

    stats = {
        "read": total_read,
        "valid": len(valid_ratings),
        "invalid": invalid_count,
        "duplicates_skipped": duplicate_count,
    }
    logger.info(f"Ratings cleaning summary: {stats}")
    return valid_ratings, stats

def generate_movie_stats_docs(ratings_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates pre-aggregated movie_stats objects from rating documents:
    [{"movieId": 1, "average_rating": 4.17, "rating_count": 215}, ...]
    """
    if not ratings_docs:
        return []

    df = pd.DataFrame(ratings_docs)
    grouped = df.groupby("movieId").agg(
        average_rating=("rating", "mean"),
        rating_count=("rating", "count")
    ).reset_index()

    grouped["average_rating"] = grouped["average_rating"].round(2)
    stats_docs = grouped.to_dict(orient="records")
    return stats_docs
