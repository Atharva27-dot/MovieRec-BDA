import unittest
import pandas as pd
from src.preprocessing import clean_movies, clean_ratings, generate_movie_stats_docs

class TestPreprocessing(unittest.TestCase):

    def test_clean_movies(self):
        """
        Tests movie validation, genre parsing, and duplicate elimination.
        """
        raw_data = pd.DataFrame([
            {"movieId": 1, "title": "Toy Story (1995)", "genres": "Adventure|Animation|Children"},
            {"movieId": 2, "title": "Jumanji (1995)", "genres": "Adventure|Children|Fantasy"},
            {"movieId": 1, "title": "Toy Story Duplicate", "genres": "Animation"},  # Duplicate ID
            {"movieId": -5, "title": "Invalid ID", "genres": "Action"},             # Invalid ID
            {"movieId": 3, "title": "", "genres": "Drama"},                          # Missing Title
        ])

        docs, stats = clean_movies(raw_data)

        self.assertEqual(len(docs), 2)
        self.assertEqual(stats["read"], 5)
        self.assertEqual(stats["valid"], 2)
        self.assertEqual(stats["invalid"], 2)
        self.assertEqual(stats["duplicates_skipped"], 1)

        # Check document structure
        self.assertEqual(docs[0]["movieId"], 1)
        self.assertEqual(docs[0]["title"], "Toy Story (1995)")
        self.assertEqual(docs[0]["genres"], ["Adventure", "Animation", "Children"])

    def test_clean_ratings(self):
        """
        Tests rating bounds validation (0.5 to 5.0), missing fields, and duplicate user-movie pairs.
        """
        raw_ratings = pd.DataFrame([
            {"userId": 1, "movieId": 1, "rating": 4.0, "timestamp": 964982703},
            {"userId": 1, "movieId": 2, "rating": 5.0, "timestamp": 964982704},
            {"userId": 1, "movieId": 1, "rating": 3.0, "timestamp": 964982705}, # Duplicate (1, 1)
            {"userId": 2, "movieId": 1, "rating": 7.0, "timestamp": 964982706}, # Out-of-bounds rating > 5.0
            {"userId": 3, "movieId": 1, "rating": -1.0, "timestamp": 964982707},# Out-of-bounds rating < 0.5
        ])

        docs, stats = clean_ratings(raw_ratings)

        self.assertEqual(len(docs), 2)
        self.assertEqual(stats["read"], 5)
        self.assertEqual(stats["valid"], 2)
        self.assertEqual(stats["duplicates_skipped"], 1)
        self.assertEqual(stats["invalid"], 2)

    def test_generate_movie_stats_docs(self):
        """
        Tests movie stats aggregation logic.
        """
        ratings_docs = [
            {"userId": 1, "movieId": 1, "rating": 4.0, "timestamp": 100},
            {"userId": 2, "movieId": 1, "rating": 5.0, "timestamp": 101},
            {"userId": 1, "movieId": 2, "rating": 3.0, "timestamp": 102},
        ]

        stats_docs = generate_movie_stats_docs(ratings_docs)
        self.assertEqual(len(stats_docs), 2)

        movie_1_stat = next(s for s in stats_docs if s["movieId"] == 1)
        self.assertEqual(movie_1_stat["average_rating"], 4.5)
        self.assertEqual(movie_1_stat["rating_count"], 2)

if __name__ == "__main__":
    unittest.main()
