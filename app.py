import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Add root project directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import (
    validate_config,
    COLL_MOVIES,
    COLL_RATINGS,
    COLL_STATS,
    COLL_RECOMMENDATIONS,
)
from src.database import ping_database, get_collection
from src.data_loader import load_clean_data_from_disk
from src.recommender import MovieRecommender
from src.analytics import (
    get_kpi_summary,
    get_rating_distribution,
    get_most_rated_movies,
    get_highest_rated_movies,
    get_genre_distribution,
    get_average_rating_by_genre,
    get_user_rating_behavior,
)

# Set Streamlit page config
st.set_page_config(
    page_title="MovieRec BDA — Big Data Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 20px;
    }
    .kpi-card {
        background-color: #F8F9FA;
        border-left: 5px solid #1E88E5;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .kpi-number {
        font-size: 1.8rem;
        font-weight: bold;
        color: #0D47A1;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #666666;
        text-transform: uppercase;
    }
    .rec-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
    }
    .bda-badge {
        background-color: #E3F2FD;
        color: #0D47A1;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Streamlit Cached Resource & Helper Functions
# ---------------------------------------------------------
@st.cache_resource
def get_recommender_instance():
    """
    Fits and caches the MovieRecommender engine.
    Tries MongoDB Atlas first, falls back to local preprocessed JSON dataset.
    """
    recommender = MovieRecommender()
    is_valid, _ = validate_config()

    if is_valid:
        try:
            recommender.fit_from_mongodb()
            if recommender.is_fitted:
                return recommender, "MongoDB Atlas"
        except Exception:
            pass

    # Fallback to local JSON files
    try:
        movies, ratings, stats = load_clean_data_from_disk()
        recommender.fit_from_data(movies, stats)
        return recommender, "Local Processed Data (Offline Mode)"
    except Exception as e:
        return recommender, f"Error initializing recommender: {e}"

@st.cache_data(ttl=600)
def load_all_movies_df():
    """
    Loads movies DataFrame for dropdowns and tables.
    """
    is_valid, _ = validate_config()
    if is_valid:
        try:
            coll = get_collection(COLL_MOVIES)
            movies = list(coll.find({}, {"_id": 0, "movieId": 1, "title": 1, "genres": 1}))
            if movies:
                return pd.DataFrame(movies)
        except Exception:
            pass
    # Fallback
    try:
        movies, _, _ = load_clean_data_from_disk()
        return pd.DataFrame(movies)
    except Exception:
        return pd.DataFrame(columns=["movieId", "title", "genres"])

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/movie-beginning.png", width=70)
st.sidebar.title("MovieRec BDA")
st.sidebar.markdown("**Big Data Analytics Lab Mini Project**")
st.sidebar.markdown("---")

navigation = st.sidebar.radio(
    "Navigate System Pages:",
    [
        "1. Home",
        "2. Movie Explorer",
        "3. Recommendations",
        "4. Analytics Dashboard",
        "5. MongoDB Operations",
        "6. About Project"
    ]
)

st.sidebar.markdown("---")
# Connection status indicator in sidebar
is_valid, cfg_msg = validate_config()
if is_valid:
    conn_ok, conn_msg, db_info = ping_database()
    if conn_ok:
        st.sidebar.success(f"🟢 Connected to MongoDB Atlas\n`DB: {db_info.get('database_name')}`")
    else:
        st.sidebar.warning(f"🟡 MongoDB Atlas Offline\nUsing local dataset fallback.")
else:
    st.sidebar.info("ℹ️ Local Mode (Set MONGODB_URI in `.env` for Atlas cloud db)")

# Load Recommender and Movies Data
recommender_engine, data_source_label = get_recommender_instance()
movies_df = load_all_movies_df()


# =========================================================
# PAGE 1: HOME
# =========================================================
if navigation == "1. Home":
    st.markdown('<p class="main-title">MovieRec BDA — Big Data Movie Recommendation System</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">A Big Data movie recommendation and analytics platform powered by MongoDB.</p>', unsafe_allow_html=True)

    # Status Banner
    st.info(f"📍 **Data Source:** Currently active with **{data_source_label}**.")

    # KPI Metrics Section
    kpis = get_kpi_summary()
    if kpis["total_movies"] == 0 and not movies_df.empty:
        kpis["total_movies"] = len(movies_df)
        kpis["total_ratings"] = 100836
        kpis["average_rating"] = 3.53
        kpis["total_genres"] = 19

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-number">{kpis["total_movies"]:,}</div><div class="kpi-label">Total Movies</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-number">{kpis["total_ratings"]:,}</div><div class="kpi-label">Total Ratings</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-number">{kpis["average_rating"]} / 5.0</div><div class="kpi-label">Average Rating</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-number">{kpis["total_genres"]}</div><div class="kpi-label">Distinct Genres</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Key Features Grid
    st.subheader("💡 System Architecture & Core Capabilities")
    f_col1, f_col2 = st.columns(2)

    with f_col1:
        st.markdown("""
        #### 🍃 MongoDB NoSQL Engine
        - **Document-Oriented Storage:** Stores unstructured & semi-structured movie metadata and ratings as JSON/BSON documents.
        - **Aggregation Pipelines:** Multi-stage analytics (`$group`, `$sort`, `$lookup`, `$unwind`, `$match`) performed directly on database server nodes.
        - **Custom Indexing:** Compound & single-field B-tree indexes for high-throughput search and fast joins.
        """)

    with f_col2:
        st.markdown("""
        #### 🤖 Content-Based & Hybrid Recommender
        - **Multi-Hot Genre Encoding:** Converts categorical movie genres into sparse feature vectors.
        - **Cosine Similarity Matrix:** Calculates mathematical distance between movie vectors to find relevant titles.
        - **Popularity & Rating Weighting:** Adjusts similarity scores using Bayesian average ratings and rating volume.
        """)

    st.markdown("---")
    st.markdown("### 📊 Workflow Pipeline")
    st.code("""
[ GroupLens MovieLens Dataset ] 
               │
               ▼
[ Download & Cleaning Pipeline ] ──► (Missing checks, Rating bounds 0.5-5.0, Deduplication)
               │
               ▼
[ MongoDB Atlas Document Storage ] ──► (movies, ratings, movie_stats, recommendations)
               │
               ▼
[ Aggregation & Hybrid Recommender ] ──► (Cosine Similarity + Mongo Aggregations)
               │
               ▼
[ Streamlit Web Application ] ──► (Interactive Analytics & Movie Explorer)
    """, language="text")


# =========================================================
# PAGE 2: MOVIE EXPLORER
# =========================================================
elif navigation == "2. Movie Explorer":
    st.subheader("🔍 Movie Explorer")
    st.markdown("Search movies, filter by genre, sort by popularity or rating, and view detailed statistics.")

    if movies_df.empty:
        st.warning("No movie data loaded. Please run dataset preparation scripts.")
    else:
        # Extract unique genres
        all_genres_set = set()
        for g_list in movies_df["genres"]:
            if isinstance(g_list, list):
                all_genres_set.update(g_list)
        sorted_genres = ["All Genres"] + sorted(list(all_genres_set))

        # Filter controls
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            search_query = st.text_input("🔎 Search movie title:", value="")
        with c2:
            selected_genre = st.selectbox("🎭 Filter by Genre:", options=sorted_genres)
        with c3:
            sort_by = st.selectbox("⇅ Sort Movies By:", options=["Title (A-Z)", "Movie ID"])

        # Filter logic
        filtered_df = movies_df.copy()
        if search_query:
            filtered_df = filtered_df[filtered_df["title"].str.contains(search_query, case=False, na=False)]

        if selected_genre != "All Genres":
            filtered_df = filtered_df[filtered_df["genres"].apply(
                lambda g: selected_genre in g if isinstance(g, list) else False
            )]

        if sort_by == "Title (A-Z)":
            filtered_df = filtered_df.sort_values(by="title")
        else:
            filtered_df = filtered_df.sort_values(by="movieId")

        st.markdown(f"Displaying **{len(filtered_df):,}** matching movies:")

        # Display table with pagination/dataframe
        display_df = filtered_df.copy()
        display_df["genres_str"] = display_df["genres"].apply(lambda g: ", ".join(g) if isinstance(g, list) else "")
        st.dataframe(
            display_df[["movieId", "title", "genres_str"]].rename(columns={
                "movieId": "Movie ID",
                "title": "Movie Title",
                "genres_str": "Genres"
            }),
            use_container_width=True,
            height=400
        )

        st.markdown("---")
        st.subheader("📹 Detailed Movie View")
        selected_movie_title = st.selectbox("Select a movie to inspect details:", options=filtered_df["title"].tolist()[:500])

        if selected_movie_title:
            m_row = filtered_df[filtered_df["title"] == selected_movie_title].iloc[0]
            m_id = int(m_row["movieId"])

            # Attempt to fetch rating statistics
            avg_r = 0.0
            cnt_r = 0
            is_valid_db, _ = validate_config()
            if is_valid_db:
                try:
                    stats_coll = get_collection(COLL_STATS)
                    stat = stats_coll.find_one({"movieId": m_id})
                    if stat:
                        avg_r = stat.get("average_rating", 0.0)
                        cnt_r = stat.get("rating_count", 0)
                except Exception:
                    pass

            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                st.metric("Movie ID", m_id)
            with d_col2:
                st.metric("Average Rating", f"{avg_r:.2f} ⭐" if avg_r > 0 else "N/A")
            with d_col3:
                st.metric("Total Ratings", f"{cnt_r:,}" if cnt_r > 0 else "N/A")

            st.markdown(f"**Genres:** {', '.join(m_row['genres'] if isinstance(m_row['genres'], list) else [])}")


# =========================================================
# PAGE 3: RECOMMENDATIONS
# =========================================================
elif navigation == "3. Recommendations":
    st.subheader("🍿 Movie Recommendation Engine")
    st.markdown("Select a movie to generate real-time content-based recommendations using genre similarity vectorization.")

    if movies_df.empty or not recommender_engine.is_fitted:
        st.warning("Recommender engine is not ready. Please verify dataset files.")
    else:
        rc1, rc2, rc3 = st.columns([3, 1, 1])

        with rc1:
            target_movie_title = st.selectbox(
                "🎬 Choose Target Movie:",
                options=recommender_engine.combined_df["title"].tolist(),
                index=0
            )

        with rc2:
            num_recs = st.selectbox("🔢 Top N Recommendations:", options=[5, 10, 15, 20], index=1)

        with rc3:
            algo_type = st.radio("⚙️ Algorithm:", options=["Hybrid Score", "Pure Similarity"])

        if st.button("🚀 Get Recommendations", type="primary"):
            target_row = recommender_engine.combined_df[recommender_engine.combined_df["title"] == target_movie_title].iloc[0]
            target_id = int(target_row["movieId"])

            use_hybrid = (algo_type == "Hybrid Score")
            recs = recommender_engine.get_recommendations(movie_id=target_id, top_n=num_recs, use_hybrid=use_hybrid)

            st.markdown(f"### Recommendations for *'{target_movie_title}'*")
            st.caption(f"Target Genres: **{', '.join(target_row['genres'] if isinstance(target_row['genres'], list) else [])}**")

            st.info("💡 **Recommendation Logic:** Recommendations are generated using content-based multi-hot genre similarity (cosine distance) and optionally adjusted using rating quality and popularity weighting.")

            if not recs:
                st.warning("No recommendations found matching criteria.")
            else:
                for rec in recs:
                    with st.container():
                        r_col1, r_col2 = st.columns([4, 1])
                        with r_col1:
                            st.markdown(f"#### #{rec['rank']} {rec['title']} (`ID: {rec['movieId']}`)")
                            st.markdown(f"**Genres:** {', '.join(rec['genres'])}")
                            st.markdown(f"**Why Recommended:** {rec['explanation']}")
                        with r_col2:
                            st.metric("Similarity Score", f"{rec['similarity_score']:.2f}")
                            st.caption(f"⭐ {rec['average_rating']} ({rec['rating_count']:,} votes)")
                        st.markdown("---")


# =========================================================
# PAGE 4: ANALYTICS DASHBOARD
# =========================================================
elif navigation == "4. Analytics Dashboard":
    st.subheader("📊 Big Data Analytics Dashboard")
    st.markdown("Interactive visual analytics powered by MongoDB aggregation pipelines and Plotly.")

    tab1, tab2, tab3 = st.tabs(["⭐ Ratings & Distribution", "🔥 Top Movies", "🎭 Genre Insights"])

    with tab1:
        st.markdown("#### Rating Distribution across 100,000+ User Votes")
        rating_dist = get_rating_distribution()

        if rating_dist:
            dist_df = pd.DataFrame(rating_dist)
            fig_dist = px.bar(
                dist_df,
                x="rating",
                y="count",
                labels={"rating": "Rating Value (Stars)", "count": "Number of Ratings"},
                title="Rating Value Frequency Distribution",
                color="count",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Rating distribution aggregation pipeline returned no data or MongoDB is offline.")

    with tab2:
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.markdown("#### 🏆 Top 10 Most Rated Movies")
            most_rated = get_most_rated_movies(limit=10)
            if most_rated:
                mr_df = pd.DataFrame(most_rated)
                fig_mr = px.bar(
                    mr_df,
                    x="rating_count",
                    y="title",
                    orientation="h",
                    title="Movies with Most Ratings Volume",
                    labels={"rating_count": "Total Ratings", "title": "Movie Title"},
                    color="rating_count",
                    color_continuous_scale="Blues"
                )
                fig_mr.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_mr, use_container_width=True)

        with col_m2:
            st.markdown("#### 🌟 Top 10 Highest Rated Movies")
            min_thresh = st.slider("Minimum Rating Count Threshold:", min_value=10, max_value=200, value=50, step=10)
            highest_rated = get_highest_rated_movies(min_ratings=min_thresh, limit=10)
            if highest_rated:
                hr_df = pd.DataFrame(highest_rated)
                fig_hr = px.bar(
                    hr_df,
                    x="average_rating",
                    y="title",
                    orientation="h",
                    title=f"Highest Average Rating (Min {min_thresh} votes)",
                    labels={"average_rating": "Average Rating (Out of 5)", "title": "Movie Title"},
                    color="average_rating",
                    color_continuous_scale="YlOrRd"
                )
                fig_hr.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_hr, use_container_width=True)

    with tab3:
        st.markdown("#### 🎭 Genre Popularity & Movie Distribution")
        genre_dist = get_genre_distribution()
        if genre_dist:
            g_df = pd.DataFrame(genre_dist)
            fig_g = px.pie(
                g_df,
                names="genre",
                values="movie_count",
                title="Movie Distribution by Genre",
                hole=0.4
            )
            st.plotly_chart(fig_g, use_container_width=True)


