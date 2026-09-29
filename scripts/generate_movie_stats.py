import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import ping_database, get_collection
from src.config import COLL_RATINGS, COLL_STATS, COLL_RECOMMENDATIONS
from src.data_loader import batch_upsert_movie_stats
from src.recommender import MovieRecommender

def main():
    print("Connecting to MongoDB Atlas...")
    success, message, _ = ping_database()
    if not success:
        print(f"Error: {message}")
        sys.exit(1)

    ratings_coll = get_collection(COLL_RATINGS)
    print("Calculating movie statistics using MongoDB Aggregation Pipeline...")
    pipeline = [
        {
            "$group": {
                "_id": "$movieId",
                "average_rating": {"$avg": "$rating"},
                "rating_count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "movieId": "$_id",
                "average_rating": {"$round": ["$average_rating", 2]},
                "rating_count": 1,
                "_id": 0
            }
        }
    ]

    stats_docs = list(ratings_coll.aggregate(pipeline))
    print(f"Aggregated rating statistics for {len(stats_docs):,} movies.")

    print("Upserting stats into 'movie_stats' collection...")
    batch_upsert_movie_stats(stats_docs)
    print("Movie stats collection updated.")

    print("\nGenerating sample pre-computed recommendations for top movies...")
    recommender = MovieRecommender()
    recommender.fit_from_mongodb()

    if recommender.is_fitted and recommender.combined_df is not None:
        # Get top 20 most popular movies
        top_movies = recommender.combined_df.sort_values(by="rating_count", ascending=False).head(20)
        recs_coll = get_collection(COLL_RECOMMENDATIONS)
        recs_coll.delete_many({})  # Refresh sample recs cache

        sample_recs_count = 0
        for _, m in top_movies.iterrows():
            m_id = int(m["movieId"])
            recs = recommender.get_recommendations(movie_id=m_id, top_n=5)
            for rec in recs:
                recs_coll.insert_one({
                    "source_movie_id": m_id,
                    "recommended_movie_id": rec["movieId"],
                    "similarity_score": rec["similarity_score"],
                    "hybrid_score": rec["hybrid_score"],
                    "matching_genres": rec["matching_genres"],
                })
                sample_recs_count += 1
        print(f"Cached {sample_recs_count} recommendations in 'recommendations' collection.")

if __name__ == "__main__":
    main()
