import pandas as pd
import numpy as np
import os


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_movies():
    path = os.path.join(DATA_DIR, "movies.csv")
    df = pd.read_csv(path)
    df.dropna(subset=["title", "genre", "description"], inplace=True)
    df["genre"] = df["genre"].fillna("Unknown")
    df["description"] = df["description"].fillna("")
    df["avg_rating"] = df["avg_rating"].fillna(df["avg_rating"].mean())
    df["content"] = df["genre"].str.replace("|", " ") + " " + df["description"]
    df.reset_index(drop=True, inplace=True)
    return df


def load_ratings():
    path = os.path.join(DATA_DIR, "ratings.csv")
    df = pd.read_csv(path)
    df.dropna(inplace=True)
    df["rating"] = df["rating"].clip(0, 10)
    return df


def build_user_item_matrix(ratings_df, movies_df):
    merged = ratings_df.merge(movies_df[["movie_id", "title"]], on="movie_id", how="left")
    matrix = merged.pivot_table(index="user_id", columns="title", values="rating")
    return matrix