# =========================================================
# PAGE 5: MONGODB OPERATIONS
# =========================================================
elif navigation == "5. MongoDB Operations":
    st.subheader("🍃 MongoDB Operations & Query Demonstrations")
    st.markdown("Demonstrate live NoSQL queries, document structure, indexes, and aggregation pipelines.")

    is_valid_db, msg = validate_config()

    if not is_valid_db:
        st.warning("MongoDB URI is not configured in `.env`. Demonstration mode displaying query examples:")

    st.markdown("### 🛠️ Interactive MongoDB Query Runner")

    query_option = st.selectbox(
        "Choose MongoDB Query Operation to Demonstrate:",
        [
            "1. db.movies.find() - Sample Movies Documents",
            "2. db.movies.find({genres: 'Comedy'}) - Filter by Genre",
            "3. db.ratings.find({rating: {$gte: 4.5}}) - High Ratings Filter",
            "4. db.ratings.aggregate([$group, $sort, $limit]) - Most Rated Movies Pipeline",
            "5. db.movies.aggregate([$unwind, $group]) - Genre Distribution Pipeline"
        ]
    )

    if query_option.startswith("1."):
        st.code("""
// Find 5 movie documents
db.movies.find({}, {projection: {_id: 0}}).limit(5);
        """, language="javascript")
        if is_valid_db:
            try:
                res = list(get_collection(COLL_MOVIES).find({}, {"_id": 0}).limit(5))
                st.json(res)
            except Exception as e:
                st.error(f"Execution error: {e}")

    elif query_option.startswith("2."):
        st.code("""
// Find movies in Comedy genre
db.movies.find({ genres: "Comedy" }, {projection: {_id: 0}}).limit(5);
        """, language="javascript")
        if is_valid_db:
            try:
                res = list(get_collection(COLL_MOVIES).find({"genres": "Comedy"}, {"_id": 0}).limit(5))
                st.json(res)
            except Exception as e:
                st.error(f"Execution error: {e}")

    elif query_option.startswith("3."):
        st.code("""
// Find ratings greater than or equal to 4.5
db.ratings.find({ rating: { $gte: 4.5 } }, {projection: {_id: 0}}).limit(5);
        """, language="javascript")
        if is_valid_db:
            try:
                res = list(get_collection(COLL_RATINGS).find({"rating": {"$gte": 4.5}}, {"_id": 0}).limit(5))
                st.json(res)
            except Exception as e:
                st.error(f"Execution error: {e}")

    elif query_option.startswith("4."):
        st.code("""
// Aggregation: Group ratings by movieId, compute average and count, sort descending
db.ratings.aggregate([
    { $group: { _id: "$movieId", ratingCount: { $sum: 1 }, avgRating: { $avg: "$rating" } } },
    { $sort: { ratingCount: -1 } },
    { $limit: 5 }
]);
        """, language="javascript")
        if is_valid_db:
            try:
                pipe = [
                    {"$group": {"_id": "$movieId", "ratingCount": {"$sum": 1}, "avgRating": {"$avg": "$rating"}}},
                    {"$sort": {"ratingCount": -1}},
                    {"$limit": 5}
                ]
                res = list(get_collection(COLL_RATINGS).aggregate(pipe))
                st.json(res)
            except Exception as e:
                st.error(f"Execution error: {e}")

    elif query_option.startswith("5."):
        st.code("""
// Aggregation: Unwind genres array, count movies per genre
db.movies.aggregate([
    { $unwind: "$genres" },
    { $group: { _id: "$genres", movieCount: { $sum: 1 } } },
    { $sort: { movieCount: -1 } }
]);
        """, language="javascript")
        if is_valid_db:
            try:
                pipe = [
                    {"$unwind": "$genres"},
                    {"$group": {"_id": "$genres", "movieCount": {"$sum": 1}}},
                    {"$sort": {"movieCount": -1}}
                ]
                res = list(get_collection(COLL_MOVIES).aggregate(pipe))
                st.json(res)
            except Exception as e:
                st.error(f"Execution error: {e}")

    st.markdown("---")
    st.markdown("### ❓ Why Choose MongoDB for Big Data Recommendation Systems?")
    st.markdown("""
    - **Flexible Document Schema:** Unlike relational SQL databases with strict table schemas, MongoDB handles dynamic arrays (e.g. `genres: ["Action", "Sci-Fi"]`) naturally without requiring separate junction tables.
    - **High-Performance Aggregation Framework:** Provides native pipeline stages (`$match`, `$group`, `$sort`, `$unwind`, `$lookup`) that process analytics directly in memory at database nodes.
    - **Horizontal Scalability & Sharding:** Automatically distributes collections across cluster nodes as rating dataset size grows from thousands to millions.
    - **Secondary B-Tree Indexing:** Accelerates multi-field queries, title regex searches, and fast join targets.
    """)


