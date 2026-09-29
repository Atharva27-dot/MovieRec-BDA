# MovieRec-BDA: Big Data Movie Recommendation System Using MongoDB

> **Big Data Analytics (BDA) Lab Mini-Project**  
> An end-to-end Big Data Analytics and Movie Recommendation platform powered by **MongoDB Atlas Cloud**, **Streamlit**, **PyMongo**, and **NumPy**.

---

## 📌 Project Overview & Problem Statement

Modern movie streaming platforms store millions of user ratings and movie titles. Recommending relevant movies to users from massive collections requires database-level aggregation analytics and efficient recommendation algorithms.

`MovieRec-BDA` is a scalable NoSQL Big Data application that:
- Stores movie metadata and user ratings in **MongoDB Atlas Cloud**.
- Performs database-side analytics using **MongoDB Aggregation Pipelines**.
- Generates real-time movie recommendations using **Multi-Hot Genre Vectorization & Cosine Similarity**.
- Provides an interactive web dashboard built with **Streamlit** and **Plotly**.

---

## 🎯 Key Objectives
1. Model movie and rating datasets using MongoDB NoSQL document design.
2. Ingest, validate, and clean 100,000+ rating records into cloud collections.
3. Build database B-Tree indexes to accelerate search and `$lookup` joins.
4. Execute MongoDB aggregation pipelines (`$group`, `$sort`, `$unwind`, `$lookup`).
5. Develop a content-based recommendation engine with hybrid rating/popularity weighting.
6. Provide an interactive UI for movie exploration, analytics, and NoSQL query demonstration.

---

## 🛠️ Technology Stack
- **Cloud Database:** MongoDB Atlas NoSQL
- **Language:** Python 3.10+
- **Web UI:** Streamlit
- **Analytics & Math:** NumPy, Pandas, PyMongo
- **Visualization:** Plotly Express, Matplotlib
- **Dataset:** GroupLens MovieLens Benchmark (`ml-latest-small`)

---

## 📁 Directory Structure

```
MovieRec-BDA/
│
├── app.py                      # Main Streamlit web application
├── README.md                   # Complete project setup documentation
├── requirements.txt            # Python package dependencies
├── .env.example                # MongoDB Atlas environment variable template
├── .gitignore                  # Git exclusion rules
│
├── data/                       # Downloaded & preprocessed JSON datasets
│   └── README.md
│
├── src/                        # Core Python source modules
│   ├── __init__.py
│   ├── config.py               # Paths, environment variables & validation
│   ├── database.py             # PyMongo client, connection pooling & indexes
│   ├── preprocessing.py        # Data validation, cleaning & deduplication
│   ├── data_loader.py          # MongoDB batch loading & disk cache
│   ├── analytics.py            # MongoDB aggregation pipelines
│   └── recommender.py          # Pure-NumPy multi-hot & cosine recommender
│
├── scripts/                    # Automation scripts
│   ├── download_dataset.py     # Download MovieLens zip dataset
│   ├── prepare_dataset.py      # Clean raw CSVs & create JSON files
│   ├── test_connection.py      # MongoDB Atlas connection ping test
│   ├── create_indexes.py       # Create collection indexes
│   ├── load_to_mongodb.py      # Batch load documents to MongoDB Atlas
│   └── generate_movie_stats.py # Compute rating stats & cache recommendations
│
├── tests/                      # Automated unit test suite
│   ├── test_database.py
│   ├── test_preprocessing.py
│   ├── test_recommender.py
│   └── test_analytics.py
│
├── notebooks/                  # Step-by-step Jupyter Notebook
│   └── MovieRec_BDA_Analysis.ipynb
│
├── docs/                       # Project documentation for college report
│   ├── architecture.md
│   ├── methodology.md
│   ├── mongodb_queries.md
│   ├── viva_questions.md
│   └── demo_flow.md
│
└── screenshots/                # Application UI screenshots
    └── README.md
```

---

## 🌐 Step-by-Step MongoDB Atlas Setup Guide

### Step 1: Create a Free MongoDB Atlas Account
1. Visit [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and register for a free account.
2. Build a Database Cluster (select the free **M0 Sandbox** tier).

### Step 2: Create Database User Credentials
1. Under **Database Access**, click **Add New Database User**.
2. Set Authentication Method to **Password**.
3. Create a username (e.g., `bda_user`) and a secure password.
4. Assign user privileges to **Read and write to any database**.

### Step 3: Configure Network Access
1. Under **Network Access**, click **Add IP Address**.
2. Click **Allow Access from Anywhere** (`0.0.0.0/0`) for local testing.

### Step 4: Obtain Connection String
1. Click **Connect** on your Database Cluster.
2. Choose **Drivers** (Python).
3. Copy your connection string URI:
   ```text
   mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   ```

### Step 5: Configure `.env` File
Create a `.env` file in the root directory:
```env
MONGODB_URI=mongodb+srv://bda_user:YourActualPassword@cluster0.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=movie_recommendation_bda
```

> ⚠️ **IMPORTANT:** Never commit your actual `.env` file to Git!

---

## 🚀 Installation & Data Pipeline Execution

### 1. Clone Project & Install Dependencies
```powershell
cd MovieRec-BDA
pip install -r requirements.txt
```

### 2. Download MovieLens Dataset
```powershell
python scripts/download_dataset.py
```

### 3. Preprocess & Validate Dataset
```powershell
python scripts/prepare_dataset.py
```

### 4. Test MongoDB Cloud Connection
```powershell
python scripts/test_connection.py
```

### 5. Create Collection Indexes
```powershell
python scripts/create_indexes.py
```

### 6. Load Datasets into MongoDB Atlas
```powershell
python scripts/load_to_mongodb.py
```

### 7. Generate Rating Statistics
```powershell
python scripts/generate_movie_stats.py
```

### 8. Run Streamlit Application
```powershell
streamlit run app.py
```

---

## 🧪 Running Unit Tests
Execute the automated unit test suite to verify configuration, data cleaning, and recommender vector math:
```powershell
python -m unittest discover tests
```

---

## 📊 Key MongoDB Aggregation Pipeline Example

```javascript
// Aggregation: Top 10 Most Rated Movies with $lookup join
db.ratings.aggregate([
  { $group: { _id: "$movieId", ratingCount: { $sum: 1 }, avgRating: { $avg: "$rating" } } },
  { $sort: { ratingCount: -1 } },
  { $limit: 10 },
  {
    $lookup: {
      from: "movies",
      localField: "_id",
      foreignField: "movieId",
      as: "movie_info"
    }
  },
  { $unwind: "$movie_info" }
]);
```

---

## ⚠️ Realistic Limitations & Future Scope

### Limitations
- Recommender uses content-based genre vectors rather than collaborative user matrix factorization.
- MongoDB Atlas free tier storage is limited to 512 MB.

### Future Scope
- **Collaborative Filtering:** Implement SVD / User-User matrix factorization using Spark MLlib.
- **Real-Time Streaming:** Ingest live user ratings using Apache Kafka & MongoDB Change Streams.
- **Microservices:** Expose recommendation endpoints via FastAPI microservices.

---

## 👥 Author / Team Placeholder
- **Student Name:** BE Computer Engineering Student
- **Course:** Big Data Analytics (BDA) Lab Mini-Project
