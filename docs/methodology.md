# Methodology & Implementation Pipeline

## 1. Pipeline Overview
The implementation follows an 8-phase Big Data processing pipeline:

```
Dataset Download ──► Data Preprocessing ──► Validation & Deduplication
                                                  │
                                                  ▼
Visualization ◄── Recommendation Engine ◄── MongoDB Aggregation & Indexing
```

---

## 2. Step-by-Step Methodology

### Step 1: Data Ingestion & Validation
- **Source:** GroupLens MovieLens Benchmark Dataset (`ml-latest-small`).
- **Validation Rules:**
  - `movieId` & `userId` must be positive integers > 0.
  - `rating` must be between `0.5` and `5.0`.
  - Missing titles or null fields are filtered out and logged.
  - Duplicate `(userId, movieId)` rating pairs are eliminated.

### Step 2: MongoDB Atlas Storage & Bulk Loading
- PyMongo `bulk_write` with `UpdateOne(..., upsert=True)` is used in batch sizes of 5,000 records.
- Batch upserts guarantee idempotency and prevent duplicate key errors during script re-runs.

### Step 3: MongoDB Indexing
- B-Tree single and compound indexes are created using `scripts/create_indexes.py` to accelerate `$lookup` operations between `movies` and `ratings`.

### Step 4: MongoDB Aggregation Analytics
- Database-level analytics are executed using native aggregation pipelines:
  - `$unwind` for array processing of movie genres.
  - `$group` for computing counts and averages.
  - `$lookup` for performing SQL-like JOINs between collections.
  - `$sort` and `$limit` for ranking top movies.

### Step 5: Content-Based Recommendation Vectorization
- Movie genres are transformed into a **Multi-Hot Encoded Feature Matrix** $M \in \mathbb{R}^{N \times G}$ where $N$ is the number of movies and $G$ is the number of unique genres.
- Normalized genre matrix $N = \frac{M}{\|M\|_2}$.
- **Cosine Similarity Matrix** $S = N \cdot N^T$ computes genre similarity $S_{i,j} \in [0, 1]$ between all pairs of movies.

### Step 6: Hybrid Ranking Score
- The recommendation score combines content similarity with popularity and quality:
  $$\text{Score}(i, j) = 0.70 \times S_{i,j} + 0.20 \times \left(\frac{\text{Rating}_j}{5.0}\right) + 0.10 \times \min\left(\frac{\log(1 + \text{Count}_j)}{\log(1 + 300)}, 1.0\right)$$
- This prevents obscure single-rated movies from dominating top recommendations.
