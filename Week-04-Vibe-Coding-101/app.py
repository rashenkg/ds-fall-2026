import streamlit as st
import pandas as pd
import plotly.express as px


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="MovieLens Dashboard",
    page_icon="🎬",
    layout="wide"
)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("Week-04-Vibe-Coding-101/data/movie_ratings.csv")
    return df


df = load_data()


# ---------------------------------------------------------
# Clean and prepare data
# ---------------------------------------------------------

# Make sure year is numeric
df["year"] = pd.to_numeric(df["year"], errors="coerce")

# Remove rows that do not have the fields needed for analysis
df_clean = df.dropna(subset=["rating", "title", "movie_id"])


# ---------------------------------------------------------
# Create genre-level dataset
# ---------------------------------------------------------

genre_df = df_clean.copy()

# Split pipe-separated genres
genre_df["genres"] = genre_df["genres"].fillna("Unknown").str.split("|")

# Create one row per movie/genre/rating combination
genre_df = genre_df.explode("genres")

# Remove extra whitespace
genre_df["genres"] = genre_df["genres"].str.strip()


# Create unique movie/genre relationships.
# This prevents movies with many ratings from being counted
# multiple times in the genre distribution.
movie_genres = (
    genre_df[
        ["movie_id", "title", "year", "genres"]
    ]
    .drop_duplicates()
)


# ---------------------------------------------------------
# Calculate genre distribution
# ---------------------------------------------------------

genre_counts = (
    movie_genres
    .groupby("genres")["movie_id"]
    .nunique()
    .sort_values(ascending=False)
)


# ---------------------------------------------------------
# Calculate genre satisfaction
# ---------------------------------------------------------

genre_ratings = (
    genre_df
    .groupby("genres")["rating"]
    .mean()
    .sort_values(ascending=False)
)


# ---------------------------------------------------------
# Calculate ratings by movie release year
# ---------------------------------------------------------

ratings_by_year = (
    df_clean
    .dropna(subset=["year"])
    .groupby("year")["rating"]
    .mean()
    .reset_index()
    .sort_values("year")
)


# ---------------------------------------------------------
# Calculate movie-level rating statistics
# ---------------------------------------------------------

movie_stats = (
    df_clean
    .groupby(["movie_id", "title"])
    .agg(
        average_rating=("rating", "mean"),
        rating_count=("rating", "count")
    )
    .reset_index()
)


# ---------------------------------------------------------
# Dashboard title
# ---------------------------------------------------------

st.title("MovieLens Movie Ratings Dashboard")

st.write(
    "Explore genre distributions, genre satisfaction, "
    "rating trends across movie release years, and highly rated movies."
)


# ---------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------

st.sidebar.header("Dashboard Controls")


# Genre selector
available_genres = sorted(
    genre_df["genres"].dropna().unique().tolist()
)

selected_genres = st.sidebar.multiselect(
    "Select genres for the satisfaction chart",
    options=available_genres,
    default=available_genres
)


# Rating threshold
rating_threshold = st.sidebar.slider(
    "Minimum number of ratings",
    min_value=10,
    max_value=500,
    value=50,
    step=10
)


# ---------------------------------------------------------
# Question 1
# ---------------------------------------------------------

st.header("1. Genre Breakdown")

st.write(
    "Number of unique rated movies associated with each genre. "
    "Movies with multiple genres are counted once in each applicable genre."
)

fig_genre_distribution = px.bar(
    genre_counts,
    orientation="h",
    labels={
        "value": "Number of Movies",
        "genres": "Genre"
    },
    title="Number of Rated Movies by Genre"
)

fig_genre_distribution.update_layout(
    yaxis={"categoryorder": "total ascending"}
)

st.plotly_chart(
    fig_genre_distribution,
    use_container_width=True
)


# ---------------------------------------------------------
# Question 2
# ---------------------------------------------------------

st.header("2. Genre Satisfaction")

st.write(
    "Average rating for each genre. A movie's ratings contribute "
    "to every genre assigned to that movie."
)

if selected_genres:

    filtered_genre_ratings = (
        genre_ratings
        .loc[genre_ratings.index.isin(selected_genres)]
        .sort_values(ascending=True)
    )

    fig_genre_satisfaction = px.bar(
        filtered_genre_ratings,
        orientation="h",
        labels={
            "value": "Average Rating",
            "genres": "Genre"
        },
        title="Average Rating by Genre"
    )

    fig_genre_satisfaction.update_layout(
        yaxis={"categoryorder": "total ascending"}
    )

    st.plotly_chart(
        fig_genre_satisfaction,
        use_container_width=True
    )

    highest_genre = filtered_genre_ratings.idxmax()
    lowest_genre = filtered_genre_ratings.idxmin()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Highest Average Rating",
            f"{highest_genre}: {filtered_genre_ratings.max():.2f}"
        )

    with col2:
        st.metric(
            "Lowest Average Rating",
            f"{lowest_genre}: {filtered_genre_ratings.min():.2f}"
        )

else:
    st.warning("Select at least one genre.")


# ---------------------------------------------------------
# Question 3
# ---------------------------------------------------------

st.header("3. Ratings Over Time")

st.write(
    "Mean rating grouped by the movie's release year, "
    "not the year in which the user submitted the rating."
)

fig_ratings_over_time = px.line(
    ratings_by_year,
    x="year",
    y="rating",
    labels={
        "year": "Movie Release Year",
        "rating": "Mean Rating"
    },
    title="Mean Rating by Movie Release Year",
    markers=True
)

st.plotly_chart(
    fig_ratings_over_time,
    use_container_width=True
)


# ---------------------------------------------------------
# Question 4
# ---------------------------------------------------------

st.header("4. Best Movies With a Rating Floor")

st.write(
    "Top 5 movies ranked by average rating after requiring "
    "a minimum number of ratings."
)


# Interactive threshold
filtered_movies = (
    movie_stats[
        movie_stats["rating_count"] >= rating_threshold
    ]
    .sort_values(
        "average_rating",
        ascending=False
    )
    .head(5)
)


fig_top_movies = px.bar(
    filtered_movies.sort_values("average_rating"),
    x="average_rating",
    y="title",
    orientation="h",
    text="average_rating",
    labels={
        "average_rating": "Average Rating",
        "title": "Movie"
    },
    title=f"Top 5 Movies — At Least {rating_threshold} Ratings"
)

fig_top_movies.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)

st.plotly_chart(
    fig_top_movies,
    use_container_width=True
)


# ---------------------------------------------------------
# Required comparison: 50 vs 150 ratings
# ---------------------------------------------------------

st.subheader("Required Comparison: 50 vs. 150 Ratings")


def get_top_movies(threshold):
    return (
        movie_stats[
            movie_stats["rating_count"] >= threshold
        ]
        .sort_values(
            "average_rating",
            ascending=False
        )
        .head(5)
    )


top_50 = get_top_movies(50)
top_150 = get_top_movies(150)


col1, col2 = st.columns(2)


with col1:

    st.write("### Minimum 50 Ratings")

    st.dataframe(
        top_50[
            ["title", "average_rating", "rating_count"]
        ].reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )


with col2:

    st.write("### Minimum 150 Ratings")

    st.dataframe(
        top_150[
            ["title", "average_rating", "rating_count"]
        ].reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.divider()

st.caption(
    "MovieLens Dashboard | Built with Python, Pandas, Plotly, and Streamlit"
)