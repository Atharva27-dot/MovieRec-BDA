# Big Data Analytics (BDA) Lab Viva Questions & Answers

This document contains 32 essential Viva Voce questions and detailed technical answers covering Big Data concepts, NoSQL, MongoDB Atlas, Aggregation, Recommendation Algorithms, and System Architecture.

---

### Q1: What is Big Data?
**Answer:** Big Data refers to data collections characterized by high Volume, Velocity, Variety, Veracity, and Value (the 5 Vs) that exceed the storage, processing, and management capabilities of traditional relational database management systems (RDBMS).

### Q2: Why is this project classified as a Big Data Analytics project?
**Answer:** The project demonstrates fundamental Big Data concepts including NoSQL document storage, semi-structured data ingestion, database-side aggregation pipelines, indexing strategies, and automated data processing over 100,000+ benchmark rating records.

### Q3: What is NoSQL?
**Answer:** NoSQL ("Not Only SQL") refers to non-relational database management systems designed for horizontal scaling, flexible dynamic schemas, high availability, and rapid handling of semi-structured or unstructured data formats like JSON/BSON.

### Q4: Why use MongoDB instead of a Relational Database like MySQL?
**Answer:**
1. **Flexible Schema:** MongoDB supports embedded arrays (`genres: ["Action", "Comedy"]`) without requiring complex SQL multi-table join tables.
2. **Horizontal Scaling:** Built-in auto-sharding allows dataset distribution across cluster nodes.
3. **Database-Level Aggregation:** Performs analytical aggregations in memory at database nodes.

### Q5: What is a MongoDB Document?
**Answer:** A document is a basic unit of data in MongoDB, represented as a BSON (Binary JSON) object containing key-value pairs, arrays, and sub-documents.

### Q6: What is a MongoDB Collection?
**Answer:** A collection is a grouping of MongoDB documents, analogous to a table in a relational database, but without enforcing a rigid pre-defined schema.

### Q7: What is BSON?
**Answer:** BSON (Binary JSON) is the binary-encoded serialization format used by MongoDB to store documents. It extends JSON by adding support for data types such as Date, ObjectId, 32/64-bit integers, and Binary Data.

### Q8: What is MongoDB Atlas?
**Answer:** MongoDB Atlas is a fully managed cloud database platform that automates database deployment, cluster scaling, automated backups, network security, and global region distribution.

### Q9: What is the MovieLens dataset?
**Answer:** MovieLens is a standard benchmark dataset created by the GroupLens research group at the University of Minnesota. It contains real user ratings, movie titles, release years, and genre tags.

### Q10: What MongoDB collections are used in this system?
**Answer:**
1. `movies`: Stores `movieId`, `title`, and `genres` list.
2. `ratings`: Stores `userId`, `movieId`, `rating`, and `timestamp`.
3. `movie_stats`: Stores precomputed `average_rating` and `rating_count`.
4. `recommendations`: Stores cached recommendation pairs and similarity scores.

### Q11: What is a MongoDB Aggregation Pipeline?
**Answer:** An aggregation pipeline is a framework for data processing composed of sequential stages (e.g., `$match`, `$group`, `$sort`, `$limit`, `$lookup`, `$unwind`). Documents pass through stages where transformations and aggregations occur on the server.

### Q12: What does the `$unwind` stage do?
**Answer:** `$unwind` deconstructs an array field from input documents to output a document for *each* element of the array. For example, unwinding `genres: ["Action", "Comedy"]` produces two separate document iterations.

### Q13: What does the `$lookup` stage do?
**Answer:** `$lookup` performs an equality left-outer join between documents from another collection in the same database, bringing matching attributes into an array field.

### Q14: What is the purpose of Database Indexing?
**Answer:** Indexes are specialized B-Tree data structures that store a small portion of the collection's data in an easily traversable form. They prevent full collection scans (`COLLSCAN`), reducing search query complexity from $O(N)$ to $O(\log N)$.