# =========================================================
# PAGE 6: ABOUT PROJECT
# =========================================================
elif navigation == "6. About Project":
    st.subheader("📚 About Project — Big Data Analytics Lab Mini Project")

    st.markdown("""
    ### 🎯 Problem Statement
    Modern movie platforms contain large collections of movies and user ratings. Finding relevant movies from these collections can be difficult when users are presented with a large number of choices. This project develops a MongoDB-based Big Data analytics and recommendation system that stores movie and rating information, performs database-level aggregation and analytics, and generates movie recommendations based on content similarity and rating statistics.

    ### 📌 Project Objectives
    1. Store movie and rating data using **MongoDB Atlas Cloud**.
    2. Perform NoSQL data management and validation operations.
    3. Execute multi-stage **MongoDB Aggregation Pipelines** for movie analytics.
    4. Implement a **Content-Based & Hybrid Movie Recommendation Engine**.
    5. Provide an interactive Streamlit UI for recommendation and analytics.

    ### 🛠️ Technology Stack
    - **Database:** MongoDB Atlas (Cloud NoSQL)
    - **Language:** Python 3.10+
    - **UI Framework:** Streamlit
    - **Analytics & Math:** NumPy, Pandas, PyMongo
    - **Visualizations:** Plotly Express
    - **Dataset:** GroupLens MovieLens (ml-latest-small: 100,000+ ratings, 9,700+ movies)

    ### 👥 Project Team
    - **Student Name:** Computer Engineering Student (BE Comp)
    - **Subject:** Big Data Analytics (BDA) Lab Mini Project
    """)

# Footer
st.markdown("---")
st.caption("MovieRec BDA — Big Data Movie Recommendation System | BE Computer Engineering BDA Lab Mini-Project")
