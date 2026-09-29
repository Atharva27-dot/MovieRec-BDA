# Data Directory

This directory stores raw downloaded MovieLens datasets and preprocessed CSV/JSON files before ingestion into MongoDB Atlas.

Files generated in this directory:
- `ml-latest-small.zip`: Downloaded dataset archive from GroupLens.
- `ml-latest-small/`: Extracted raw files (`movies.csv`, `ratings.csv`, `tags.csv`, `links.csv`).
- `clean_movies.json`: Preprocessed movie document dataset.
- `clean_ratings.json`: Preprocessed ratings document dataset.
