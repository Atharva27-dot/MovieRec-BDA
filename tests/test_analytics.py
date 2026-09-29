import unittest
from src.analytics import get_kpi_summary

class TestAnalytics(unittest.TestCase):

    def test_kpi_summary_keys(self):
        """
        Tests that get_kpi_summary returns a valid dict structure even when offline/mocked.
        """
        kpis = get_kpi_summary()
        self.assertIn("total_movies", kpis)
        self.assertIn("total_ratings", kpis)
        self.assertIn("average_rating", kpis)
        self.assertIn("total_genres", kpis)

if __name__ == "__main__":
    unittest.main()
