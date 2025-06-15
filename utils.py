import requests

# ---------- Fetch movie details ----------
def fetch_details(movie_id):
    api_key = "d992a4fdc3fdd564a70e63b9e9850954"
    
    # Movie info
    info_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        info = requests.get(info_url).json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch movie details: {e}"}
    
    poster_path = info.get('poster_path', '')
    poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else ""
    genres = ", ".join([genre['name'] for genre in info.get('genres', [])])
    rating = info.get('vote_average', 'N/A')
    overview = info.get('overview', 'No description available.')
    imdb_id = info.get('imdb_id', '')
    tmdb_link = f"https://www.themoviedb.org/movie/{movie_id}"
    imdb_link = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else "Not available"
    
    # Credits
    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}&language=en-US"
    try:
        credits = requests.get(credits_url).json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch credits: {e}"}
    
    cast = [actor['name'] for actor in credits.get('cast', [])[:3]]
    cast_names = ", ".join(cast) if cast else "Not available"
    
    crew = credits.get('crew', [])
    director = next((member['name'] for member in crew if member['job'] == 'Director'), "Not available")
    
    return {
        "poster": poster_url,
        "genres": genres,
        "rating": rating,
        "overview": overview,
        "cast": cast_names,
        "director": director,
        "tmdb_link": tmdb_link,
        "imdb_link": imdb_link
    }

# ---------- Recommend movies ----------
def recommend(movie, selected_genres, min_rating, movies, similarity):
    # Check if movie exists in the dataset
    if movie not in movies['title'].values:
        return []

    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended = []
    for i in distances[1:]:
        movie_id = movies.iloc[i[0]].movie_id
        name = movies.iloc[i[0]].title
        details = fetch_details(movie_id)
        trailer_url = f"https://www.youtube.com/results?search_query={name.replace(' ', '+')}+trailer"

        # Check if movie matches selected genres and rating
        movie_genres = set(details['genres'].lower().split(", "))  # Set for faster comparison
        selected_genres_set = set([genre.lower() for genre in selected_genres])
        
        if movie_genres.intersection(selected_genres_set) and float(details['rating']) >= min_rating:
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
                "tmdb_link": details['tmdb_link']
            })
        if len(recommended) == 5:
            break
    return recommended
