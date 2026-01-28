import streamlit as st
import requests
import pandas as pd
from streamlit_searchbox import st_searchbox
import os

API_KEY = os.getenv("TMDB_API_KEY")

# Aplikacja korzysta z danych TMDB API, ale nie jest oficjalnie powiązana z TMDB.

st.set_page_config(page_title="Rekomendacje", page_icon="🎬", layout="wide", )
st.title("🎬 Znajdź rekomendacje", text_alignment="center")
st.caption("Wyszukaj film, aby znaleźć rekomendacje na jego podstawie.", text_alignment="center")

# Stan dla searchbox
if "movie_search_key" not in st.session_state:
    st.session_state.movie_search_key = 0

if "movie_title_to_id" not in st.session_state: 
    st.session_state.movie_title_to_id = {}

# Funkcja znajdująca słowa kluczowe dla filmu
@st.cache_data(ttl=3600)
def get_movie_keywords(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}/keywords",
        params={"api_key": API_KEY}
    )
    return r.json().get("keywords", [])

# Funkcja wyszukiwania filmów
@st.cache_data(ttl=3600)
def search_movies(query: str):
    if not query:
        return []

    r = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={
            "api_key": API_KEY,
            "query": query,
            "language": "pl-PL",
            "page": 1,
            "include_adult": False
        }
    )
    results = r.json().get("results", [])
    results = sorted(results, key=lambda x: x.get("popularity", 0), reverse=True)

    return [(f"{m['title']} ({m.get('release_date','')[:4]})", m['id']) for m in results[:20]] # tuple(label, id)

# Funkcja pobierająca szczegóły filmu
@st.cache_data(ttl=3600)
def get_movie_details(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}",
        params={"api_key": API_KEY, "language": "pl-PL"}
    )
    return r.json()

# Funkcja pobierająca pełną obsadę (aktorzy i obsada techniczna)
@st.cache_data(ttl=3600)
def get_movie_credits(movie_id):
        r = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}/credits",
            params={"api_key": API_KEY, "language": "pl-PL"}
        )
        return r.json()

# Funkcja pobierająca ID filmów
@st.cache_data(ttl=3600)
def get_genre_ids():
    r = requests.get(
        "https://api.themoviedb.org/3/genre/movie/list",
        params={"api_key": API_KEY, "language": "pl-PL"}
    )
    genres = r.json().get("genres", [])
    # zamiana nazwa -> id
    return {g['name']: g['id'] for g in genres}

# Funkcja pobierająca filmy po gatunkach
@st.cache_data(ttl=3600)
def get_movies_by_genres(genre_ids, language=None, n=51):
    movies = []
    page = 1
    while len(movies) < n:
        params = {
            "api_key": API_KEY,
            "with_genres": ",".join(map(str, genre_ids)),
            "language": "pl-PL",
            "sort_by": "popularity.desc",
            "page": page,
            "include_adult": False
        }
        if language:
            params["with_original_language"] = language
        r = requests.get("https://api.themoviedb.org/3/discover/movie", params=params)
        results = r.json().get("results", [])
        for m in results:
            details = get_movie_details(m['id'])
            movies.append(details)
            if len(movies) >= n:
                break
        page += 1
    return movies[:n]

# Słownik gatunków obowiązkowych, dla których rekomendacja musi zgadzać się z wyszukiwanym filmem
MANDATORY_GENRES = {"Animation", "Horror", "Documentary", "Fantasy", "Western",
                    "Document", "Historical", "Musical", "Sci-Fi", "War"}

# Funkcja do tworzenia rekomendacji
@st.cache_data(ttl=3600)
def custom_recommendations(movie, candidate_movies, top_n=51):
    movie_genres = {g['name'] for g in movie.get('genres', [])}
    movie_keywords = {k['name'] for k in get_movie_keywords(movie['id'])}
    mandatory_in_movie = MANDATORY_GENRES.intersection(movie_genres)
    
    candidate_keywords = {m['id']: {k['name'] for k in get_movie_keywords(m['id'])} 
                          for m in candidate_movies}

    scored_movies = []
    for m in candidate_movies:
        if m['id'] == movie['id']:
            continue
        m_genres = {g['name'] for g in m.get('genres', [])}

        # Filtrowanie po gatunkach obowiązkowych
        if mandatory_in_movie and not mandatory_in_movie.issubset(m_genres):
            continue  # odrzucamy film jeśli nie ma wymaganego gatunku
        
        score = 0   # waga (wynik filmu)

        # Liczba wspólnych gatunków
        common_genres = movie_genres.intersection(m_genres)
        score += len(common_genres) * 2
        if len(common_genres) >= 2:
            score += 3  # zwiększenie wagi (wyniku filmu)

        m_keywords = candidate_keywords[m['id']]
        common_keywords = movie_keywords.intersection(m_keywords)
        score += len(common_keywords)

        if len(common_keywords) >= 3:
            score += 4  # zwiększenie wagi (wyniku filmu)

        scored_movies.append((score, m, common_genres, common_keywords))

    scored_movies.sort(key=lambda x: x[0], reverse=True)
    return scored_movies[:top_n]

