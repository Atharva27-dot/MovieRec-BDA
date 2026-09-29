import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from src.config import COLL_MOVIES, COLL_STATS
from src.database import get_collection

logger = logging.getLogger("MovieRecBDA.Recommender")

class MovieRecommender:
    """
    Content-Based & Hybrid Movie Recommendation Engine.
    Uses Pure-NumPy Multi-Hot Encoding of movie genres and Cosine Similarity,
    enhanced with rating quality and popularity metrics.
    Completely self-contained without DLL dependencies.
    """

    def __init__(self):
        self.movies_df: Optional[pd.DataFrame] = None
        self.stats_df: Optional[pd.DataFrame] = None
        self.combined_df: Optional[pd.DataFrame] = None
        self.similarity_matrix: Optional[np.ndarray] = None
        self.movie_id_to_idx: Dict[int, int] = {}
        self.all_genres: List[str] = []
        self.is_fitted: bool = False

    def fit_from_data(self, movies_data: List[Dict[str, Any]], stats_data: Optional[List[Dict[str, Any]]] = None):
        """
        Fits the recommendation model from in-memory movie and stats documents.
        """
        if not movies_data:
            logger.warning("No movie data provided to fit recommender.")
            return

        self.movies_df = pd.DataFrame(movies_data)

        if stats_data:
            self.stats_df = pd.DataFrame(stats_data)
        else:
            self.stats_df = pd.DataFrame(columns=["movieId", "average_rating", "rating_count"])

        # Merge movies and stats
        if not self.stats_df.empty:
            merged = pd.merge(self.movies_df, self.stats_df, on="movieId", how="left")
        else:
            merged = self.movies_df.copy()
            merged["average_rating"] = 0.0
            merged["rating_count"] = 0

        merged["average_rating"] = merged["average_rating"].fillna(0.0)
        merged["rating_count"] = merged["rating_count"].fillna(0)

        self.combined_df = merged.reset_index(drop=True)
        self.movie_id_to_idx = {row["movieId"]: idx for idx, row in self.combined_df.iterrows()}

        # 1. Extract set of all unique genres across all movies
        genre_set = set()
        for g_list in self.combined_df["genres"]:
            if isinstance(g_list, list):
                genre_set.update(g_list)
        self.all_genres = sorted(list(genre_set))
        genre_to_col = {g: i for i, g in enumerate(self.all_genres)}

        num_movies = len(self.combined_df)
        num_genres = len(self.all_genres)

        # 2. Build multi-hot feature matrix (num_movies x num_genres)
        multi_hot = np.zeros((num_movies, num_genres), dtype=np.float32)

        for idx, g_list in enumerate(self.combined_df["genres"]):
            if isinstance(g_list, list):
                for g in g_list:
                    if g in genre_to_col:
                        multi_hot[idx, genre_to_col[g]] = 1.0

        # 3. Compute row norms for cosine similarity
        norms = np.linalg.norm(multi_hot, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-9)  # Avoid division by zero
        normalized_matrix = multi_hot / norms

        # 4. Compute cosine similarity via dot product: S = N . N^T
        self.similarity_matrix = np.dot(normalized_matrix, normalized_matrix.T)
        self.is_fitted = True
        logger.info(f"Fitted MovieRecommender on {num_movies} movies and {num_genres} distinct genres.")

    def fit_from_mongodb(self):
        """
        Fetches movies and movie_stats directly from MongoDB Atlas and fits the model.
        """
        try:
            movies_coll = get_collection(COLL_MOVIES)
            stats_coll = get_collection(COLL_STATS)

            movies_docs = list(movies_coll.find({}, {"_id": 0, "movieId": 1, "title": 1, "genres": 1}))
            stats_docs = list(stats_coll.find({}, {"_id": 0, "movieId": 1, "average_rating": 1, "rating_count": 1}))

            self.fit_from_data(movies_docs, stats_docs)
        except Exception as e:
            logger.error(f"Failed to fit recommender from MongoDB: {e}")
            self.is_fitted = False

    def get_recommendations(
        self,
        movie_id: int,
        top_n: int = 10,
        use_hybrid: bool = True,
        min_rating_count: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Generates top-N recommendations for a given movie ID.
        """
        if not self.is_fitted or self.combined_df is None or self.similarity_matrix is None:
            raise ValueError("Recommender model is not fitted. Call fit_from_data() or fit_from_mongodb() first.")

        if movie_id not in self.movie_id_to_idx:
            logger.warning(f"Movie ID {movie_id} not found in model vocabulary.")
            return []

        target_idx = self.movie_id_to_idx[movie_id]
        target_row = self.combined_df.iloc[target_idx]
        target_genres = set(target_row["genres"]) if isinstance(target_row["genres"], list) else set()

        sim_scores = self.similarity_matrix[target_idx]

        results = []
        for idx, sim in enumerate(sim_scores):
            # Exclude the target movie itself
            if idx == target_idx:
                continue

            cand_row = self.combined_df.iloc[idx]
            cand_genres = set(cand_row["genres"]) if isinstance(cand_row["genres"], list) else set()

            rating_cnt = int(cand_row["rating_count"])
            if rating_cnt < min_rating_count:
                continue

            avg_rating = float(cand_row["average_rating"])
            matching_g = sorted(list(target_genres.intersection(cand_genres)))

            # Hybrid Score calculation:
            # 70% genre similarity, 20% rating quality (out of 5), 10% log-scaled rating count popularity
            if use_hybrid:
                norm_rating = avg_rating / 5.0
                norm_pop = min(np.log1p(rating_cnt) / np.log1p(300), 1.0)
                final_score = (0.7 * sim) + (0.2 * norm_rating) + (0.1 * norm_pop)
            else:
                final_score = sim

            # Filter out movies with zero genre similarity unless requested
            if sim <= 0 and use_hybrid:
                continue

            explanation = (
                f"Shares {len(matching_g)} genre(s): [{', '.join(matching_g)}]. "
                f"Genre similarity: {sim:.2f}, Avg Rating: {avg_rating:.1f} ({rating_cnt:,} ratings)."
            )

            results.append({
                "movieId": int(cand_row["movieId"]),
                "title": cand_row["title"],
                "genres": cand_row["genres"],
                "similarity_score": round(float(sim), 4),
                "hybrid_score": round(float(final_score), 4),
                "average_rating": round(avg_rating, 2),
                "rating_count": rating_cnt,
                "matching_genres": matching_g,
                "explanation": explanation
            })

        # Sort by hybrid score (or similarity score) descending
        results = sorted(results, key=lambda x: x["hybrid_score"], reverse=True)[:top_n]

        for rank, rec in enumerate(results, start=1):
            rec["rank"] = rank

        return results

# Global singleton recommender instance
_global_recommender = MovieRecommender()

def get_recommendations_api(movie_id: int, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience module-level API function.
    """
    if not _global_recommender.is_fitted:
        _global_recommender.fit_from_mongodb()
    return _global_recommender.get_recommendations(movie_id=movie_id, top_n=top_n)
