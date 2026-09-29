import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import ping_database

def test_conn():
    """
    Tests MongoDB Atlas connection string.
    """
    print("Testing MongoDB Atlas Connection...")
    success, message, info = ping_database()
    if success:
        print("\n==========================================")
        print("SUCCESS: " + message)
        print(f"Target Database : {info.get('database_name')}")
        print(f"MongoDB Version : {info.get('version')}")
        print("==========================================\n")
        sys.exit(0)
    else:
        print("\n==========================================")
        print("FAILURE: " + message)
        print("==========================================\n")
        sys.exit(1)

if __name__ == "__main__":
    test_conn()
