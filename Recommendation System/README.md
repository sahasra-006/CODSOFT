# Movie Recommendation System
A Python project that recommends movies using content-based and collaborative filtering. Built with pandas, scikit-learn, and Streamlit.

## Tech Stack
Python, pandas, numpy, scikit-learn, Streamlit

## How to Run
bashpip install -r requirements.txt

\\CLI demo
python main.py

\\ Web app
streamlit run app.py

## Features
Content-based filtering using TF-IDF + cosine similarity
Collaborative filtering using a user-item rating matrix
Movie search by title, genre, or keyword
Top-rated movies list
Similarity scores displayed in results

## Project Structure
recommendation-system/
├── data/               # movies.csv, ratings.csv
├── src/                # preprocessing, content_based, collaborative_filtering, utils
├── app.py              # Streamlit UI
├── main.py             # CLI demo
└── requirements.txt

## Future Improvements
Use a larger dataset (e.g. MovieLens)
Add SVD-based collaborative filtering
Deploy to Streamlit Community Cloud