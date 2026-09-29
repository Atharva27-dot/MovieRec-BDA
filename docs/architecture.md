# MovieRec-BDA Architecture Specification

## 1. System Overview
`MovieRec-BDA` is an end-to-end Big Data Analytics and Recommendation platform powered by **MongoDB Atlas Cloud** and **Streamlit**. It demonstrates scalable NoSQL document modeling, bulk data ingestion pipelines, database-level aggregation analytics, and content-based recommendation vectorization.

---

## 2. Architecture Diagram

```
                 +---------------------------------------+
                 |    GroupLens MovieLens Dataset        |
                 | (movies.csv & ratings.csv: 100k+ recs)|
                 +---------------------------------------+
                                     |
                                     v
                 +---------------------------------------+
                 |       Data Ingestion Pipeline         |
                 | (Validation, Deduplication, Cleaning) |
                 +---------------------------------------+
                                     |
                                     v
                 +---------------------------------------+
                 |         MongoDB Atlas Cloud           |
                 |     (Database: movie_recommendation_bda)|
                 |  - movies                             |
                 |  - ratings                            |
                 |  - movie_stats                        |
                 |  - recommendations                    |
                 +---------------------------------------+
                                 /       \
                                /         \
                               v           v
       +----------------------------+  +----------------------------+
       | MongoDB Aggregation Engine |  | Content-Based Recommender  |
       | ($group,$unwind,$lookup)   |  | (Multi-Hot Genre Vectors   |
       |                            |  |  + Cosine Similarity Matrix) |
       +----------------------------+  +----------------------------+
                                \         /
                                 \       /
                                  v     v
                 +---------------------------------------+
                 |       Streamlit Web Application       |
                 |  - Movie Explorer                     |
                 |  - Recommendation Engine              |
                 |  - Interactive Analytics Dashboard    |
                 |  - MongoDB Operations Inspector       |
                 +---------------------------------------+
```

---

## 3. Data Models (JSON/BSON Documents)

### `movies` Collection
```json
{
  "_id": {"$oid": "64f1a2b3c4d5e6f7a8b9c0d1"},
  "movieId": 1,
  "title": "Toy Story (1995)",
  "genres": ["Adventure", "Animation", "Children", "Comedy", "Fantasy"]
}
```

### `ratings` Collection
```json
{
  "_id": {"$oid": "64f1a2b3c4d5e6f7a8b9c0d2"},
  "userId": 1,
  "movieId": 1,
  "rating": 4.0,
  "timestamp": 964982703
}
```

### `movie_stats` Collection
```json
{
  "_id": {"$oid": "64f1a2b3c4d5e6f7a8b9c0d3"},
  "movieId": 1,
  "average_rating": 3.92,
  "rating_count": 215
}
```

### `recommendations` Collection
```json
{
  "_id": {"$oid": "64f1a2b3c4d5e6f7a8b9c0d4"},
  "source_movie_id": 1,
  "recommended_movie_id": 7,
  "similarity_score": 1.0,
  "hybrid_score": 0.85,
  "matching_genres": ["Adventure", "Animation", "Children", "Comedy"]
}
```

---

## 4. Indexing Strategy
To optimize query latency across 100,000+ ratings:
1. `movies.movieId`: Unique B-Tree index for O(1) single-movie lookups.
2. `movies.title`: B-Tree index for fast regex searching.
3. `movies.genres`: Multi-key index for filtering array elements.
4. `ratings.movieId`: Index for `$lookup` joins and movie aggregations.
5. `ratings.userId`: Index for user rating history.
6. `ratings.(movieId, userId)`: Unique compound index to prevent duplicate rating records.
7. `movie_stats.average_rating` & `rating_count`: Indexes for descending leaderboard sorting.
