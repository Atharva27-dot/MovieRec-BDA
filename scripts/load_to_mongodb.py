import sys
import time
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import ping_database
from src.data_loader import (
    load_clean_data_from_disk,
    batch_upsert_movies,
    batch_upsert_ratings,
    batch_upsert_movie_stats,
)

def main():
    print("Connecting to MongoDB Atlas...")
    success, message, info = ping_database()
    if not success:
        print(f"Error: {message}")
        print("Please configure MONGODB_URI in your .env file before ingesting data.")
        sys.exit(1)

    print(f"Connected to database: {info.get('database_name')}")

    print("\nReading preprocessed datasets from disk...")
    try:
        movies, ratings, stats = load_clean_data_from_disk()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run 'python scripts/prepare_dataset.py' first.")
        sys.exit(1)

    print(f"Loaded from disk: {len(movies):,} movies, {len(ratings):,} ratings, {len(stats):,} movie stats.")

    start_time = time.time()

    # 1. Ingest Movies
    print("\n--- Ingesting Movies Collection ---")
    m_count = batch_upsert_movies(movies)
    print(f"Movies Ingestion Complete: {m_count:,} documents processed.")

    # 2. Ingest Ratings
    print("\n--- Ingesting Ratings Collection ---")
    r_count = batch_upsert_ratings(ratings)
    print(f"Ratings Ingestion Complete: {r_count:,} documents processed.")

    # 3. Ingest Movie Stats
    print("\n--- Ingesting Movie Stats Collection ---")
    s_count = batch_upsert_movie_stats(stats)
    print(f"Movie Stats Ingestion Complete: {s_count:,} documents processed.")

    elapsed = time.time() - start_time
    print(f"\nData Ingestion Pipeline Finished in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