### Q15: What indexes were created in this project?
**Answer:**
- `movies.movieId` (Unique)
- `movies.title` & `movies.genres`
- `ratings.movieId` & `ratings.userId`
- `ratings.(movieId, userId)` (Unique compound)
- `movie_stats.average_rating` & `rating_count`

### Q16: How are duplicate records prevented during ingestion?
**Answer:** Ingestion uses PyMongo `bulk_write` with `UpdateOne(filter, update, upsert=True)` based on unique keys (`movieId` for movies, `(userId, movieId)` for ratings).

### Q17: Why use Batch Ingestion instead of single inserts?
**Answer:** Single inserts incur network round-trip overhead for every document. Batching 5,000 documents per `bulk_write` operation reduces network overhead by 99.9% and dramatically accelerates loading.

### Q18: What is Content-Based Recommendation?
**Answer:** Content-based recommendation recommends items similar to those the user liked in the past, based on item attributes (e.g., movie genres, director, keywords).

### Q19: What is Multi-Hot Encoding?
**Answer:** Multi-hot encoding converts categorical lists (like movie genres) into binary feature vectors of length $G$ (total genres), where `1` indicates presence of a genre and `0` indicates absence.

### Q20: What is Cosine Similarity?
**Answer:** Cosine similarity measures the cosine of the angle between two non-zero vectors in an inner product space:
$$\text{Similarity}(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$$
It yields a value between `0` (completely orthogonal/dissimilar) and `1` (identical orientation).

### Q21: What is the Hybrid Recommendation Enhancement in this project?
**Answer:** It combines raw genre cosine similarity (70%) with normalized average rating quality (20%) and logarithmic rating count popularity (10%) to prevent obscure movies with few ratings from dominating top recommendations.

### Q22: Why exclude the target movie from its own recommendations?
**Answer:** A movie is 100% identical to itself ($\text{similarity} = 1.0$). Recommending the selected movie to the user provides zero discovery value.

### Q23: What is Streamlit?
**Answer:** Streamlit is an open-source Python framework that allows developers to turn Python scripts into interactive web applications without requiring front-end HTML/CSS/JS code.

### Q24: How is Streamlit caching utilized?
**Answer:** `@st.cache_resource` and `@st.cache_data` cache database connections and heavy recommendation matrix computations so dropdown changes render instantly without recalculating matrices.

### Q25: Where is data validation performed?
**Answer:** Data validation occurs during the preprocessing phase in `src/preprocessing.py` before inserting documents into MongoDB Atlas.

### Q26: What validation checks are enforced?
**Answer:** Check for missing/null IDs, valid title text, ratings within range $[0.5, 5.0]$, valid timestamp format, and removal of duplicate pairs.

### Q27: How does the system handle MongoDB network failures?
**Answer:** The system catches PyMongo `ConnectionFailure` and `ServerSelectionTimeoutError` exceptions with 5-second timeouts and falls back gracefully to preprocessed local JSON files.

### Q28: How are MongoDB Atlas credentials secured?
**Answer:** Credentials are stored in environment variables inside `.env`, which is ignored by Git via `.gitignore`. `.env.example` provides placeholders for users.

### Q29: What is the difference between SQL JOIN and MongoDB `$lookup`?
**Answer:** SQL JOINs are executed dynamically across tables at query runtime, whereas MongoDB `$lookup` brings joined documents into an array inside an aggregation pipeline, often combined with `$unwind`.

### Q30: What are the main limitations of this system?
**Answer:**
1. Recommendations rely primarily on genre metadata.
2. User-collaborative filtering (user matrix factorization) is not the primary algorithm.
3. MongoDB Atlas free tier has storage (512MB) limits.

### Q31: How can this system be scaled for production?
**Answer:**
1. Deploy MongoDB Atlas Auto-Scaling Cluster with Sharding across `movieId`.
2. Implement Apache Spark or Ray for distributed similarity matrix computation.
3. Add real-time Redis caching for recommendation responses.

### Q32: Why did you not use Hadoop or MapReduce for this project?
**Answer:** Modern Big Data architectures favor document database aggregations and cloud NoSQL platforms like MongoDB Atlas over heavy legacy Hadoop MapReduce clusters for interactive real-time applications.
