import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.preprocessing import load_movies, load_ratings, build_user_item_matrix
from src.content_based import build_tfidf_matrix, get_content_recommendations
from src.collaborative_filtering import get_collaborative_recommendations
from src.utils import search_movies, get_top_rated, format_genres

# --- page config ---
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# --- load data once ---
@st.cache_data
def load_all_data():
    movies = load_movies()
    ratings = load_ratings()
    user_item = build_user_item_matrix(ratings, movies)
    tfidf_matrix = build_tfidf_matrix(movies)
    return movies, ratings, user_item, tfidf_matrix

movies_df, ratings_df, user_item_matrix, tfidf_matrix = load_all_data()


# --- sidebar ---
st.sidebar.title("🎬 Movie Recommender")
st.sidebar.markdown("A simple recommendation system built with Python & scikit-learn.")
st.sidebar.markdown("---")

mode = st.sidebar.radio(
    "Choose Mode",
    ["Content-Based", "Collaborative Filtering", "Search", "Top Rated"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.markdown(
    "This project uses TF-IDF + Cosine Similarity for content-based filtering "
    "and a user-item matrix approach for collaborative filtering."
)


# --- main area ---
st.title("🎬 Movie Recommendation System")
st.markdown("Discover movies you'll love based on what you've already watched.")
st.markdown("---")


# =========================================================
# MODE 1: Content-Based
# =========================================================
if mode == "Content-Based":
    st.header("Content-Based Recommendations")
    st.markdown(
        "Pick a movie and we'll find similar ones based on genre and description "
        "using TF-IDF vectorization and cosine similarity."
    )

    movie_list = sorted(movies_df["title"].tolist())
    selected_movie = st.selectbox("Select a movie you liked:", movie_list)

    top_n = st.slider("Number of recommendations:", min_value=3, max_value=10, value=5)

    if st.button("Get Recommendations", type="primary"):
        results, error = get_content_recommendations(selected_movie, movies_df, tfidf_matrix, top_n)

        if error:
            st.error(error)
        else:
            st.success(f"Top {top_n} movies similar to **{selected_movie}**:")

            # show selected movie info
            movie_info = movies_df[movies_df["title"] == selected_movie].iloc[0]
            with st.expander("Selected Movie Details"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Rating", movie_info["avg_rating"])
                col2.metric("Year", movie_info["year"])
                col3.metric("Genre", format_genres(movie_info["genre"]))
                st.write(movie_info["description"])

            st.markdown("### Recommended Movies")
            for i, row in results.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    col1.write(f"**{row['title']}**")
                    col2.write(format_genres(row["genre"]))
                    col3.write(f"⭐ {row['avg_rating']}")
                    col4.write(f"Match: `{row['similarity_score']:.2f}`")
                st.divider()


# =========================================================
# MODE 2: Collaborative Filtering
# =========================================================
elif mode == "Collaborative Filtering":
    st.header("Collaborative Filtering")
    st.markdown(
        "Enter a User ID to see recommendations based on what similar users have watched and rated."
    )

    available_users = sorted(user_item_matrix.index.tolist())
    user_id = st.selectbox("Select User ID:", available_users)

    top_n = st.slider("Number of recommendations:", min_value=3, max_value=10, value=5)

    if st.button("Get Recommendations", type="primary"):
        results, error = get_collaborative_recommendations(user_id, user_item_matrix, top_n)

        if error:
            st.error(error)
        else:
            # show movies this user has already rated
            user_rated = user_item_matrix.loc[user_id].dropna()
            with st.expander(f"Movies User {user_id} has already rated ({len(user_rated)})"):
                for title, rating in user_rated.sort_values(ascending=False).items():
                    st.write(f"- **{title}** — ⭐ {rating}")

            st.success(f"Top {top_n} recommendations for User {user_id}:")

            if results.empty:
                st.warning("Not enough data to generate recommendations for this user.")
            else:
                st.markdown("### Predicted Ratings")
                for i, row in results.iterrows():
                    col1, col2 = st.columns([4, 1])
                    col1.write(f"**{row['title']}**")
                    col2.write(f"⭐ {row['predicted_rating']}")
                    st.divider()


# =========================================================
# MODE 3: Search
# =========================================================
elif mode == "Search":
    st.header("Search Movies")
    st.markdown("Search by title, genre, or keywords from the description.")

    query = st.text_input("Enter search term:", placeholder="e.g. crime, thriller, dream...")

    if query:
        results = search_movies(query, movies_df)
        if results.empty:
            st.warning("No movies found matching your search.")
        else:
            st.success(f"Found {len(results)} result(s):")
            for i, row in results.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    col1.write(f"**{row['title']}** ({row['year']})")
                    col2.write(format_genres(row["genre"]))
                    col3.write(f"⭐ {row['avg_rating']}")
                st.divider()


# =========================================================
# MODE 4: Top Rated
# =========================================================
elif mode == "Top Rated":
    st.header("Top Rated Movies")
    st.markdown("The highest rated movies in our dataset.")

    n = st.slider("Show top N movies:", min_value=5, max_value=20, value=10)
    top_movies = get_top_rated(movies_df, n)

    for rank, (i, row) in enumerate(top_movies.iterrows(), start=1):
        col1, col2, col3, col4 = st.columns([0.5, 3, 2, 1])
        col1.write(f"**#{rank}**")
        col2.write(f"**{row['title']}** ({row['year']})")
        col3.write(format_genres(row["genre"]))
        col4.write(f"⭐ {row['avg_rating']}")
        st.divider()


# --- footer ---
st.markdown("---")
st.caption("Built with Python · pandas · scikit-learn · Streamlit")
