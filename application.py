# Import necessary libraries
import pickle                                                     # For loading serialized movie data and similarity matrix
import streamlit as st                                            # Streamlit for creating the web application
import requests                                                   # For making API requests to TMDb
import pandas as pd                                               # For handling tabular data
import warnings                                                   # To suppress warning messages
warnings.filterwarnings("ignore")                                 # Ignore warning messages
import time                                                       # To add delays for better UI experience
# import openai  # Uncomment if using OpenAI API (currently not used)
import sys                                                        # For system-specific parameters and functions (currently unused)

# ---------- Fetch movie details from TMDb API ----------
def fetch_details(movie_id):
    api_key = "d992a4fdc3fdd564a70e63b9e9850954"                  # API key for TMDb
                                                                  # URL to get movie information
    info_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    info = requests.get(info_url).json()                          # Make GET request and parse response as JSON

    # Get poster URL if available
    poster_path = info.get('poster_path', '')
    poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else ""

    # Extract genres as a comma-separated string 
    genres = ", ".join([genre['name'] for genre in info.get('genres', [])])
    rating = info.get('vote_average', 'N/A')                                            # Get average vote
    overview = info.get('overview', 'No description available.')                        # Get overview or fallback
    imdb_id = info.get('imdb_id', '')                                                   # Get IMDb ID
    tmdb_link = f"https://www.themoviedb.org/movie/{movie_id}"                          #  Link to TMDb page
    imdb_link = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else "Not available" # IMDb link
    release_date = info.get('release_date', 'N/A')                                      # Release date
    
    # URL to get cast and crew details
    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}&language=en-US"
    credits = requests.get(credits_url).json()                                          # Make request for credits info

    # Extract top 10 cast members
    cast = [actor['name'] for actor in credits.get('cast', [])[:10]]
    cast_names = ", ".join(cast) if cast else "Not available"

    # Extract director from crew info
    crew = credits.get('crew', [])
    director = next((member['name'] for member in crew if member['job'] == 'Director'), "Not available")

    # Return dictionary of movie details
    return {
        "poster": poster_url,
        "genres": genres,
        "rating": rating,
        "overview": overview,
        "cast": cast_names,
        "director": director,
        "tmdb_link": tmdb_link,
        "imdb_link": imdb_link,
        "release_date": release_date
        
    }

# ---------- Fetch top 10 trending movies from TMDb ----------
def fetch_trending():
    api_key = "d992a4fdc3fdd564a70e63b9e9850954"                                          # TMDb API key
    url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={api_key}"           # Trending endpoint
    response = requests.get(url).json()                                                   # GET request
    return response.get('results', [])[:10]                                               # Return top 10 trending movies

# ---------- Recommend movies similar to selected one ----------
def recommend(movie, selected_genres=[], min_rating=0, min_year=1900, max_year=2100):
    # Get index of the selected movie
    index = movies[movies['title'] == movie].index[0]

    # Get similarity scores and sort them
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended = []                      # List to store recommended movies
    for i in distances[1:]:               #  Skip the first one (same movie)
        movie_id = movies.iloc[i[0]].movie_id  # Get movie ID
        name = movies.iloc[i[0]].title    # Get movie title
        details = fetch_details(movie_id) # Fetch details from TMDb

        # Construct trailer URL (YouTube search)
        trailer_url = f"https://www.youtube.com/results?search_query={name.replace(' ', '+')}+trailer"

        # Parse release year safely
        try:
            release_year = int(details['release_date'].split('-')[0])
        except:
            release_year = 0

        # Apply filters for genre, rating, and year
        if (
            all(g.lower() in details['genres'].lower() for g in selected_genres)
            and float(details['rating']) >= min_rating
            and min_year <= release_year <= max_year
        ):
            # Add to recommendations
            recommended.append({
                "name": name,
                "poster": details['poster'],
                "genres": details['genres'],
                "rating": details['rating'],
                "overview": details['overview'],
                "cast": details['cast'],
                "director": details['director'],
                "trailer_url": trailer_url,
                "imdb_link": details['imdb_link'],
                "tmdb_link": details['tmdb_link'],
                "release_date": details['release_date']
            })
        if len(recommended) == 10:  # Stop after 10 recommendations
            break
    return recommended              # Return list of recommended movies

# ---------- Load serialized movie data and similarity matrix ----------
movies = pickle.load(open('movie_list.pkl', 'rb'))      # Load movie list DataFrame
similarity = pickle.load(open('similarity.pkl', 'rb'))  # Load similarity matrix
movie_list = movies['title'].values                     # Extract movie titles

# ---------- Predefined genre options ----------
genre_options = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", 
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", 
    "Mystery", "Romance", "Science Fiction", "TV Movie", "Thriller", 
    "War", "Western","others"
]

