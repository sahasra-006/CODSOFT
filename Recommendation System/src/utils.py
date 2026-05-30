import pandas as pd


def search_movies(query, movies_df):
    query = query.lower().strip()
    mask = (
        movies_df["title"].str.lower().str.contains(query) |
        movies_df["genre"].str.lower().str.contains(query) |
        movies_df["description"].str.lower().str.contains(query)
    )
    return movies_df[mask][["title", "genre", "year", "avg_rating"]].reset_index(drop=True)


def get_top_rated(movies_df, n=10):
    return movies_df.sort_values("avg_rating", ascending=False).head(n)[
        ["title", "genre", "year", "avg_rating"]
    ].reset_index(drop=True)


def format_genres(genre_str):
    return genre_str.replace("|", " • ")
