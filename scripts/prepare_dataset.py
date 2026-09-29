import sys
from pathlib import Path
import pandas as pd

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAW_DATA_DIR
from src.preprocessing import clean_movies, clean_ratings, generate_movie_stats_docs
from src.data_loader import save_clean_data_to_disk

def prepare():
    """
    Loads raw CSVs, performs validation and cleaning, generates statistics documents,
    and saves JSON datasets for ingestion.
    """
    movies_csv = RAW_DATA_DIR / "movies.csv"
    ratings_csv = RAW_DATA_DIR / "ratings.csv"

    if not movies_csv.exists() or not ratings_csv.exists():
        print("Raw dataset files not found. Running download script first...")
        from scripts.download_dataset import download_and_extract
        download_and_extract()

    print("\n--- Cleaning Movies Dataset ---")
    movies_df = pd.read_csv(movies_csv)
    movies_docs, movies_stats = clean_movies(movies_df)
    print(f"Movies Read    : {movies_stats['read']:,}")
    print(f"Movies Valid   : {movies_stats['valid']:,}")
    print(f"Movies Invalid : {movies_stats['invalid']:,}")
    print(f"Duplicates     : {movies_stats['duplicates_skipped']:,}")

    valid_movie_ids = {m["movieId"] for m in movies_docs}

    print("\n--- Cleaning Ratings Dataset ---")
    ratings_df = pd.read_csv(ratings_csv)
    ratings_docs, ratings_stats = clean_ratings(ratings_df, valid_movie_ids=valid_movie_ids)
    print(f"Ratings Read   : {ratings_stats['read']:,}")
    print(f"Ratings Valid  : {ratings_stats['valid']:,}")
    print(f"Ratings Invalid: {ratings_stats['invalid']:,}")
    print(f"Duplicates     : {ratings_stats['duplicates_skipped']:,}")

    print("\n--- Generating Movie Statistics ---")
    stats_docs = generate_movie_stats_docs(ratings_docs)
    print(f"Generated stats for {len(stats_docs):,} movies.")

    print("\n--- Saving Cleaned Datasets to Disk ---")
    save_clean_data_to_disk(movies_docs, ratings_docs, stats_docs)
    print("Dataset preparation complete!")

if __name__ == "__main__":
    prepare()