# Słownik id: gatunek
genre_name_to_id = get_genre_ids()

# Searchbox
selected_movie = st_searchbox(search_movies, key="movie_searchbox",
                              placeholder="Np. Shrek, Avatar, Zmierzch ...")

# Wyświetlanie wybranego filmu
if selected_movie:
    movie_id = selected_movie
    if movie_id:
        movie = get_movie_details(movie_id)
        movie_genre_ids = [genre_name_to_id[g['name']] for g in movie.get('genres', []) if g['name'] in genre_name_to_id]

        st.markdown(f"### {movie.get('title', 'Brak tytułu')}", text_alignment="center")

        if movie.get('tagline'):
                st.markdown(f"*{movie.get('tagline', '')}*", text_alignment="center")

        st.markdown(
            "<hr style='border: 0.5px solid #ddd; margin-top: 4px; margin-bottom: 30px;'>",
            unsafe_allow_html=True
        )

        col_left, div, col_right = st.columns([1, 0.2, 4])

        with col_left:
            if movie.get("poster_path"):
                st.image(f"https://image.tmdb.org/t/p/w400{movie['poster_path']}")
            else:
                st.write("Brak plakatu")

        with div:
            st.markdown("<div style='border-left:1px solid #ddd; height:100%;'></div>",
                    unsafe_allow_html=True)

        with col_right:
            
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Oryginalny tytuł:** {movie.get('original_title', '–')}")
                genres = ", ".join([g['name'] for g in movie.get('genres', [])])
                st.write(f"**Gatunki:** {genres or '–'}")
                st.write(f"**Ocena:** {movie.get('vote_average', '–')} ({movie.get('vote_count', '–')} głosów)")
                runtime = movie.get('runtime')
                st.write(f"**Czas trwania:** {runtime} min" if runtime else "Czas trwania: –")

            with col2:
                st.write(f"**Data wydania:** {movie.get('release_date', '–')}")
                languages = ', '.join([l['name'] for l in movie.get('spoken_languages', [])])
                st.write(f"**Język:** {languages or '–'}")
                st.write(f"**Budżet:** {movie.get('budget', '–')}$")
                st.write(f"**Przychód:** {movie.get('revenue', '–')}$")

            st.markdown(
                "<hr style='border: 0.5px solid #ddd; margin-top: 4px; margin-bottom: 20px;'>",
                unsafe_allow_html=True
            )

            keywords = get_movie_keywords(movie_id)
            keyword_names = [k['name'] for k in keywords]
            if keyword_names:
                st.markdown("**Słowa kluczowe:** " + ", ".join(keyword_names))

            st.markdown(
                "<hr style='border: 0.5px solid #ddd; margin-top: 4px; margin-bottom: 20px;'>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"<p><strong>Opis:</strong> {movie.get('overview', 'Brak opisu')}</p>",
                unsafe_allow_html=True
            )


        action = st.pills(label="", options=["Szukaj rekomendacji"], selection_mode="single", width="content")

        if action == "Szukaj rekomendacji":
            language_code = movie.get('spoken_languages', [{}])[0].get('iso_639_1')
            candidate_movies = get_movies_by_genres(movie_genre_ids, language=language_code, n=51)

            recommendations = custom_recommendations(movie, candidate_movies, top_n=51)

            st.markdown(f"<h3 style='text-align:center;'>Znalezione rekomendacje ({len(recommendations)})</h3>",
                        unsafe_allow_html=True)
            st.divider()

            for score, rec, common_genres, common_keywords in recommendations:
                col1, div, col2 = st.columns([1, 0.2, 4])
                with col1:
                    if rec.get('poster_path'):
                        st.image(f"https://image.tmdb.org/t/p/w200{rec['poster_path']}")

                with div:
                    st.markdown("<div style='border-left:1px solid #ddd; height:100%;'></div>",
                        unsafe_allow_html=True)  

                with col2:
                    st.markdown(f"<h3>{rec['title']} ({rec.get('release_date','')[:4]})</h3>", unsafe_allow_html=True)

                    st.markdown(
                        "<hr style='border: 0.5px solid #ddd; margin-top: 4px; margin-bottom: 20px;'>",
                        unsafe_allow_html=True
                    )

                    st.write(f"*Ocena:* {rec.get('vote_average', '–')} ({movie.get('vote_count', '–')} głosów)")
                    st.write(f"*Wspólne gatunki:* {', '.join(common_genres) or '–'}")
                    st.write(f"*Wspólne słowa kluczowe:* {', '.join(list(common_keywords)[:5]) or '–'}")
                    if st.button("Zobacz szczegóły", key=f"details_{rec['id']}"):
                        st.switch_page("pages/movie.py", query_params={"id": rec["id"]})

                st.divider()


placeholder = st.empty()

with placeholder.container():
    if st.button("🏠︎"):
        st.query_params.clear()
        st.switch_page("main.py")

st.markdown(
    """
    <style>
    .element-container:nth-of-type(1) button {
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 999;
        width: 50px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
