import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def get_similar_users(user_id, user_item_matrix, top_n=5):
    if user_id not in user_item_matrix.index:
        return []

    # fill missing ratings with 0 for similarity calculation
    matrix_filled = user_item_matrix.fillna(0)
    sim_matrix = cosine_similarity(matrix_filled)
    sim_df = pd.DataFrame(sim_matrix, index=user_item_matrix.index, columns=user_item_matrix.index)

    user_sims = sim_df[user_id].drop(user_id).sort_values(ascending=False)
    return user_sims.head(top_n).index.tolist()


def get_collaborative_recommendations(user_id, user_item_matrix, top_n=5):
    if user_id not in user_item_matrix.index:
        return pd.DataFrame(), f"User {user_id} not found."

    similar_users = get_similar_users(user_id, user_item_matrix)
    if not similar_users:
        return pd.DataFrame(), "Not enough user data for recommendations."

    # movies the target user has already rated
    rated_by_user = user_item_matrix.loc[user_id].dropna().index.tolist()

    # aggregate ratings from similar users for movies our user hasn't seen
    similar_ratings = user_item_matrix.loc[similar_users]
    avg_ratings = similar_ratings.mean(axis=0)

    unrated = avg_ratings.drop(labels=rated_by_user, errors="ignore")
    unrated = unrated.dropna().sort_values(ascending=False).head(top_n)

    results = pd.DataFrame({
        "title": unrated.index,
        "predicted_rating": unrated.values.round(2)
    }).reset_index(drop=True)

    return results, None
