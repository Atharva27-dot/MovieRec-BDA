import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "ml-latest-small"
CLEAN_MOVIES_JSON = DATA_DIR / "clean_movies.json"
CLEAN_RATINGS_JSON = DATA_DIR / "clean_ratings.json"
CLEAN_STATS_JSON = DATA_DIR / "clean_movie_stats.json"

# Dataset URL (GroupLens MovieLens Latest Small: ~100k ratings, 9,000 movies)
MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "movie_recommendation_bda")

# Collection Names
COLL_MOVIES = "movies"
COLL_RATINGS = "ratings"
COLL_STATS = "movie_stats"
COLL_RECOMMENDATIONS = "recommendations"

# Batch processing settings
BATCH_SIZE = 5000

def validate_config() -> tuple[bool, str]:
    """
    Validates MongoDB environment configuration.
    Returns (is_valid, message).
    """
    if not MONGODB_URI or MONGODB_URI.strip() == "" or "<username>" in MONGODB_URI:
        return False, "MongoDB connection string is missing or unconfigured. Please set MONGODB_URI in your .env file."
    return True, "Configuration is valid."
