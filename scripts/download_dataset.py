import sys
import zipfile
import urllib.request
import ssl
from pathlib import Path

# Add parent dir to path to allow importing src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR, RAW_DATA_DIR, MOVIELENS_URL

def download_and_extract():
    """
    Downloads GroupLens MovieLens latest small dataset and extracts it to data/ directory.
    Handles SSL context gracefully.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / "ml-latest-small.zip"

    print(f"Downloading dataset from: {MOVIELENS_URL}...")
    try:
        # Create unverified SSL context to prevent SSL Certificate errors on Windows Python
        ssl_context = ssl._create_unverified_context()
        req = urllib.request.Request(MOVIELENS_URL, headers={"User-Agent": "Mozilla/5.0"})

        with urllib.request.urlopen(req, context=ssl_context) as response, open(zip_path, "wb") as out_file:
            out_file.write(response.read())

        print(f"Dataset downloaded successfully to: {zip_path}")

        print("Extracting zip archive...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(DATA_DIR)
        print(f"Extracted dataset to: {RAW_DATA_DIR}")

        # Verify extracted files
        movies_csv = RAW_DATA_DIR / "movies.csv"
        ratings_csv = RAW_DATA_DIR / "ratings.csv"
        if movies_csv.exists() and ratings_csv.exists():
            print("Dataset files verified successfully!")
            print(f"- {movies_csv.name}: {movies_csv.stat().st_size / 1024:.1f} KB")
            print(f"- {ratings_csv.name}: {ratings_csv.stat().st_size / 1024 / 1024:.2f} MB")
        else:
            print("Error: Extracted dataset files are missing.")
            sys.exit(1)

    except Exception as e:
        print(f"Failed to download/extract dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_and_extract()
