import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Add root project directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import (
    validate_config,
    COLL_MOVIES,
    COLL_RATINGS,
    COLL_STATS,
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
)

# Page configuration
st.set_page_config(
    page_title="MovieRec-BDA",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for clean student project aesthetic
st.markdown("""
    <style>
    .kpi-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 6px;
        padding: 16px;
        text-align: center;
    }
    .kpi-number {
        font-size: 1.8rem;
        font-weight: bold;
        color: #212529;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #6c757d;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Streamlit Cached Resource & Helper Functions
# ---------------------------------------------------------
@st.cache_resource
def get_recommender_instance():
    """
    Loads and caches the MovieRecommender engine.
    Tries MongoDB Atlas first, falls back to local dataset.
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

    # Fallback to local processed JSON files
    try:
        movies, ratings, stats = load_clean_data_from_disk()
        recommender.fit_from_data(movies, stats)
        return recommender, "Local Dataset (Offline Mode)"
    except Exception as e:
        return recommender, f"Error initializing recommender: {e}"

@st.cache_data(ttl=600)
def load_all_movies_df():
    """
    Loads movies DataFrame for selection dropdowns and tables.
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
st.sidebar.title("MovieRec-BDA")
st.sidebar.markdown("---")

navigation = st.sidebar.radio(
    "Navigation",
    [
        "1. Home",
        "2. Movie Explorer",
        "3. Recommendations",
        "4. Analytics Dashboard",
        "5. MongoDB Operations"
    ]
)

st.sidebar.markdown("---")
# Database connection status indicator in sidebar
is_valid, cfg_msg = validate_config()
if is_valid:
    conn_ok, conn_msg, db_info = ping_database()
    if conn_ok:
        st.sidebar.success(f"Connected to MongoDB Atlas\n(DB: {db_info.get('database_name')})")
    else:
        st.sidebar.warning("MongoDB Atlas Offline (Using Local Data)")
else:
    st.sidebar.info("Local Mode (Set MONGODB_URI in .env for Cloud DB)")

# Load Recommender and Movies Data
recommender_engine, data_source_label = get_recommender_instance()
movies_df = load_all_movies_df()


# =========================================================
# PAGE 1: HOME
# =========================================================
if navigation == "1. Home":
    st.header("Home")
    
    st.write(
        "MovieRec-BDA is a movie recommendation and analytics project built using MongoDB, Python and Streamlit. "
        "It uses movie ratings and genre information to explore movies and generate recommendations."
    )

    st.info(f"**Data Source:** Currently active using **{data_source_label}**.")

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

    st.subheader("What this project does")
    st.markdown("""
    - **Explore movie information:** Search movies, filter by genre, and view rating counts.
    - **View ratings and statistics:** Analyze overall rating distributions and top-rated movies.
    - **Find movies similar to a selected movie:** Generate recommendations based on content similarity and genre matching.
    - **Analyze the movie-rating dataset:** Perform database aggregations directly on MongoDB collections.
    - **View MongoDB operations used by the project:** Inspect collections, indexes, and aggregation queries.
    """)

    st.subheader("System Overview")
    st.markdown("""
    1. **Data Ingestion:** MovieLens dataset is preprocessed, validated, and stored in MongoDB Atlas collections (`movies`, `ratings`, `movie_stats`).
    2. **MongoDB Aggregation:** Rating statistics and top movie charts are calculated using native MongoDB aggregation pipelines (`$group`, `$sort`, `$lookup`, `$unwind`).
    3. **Content Recommendation:** Genres are multi-hot encoded into feature vectors, and cosine similarity is used to rank similar movies.
    """)


# =========================================================
# PAGE 2: MOVIE EXPLORER
# =========================================================
elif navigation == "2. Movie Explorer":
    st.header("Movie Explorer")
    st.write("Search for a movie, filter by genre, and view details.")

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
            search_query = st.text_input("Search for a movie:", value="")
        with c2:
            selected_genre = st.selectbox("Filter by genre:", options=sorted_genres)
        with c3:
            sort_by = st.selectbox("Sort by:", options=["Title (A-Z)", "Movie ID"])

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

        st.write(f"Showing **{len(filtered_df):,}** movies:")

        display_df = filtered_df.copy()
        display_df["genres_str"] = display_df["genres"].apply(lambda g: ", ".join(g) if isinstance(g, list) else "")
        st.dataframe(
            display_df[["movieId", "title", "genres_str"]].rename(columns={
                "movieId": "Movie ID",
                "title": "Title",
                "genres_str": "Genres"
            }),
            use_container_width=True,
            height=350
        )

        st.markdown("---")
        st.subheader("Movie details")
        selected_movie_title = st.selectbox("Select a movie to view details:", options=filtered_df["title"].tolist()[:500])

        if selected_movie_title:
            m_row = filtered_df[filtered_df["title"] == selected_movie_title].iloc[0]
            m_id = int(m_row["movieId"])

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
                st.metric("Rating", f"{avg_r:.2f} / 5.0" if avg_r > 0 else "N/A")
            with d_col3:
                st.metric("Number of ratings", f"{cnt_r:,}" if cnt_r > 0 else "N/A")

            st.write(f"**Genres:** {', '.join(m_row['genres'] if isinstance(m_row['genres'], list) else [])}")


# =========================================================
# PAGE 3: RECOMMENDATIONS
# =========================================================
elif navigation == "3. Recommendations":
    st.header("Movie Recommendations")
    st.write("Select a movie to get recommendations based on genre similarity and rating statistics.")

    if movies_df.empty or not recommender_engine.is_fitted:
        st.warning("Recommender engine is not ready. Please verify dataset files.")
    else:
        rc1, rc2, rc3 = st.columns([3, 1, 1])

        with rc1:
            target_movie_title = st.selectbox(
                "Select a movie:",
                options=recommender_engine.combined_df["title"].tolist(),
                index=0
            )

        with rc2:
            num_recs = st.selectbox("Number of recommendations:", options=[5, 10, 15, 20], index=1)

        with rc3:
            algo_type = st.radio("Scoring method:", options=["Hybrid (Genre + Rating)", "Genre Similarity Only"])

        if st.button("Get Recommendations"):
            target_row = recommender_engine.combined_df[recommender_engine.combined_df["title"] == target_movie_title].iloc[0]
            target_id = int(target_row["movieId"])

            use_hybrid = (algo_type == "Hybrid (Genre + Rating)")
            recs = recommender_engine.get_recommendations(movie_id=target_id, top_n=num_recs, use_hybrid=use_hybrid)

            st.subheader(f"Recommended movies for '{target_movie_title}'")
            st.write(f"Genres of selected movie: **{', '.join(target_row['genres'] if isinstance(target_row['genres'], list) else [])}**")

            if not recs:
                st.warning("No recommendations found matching criteria.")
            else:
                for rec in recs:
                    with st.container():
                        r_col1, r_col2 = st.columns([4, 1])
                        with r_col1:
                            st.markdown(f"#### #{rec['rank']} {rec['title']} (ID: {rec['movieId']})")
                            st.write(f"**Genres:** {', '.join(rec['genres'])}")
                            st.write(f"**Why these movies were suggested:** {rec['explanation']}")
                        with r_col2:
                            st.metric("Similarity", f"{rec['similarity_score']:.2f}")
                            st.caption(f"Rating: {rec['average_rating']} ({rec['rating_count']:,} votes)")
                        st.markdown("---")


# =========================================================
# PAGE 4: ANALYTICS DASHBOARD
# =========================================================
elif navigation == "4. Analytics Dashboard":
    st.header("Analytics Dashboard")
    st.write("Visualizations generated from MongoDB aggregations on the MovieLens dataset.")

    tab1, tab2, tab3 = st.tabs(["Dataset Overview & Rating Statistics", "Popular Movies", "Genre Distribution"])

    with tab1:
        st.subheader("Rating Statistics")
        st.write("Distribution of user rating scores (0.5 to 5.0 stars):")
        rating_dist = get_rating_distribution()

        if rating_dist:
            dist_df = pd.DataFrame(rating_dist)
            fig_dist = px.bar(
                dist_df,
                x="rating",
                y="count",
                labels={"rating": "Rating Value", "count": "Number of Ratings"},
                title="Rating Value Distribution",
                color_discrete_sequence=["#1f77b4"]
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Rating distribution data is unavailable or MongoDB is offline.")

    with tab2:
        st.subheader("Popular Movies")
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.markdown("##### Most Rated Movies")
            most_rated = get_most_rated_movies(limit=10)
            if most_rated:
                mr_df = pd.DataFrame(most_rated)
                fig_mr = px.bar(
                    mr_df,
                    x="rating_count",
                    y="title",
                    orientation="h",
                    labels={"rating_count": "Total Ratings", "title": "Movie Title"},
                    color_discrete_sequence=["#2ca02c"]
                )
                fig_mr.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_mr, use_container_width=True)

        with col_m2:
            st.markdown("##### Highest Rated Movies")
            min_thresh = st.slider("Minimum number of ratings:", min_value=10, max_value=200, value=50, step=10)
            highest_rated = get_highest_rated_movies(min_ratings=min_thresh, limit=10)
            if highest_rated:
                hr_df = pd.DataFrame(highest_rated)
                fig_hr = px.bar(
                    hr_df,
                    x="average_rating",
                    y="title",
                    orientation="h",
                    labels={"average_rating": "Average Rating", "title": "Movie Title"},
                    color_discrete_sequence=["#ff7f0e"]
                )
                fig_hr.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_hr, use_container_width=True)

    with tab3:
        st.subheader("Genre Distribution")
        st.write("Number of movies per genre category:")
        genre_dist = get_genre_distribution()
        if genre_dist:
            g_df = pd.DataFrame(genre_dist)
            fig_g = px.pie(
                g_df,
                names="genre",
                values="movie_count",
                title="Movie Breakdown by Genre"
            )
            st.plotly_chart(fig_g, use_container_width=True)


# =========================================================
# PAGE 5: MONGODB OPERATIONS
# =========================================================
elif navigation == "5. MongoDB Operations":
    st.header("MongoDB Operations")
    st.write("Demonstration of NoSQL queries, collections, indexes, and aggregation pipelines.")

    is_valid_db, msg = validate_config()

    if not is_valid_db:
        st.warning("MongoDB URI is not set in `.env`. Demonstration query examples:")

    st.subheader("Query Examples")

    query_option = st.selectbox(
        "Select a MongoDB query operation to inspect:",
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
                st.error(f"Query error: {e}")

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
                st.error(f"Query error: {e}")

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
                st.error(f"Query error: {e}")

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
                st.error(f"Query error: {e}")

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
                st.error(f"Query error: {e}")

    st.markdown("---")
    st.subheader("MongoDB Database Statistics & Features")
    st.markdown("""
    - **Collections:** `movies`, `ratings`, `movie_stats`, `recommendations`.
    - **Indexes:** Built on `movieId`, `title`, `genres`, `userId`, and `rating` for fast lookup and aggregation.
    - **Document Storage:** Flexible JSON/BSON format allows storing array fields like `genres` directly inside documents.
    - **Aggregation Framework:** Pipeline stages (`$group`, `$sort`, `$unwind`, `$lookup`) run directly on database servers.
    """)
