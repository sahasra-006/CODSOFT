"""
main.py - quick CLI to test the recommendation system without launching Streamlit
Usage: python main.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.preprocessing import load_movies, load_ratings, build_user_item_matrix
from src.content_based import build_tfidf_matrix, get_content_recommendations
from src.collaborative_filtering import get_collaborative_recommendations
from src.utils import search_movies, get_top_rated


def run_demo():
    print("Loading data...")
    movies_df = load_movies()
    ratings_df = load_ratings()
    user_item_matrix = build_user_item_matrix(ratings_df, movies_df)
    tfidf_matrix = build_tfidf_matrix(movies_df)

    print(f"Loaded {len(movies_df)} movies and {len(ratings_df)} ratings.\n")

    # --- Content-Based Example ---
    print("=" * 50)
    print("CONTENT-BASED RECOMMENDATIONS")
    print("=" * 50)
    test_movie = "Inception"
    results, err = get_content_recommendations(test_movie, movies_df, tfidf_matrix, top_n=5)
    if err:
        print(f"Error: {err}")
    else:
        print(f"Movies similar to '{test_movie}':\n")
        print(results[["title", "genre", "similarity_score"]].to_string(index=False))

    print()

    # --- Collaborative Filtering Example ---
    print("=" * 50)
    print("COLLABORATIVE FILTERING")
    print("=" * 50)
    test_user = 1
    results, err = get_collaborative_recommendations(test_user, user_item_matrix, top_n=5)
    if err:
        print(f"Error: {err}")
    else:
        print(f"Recommendations for User {test_user}:\n")
        print(results.to_string(index=False))

    print()

    # --- Search Example ---
    print("=" * 50)
    print("SEARCH: 'crime'")
    print("=" * 50)
    search_results = search_movies("crime", movies_df)
    print(search_results[["title", "genre", "avg_rating"]].to_string(index=False))

    print()

    # --- Top Rated ---
    print("=" * 50)
    print("TOP 5 RATED MOVIES")
    print("=" * 50)
    top = get_top_rated(movies_df, 5)
    print(top.to_string(index=False))


if __name__ == "__main__":
    run_demo()
