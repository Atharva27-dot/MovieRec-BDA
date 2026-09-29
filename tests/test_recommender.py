import unittest
from src.recommender import MovieRecommender

class TestMovieRecommender(unittest.TestCase):

    def setUp(self):
        """
        Set up a small sample movie dataset for testing recommender functionality.
        """
        self.sample_movies = [
            {"movieId": 1, "title": "Toy Story (1995)", "genres": ["Adventure", "Animation", "Children", "Comedy"]},
            {"movieId": 2, "title": "Jumanji (1995)", "genres": ["Adventure", "Children", "Fantasy"]},
            {"movieId": 3, "title": "Grumpier Old Men (1995)", "genres": ["Comedy", "Romance"]},
            {"movieId": 4, "title": "Waiting to Exhale (1995)", "genres": ["Comedy", "Drama", "Romance"]},
            {"movieId": 5, "title": "Father of the Bride Part II (1995)", "genres": ["Comedy"]},
            {"movieId": 6, "title": "Heat (1995)", "genres": ["Action", "Crime", "Thriller"]},
            {"movieId": 7, "title": "Bug's Life, A (1998)", "genres": ["Adventure", "Animation", "Children", "Comedy"]},
        ]

        self.sample_stats = [
            {"movieId": 1, "average_rating": 3.92, "rating_count": 215},
            {"movieId": 2, "average_rating": 3.43, "rating_count": 110},
            {"movieId": 3, "average_rating": 3.26, "rating_count": 52},
            {"movieId": 4, "average_rating": 2.36, "rating_count": 7},
            {"movieId": 5, "average_rating": 3.07, "rating_count": 49},
            {"movieId": 6, "average_rating": 3.94, "rating_count": 126},
            {"movieId": 7, "average_rating": 3.51, "rating_count": 92},
        ]

        self.recommender = MovieRecommender()
        self.recommender.fit_from_data(self.sample_movies, self.sample_stats)

    def test_recommender_is_fitted(self):
        self.assertTrue(self.recommender.is_fitted)
        self.assertEqual(len(self.recommender.combined_df), 7)

    def test_recommendation_output_format(self):
        """
        Tests that recommendations for Toy Story (ID: 1) contain Bug's Life (ID: 7) at the top,
        and verify all required dict fields are present.
        """
        recs = self.recommender.get_recommendations(movie_id=1, top_n=3)

        self.assertGreater(len(recs), 0)
        self.assertLessEqual(len(recs), 3)

        top_rec = recs[0]
        # Required fields check
        required_keys = [
            "rank", "movieId", "title", "genres", "similarity_score",
            "hybrid_score", "average_rating", "rating_count", "matching_genres", "explanation"
        ]
        for key in required_keys:
            self.assertIn(key, top_rec)

        # Exclude self check: Toy Story (ID: 1) must not be in recommendations
        rec_ids = [r["movieId"] for r in recs]
        self.assertNotIn(1, rec_ids)

        # A Bug's Life shares identical 4 genres with Toy Story, so it should be #1 recommendation
        self.assertEqual(top_rec["movieId"], 7)

    def test_unknown_movie_id(self):
        """
        Tests that requesting recommendations for a non-existent movie ID returns an empty list.
        """
        recs = self.recommender.get_recommendations(movie_id=99999, top_n=5)
        self.assertEqual(recs, [])

if __name__ == "__main__":
    unittest.main()
