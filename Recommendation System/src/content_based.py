import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_tfidf_matrix(movies_df):
    tfidf = TfidfVectorizer(stop_words="english", max_features=500)
    tfidf_matrix = tfidf.fit_transform(movies_df["content"])
    return tfidf_matrix


def get_content_recommendations(movie_title, movies_df, tfidf_matrix, top_n=5):
    movies_df = movies_df.reset_index(drop=True)

    # find the movie in our data
    matches = movies_df[movies_df["title"].str.lower() == movie_title.lower()]
    if matches.empty:
        return pd.DataFrame(), "Movie not found in the dataset."

    idx = matches.index[0]

    # compute cosine similarity between selected movie and all others
    movie_vec = tfidf_matrix[idx]
    similarity_scores = cosine_similarity(movie_vec, tfidf_matrix).flatten()

    # sort by score, skip the movie itself
    similar_indices = similarity_scores.argsort()[::-1]
    similar_indices = [i for i in similar_indices if i != idx][:top_n]

    results = movies_df.iloc[similar_indices][["title", "genre", "year", "avg_rating"]].copy()
    results["similarity_score"] = [round(similarity_scores[i], 4) for i in similar_indices]
    results.reset_index(drop=True, inplace=True)

    return results, None
