import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import create_indexes, ping_database

def main():
    print("Connecting to MongoDB Atlas to create indexes...")
    success, message, _ = ping_database()
    if not success:
        print(f"Error: {message}")
        print("Please configure MONGODB_URI in your .env file before creating indexes.")
        sys.exit(1)

    print("Creating MongoDB Indexes...")
    index_results = create_indexes()

    print("\n--- Index Creation Summary ---")
    for coll_name, indexes in index_results.items():
        print(f"\nCollection: {coll_name}")
        for idx in indexes:
            print(f"  [+] Created index: {idx}")

    print("\n--- Index Explanations ---")
    print("1. movies.movieId (Unique): Ensures movie ID uniqueness and accelerates O(1) single-movie lookups.")
    print("2. movies.title: Optimizes regex and string search by title in Movie Explorer.")
    print("3. movies.genres: Enables multi-key index lookup when filtering movies by genre.")
    print("4. ratings.movieId: Essential for $lookup joins and rating aggregations grouped by movie.")
    print("5. ratings.userId: Optimizes user rating history lookups and user behavior analytics.")
    print("6. ratings.rating: Accelerates filtering ratings (e.g., ratings >= 4.0).")
    print("7. ratings.(movieId, userId) (Unique): Prevents duplicate rating submissions by the same user for a movie.")
    print("8. movie_stats.movieId (Unique): Fast join target for pre-computed rating metrics.")
    print("9. movie_stats.average_rating & rating_count: Accelerates sorting highest rated and most popular movies.")
    print("10. recommendations.source_movie_id: Fast retrieval of cached movie recommendation pairs.")

if __name__ == "__main__":
    main()