# ---------- Streamlit Page Setup ----------
st.set_page_config(page_title="🎬 Movie Recommender", layout="wide")  # Set page title and layout

# ---------- Main Page Header ----------
st.title("🎬 Movie Recommender System")                                         # Display title
st.markdown("Get personalized movie suggestions based on your favorite film!")  # Description
st.markdown("---")                                                              # Horizontal separator

# ---------- Sidebar Filters for User Input ----------
st.sidebar.header("🔍 Filter Your Recommendations")                            # Sidebar header
selected_movie = st.sidebar.selectbox("🎞️ Select a Movie", movie_list)         # Dropdown for movie selection
selected_genres = st.sidebar.multiselect("🎭 Filter by Genre", genre_options)  # Multi-select for genre
min_rating = st.sidebar.slider("⭐ Minimum IMDb Rating", 0.0, 10.0, 5.0)       # Rating slider
min_year = st.sidebar.slider("📅 Minimum Release Year", min_value=1970, max_value=2025, value=1975)  # Min year
max_year = st.sidebar.slider("📅 Maximum Release Year", min_value=1970, max_value=2025, value=2025)  # Max year

# ---------- Recommendation Button Trigger ----------
if st.button('🚀 Show Recommendations'):
    with st.spinner("Finding movies you’ll love..."):  # Show spinner during processing
        time.sleep(1)                                  # Simulate delay
        recommendations = recommend(selected_movie, selected_genres, min_rating, min_year, max_year)  # Get results

    st.subheader(f"🎯 Top Recommendations for: {selected_movie}")  # Show heading

    if recommendations: 
        watchlist_data = []  # Initialize watchlist data

        for movie in recommendations:      # Iterate over recommendations
            with st.container():           # Create a container per movie
                cols = st.columns([1, 2])  # Two-column layout
                with cols[0]:
                    st.image(movie['poster'], use_container_width=True)  # Show poster
                with cols[1]:
                    st.markdown(f"### {movie['name']}")                       # Movie title
                    st.markdown(f"**🎭 Genres:** {movie['genres']}")         # Genres
                    st.markdown(f"**⭐ Rating:** {movie['rating']}/10")      # Rating
                    st.markdown(f"**🎬 Director:** {movie['director']}")     # Director
                    st.markdown(f"**👥 Cast:** {movie['cast']}")             # Cast
                    st.markdown(f"**📝 Description:** {movie['overview']}")  # Overview
                    st.markdown(f"[▶️ Trailer]({movie['trailer_url']}) | [🎞️ TMDb]({movie['tmdb_link']}) | [🎥 IMDb]({movie['imdb_link']}) | **Release Date:** {movie['release_date']}")  # Links
                st.markdown("---")                                           # Divider

            # Append movie data to download list
            watchlist_data.append({
                "Movie": movie['name'],
                "Genres": movie['genres'],
                "Rating": movie['rating'],
                "Director": movie['director'],
                "Cast": movie['cast'],
                "TMDb Link": movie['tmdb_link'],
                "IMDb Link": movie['imdb_link'],
                "Trailer Link": movie['trailer_url']
            })

        # Convert watchlist to DataFrame and allow download
        df = pd.DataFrame(watchlist_data)
        st.download_button(
            label="💾 Download Watchlist",
            data=df.to_csv(index=False),
            file_name='my_movie_watchlist.csv',
            mime='text/csv'
        )

    else:
        st.warning("😕 No movies matched your filters. Try changing genre, rating, or year range.")

# ---------- Display Trending Movies ----------
with st.expander("🔥 Trending Now on TMDb"):
    
    # Get trending movies
    trending = fetch_trending()                                
    if trending:
        for movie in trending:                                                          # Loop over trending movies
            movie_id = movie['id']
            details = fetch_details(movie_id)                                           # Fetch details
            with st.container():
                cols = st.columns([1, 2])                                               # Two-column layout
                with cols[0]:
                    poster_path = details['poster']
                    st.image(poster_path, use_container_width=True)                     # Show poster
                with cols[1]:
                    st.markdown(f"### {movie['title']}")                                 # Movie title
                    st.markdown(f"**📝 Description:** {details['overview']}")           # Overview
                    st.markdown(f"**🎭 Genres:** {details['genres']}")  # Genres
                    st.markdown(f"**⭐ Rating:** {details['rating']}/10")  # Rating
                    st.markdown(f"**🎬 Director:** {details['director']}")  # Director
                    st.markdown(f"**👥 Cast:** {details['cast']}")  # Cast
                    st.markdown(f"[🎞️ TMDb]({details['tmdb_link']}) | [🎥 IMDb]({details['imdb_link']}) | **Release Date:** {details['release_date']}")  # Links
                st.markdown("---")  # Divider
    else:
        st.write("No trending movies available at the moment.")  # Fallback message
