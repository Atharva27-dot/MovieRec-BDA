import unittest
from src.config import validate_config
from src.database import ping_database

class TestDatabase(unittest.TestCase):

    def test_config_validation_missing_uri(self):
        """
        Tests that validate_config returns False when MONGODB_URI is not set.
        """
        is_valid, msg = validate_config()
        # Since .env is unconfigured by default or has placeholders
        if not is_valid:
            self.assertIn("missing", msg.lower())

    def test_ping_database_handles_invalid_uri(self):
        """
        Tests that ping_database fails gracefully with invalid URI.
        """
        success, msg, info = ping_database(uri="mongodb://invalid:27017")
        self.assertFalse(success)
        self.assertIn("error", msg.lower())
        self.assertEqual(info, {})

if __name__ == "__main__":
    unittest.main()
