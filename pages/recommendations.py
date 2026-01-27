import streamlit as st
import requests
import pandas as pd
from streamlit_searchbox import st_searchbox
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

# Aplikacja korzysta z danych TMDB API, ale nie jest oficjalnie powiązana z TMDB.


st.set_page_config(page_title="Rekomendacje", layout="wide")
st.title("Znajdź rekomendacje")

# --- Session state ---
if "movie_search_key" not in st.session_state:
    st.session_state.movie_search_key = 0

if "movie_title_to_id" not in st.session_state: 
    st.session_state.movie_title_to_id = {}

@st.cache_data(ttl=3600)
def get_movie_keywords(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}/keywords",
        params={"api_key": API_KEY}
    )
    return r.json().get("keywords", [])  # lista słowników: {"id":..., "name":...}


# --- Funkcja wyszukiwania filmów ---
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

    # lista tupli (label, id)
    return [(f"{m['title']} ({m.get('release_date','')[:4]})", m['id']) for m in results[:20]]


# --- Searchbox ---
selected_movie = st_searchbox(
    search_movies,
    label="Wyszukaj film, aby zobaczyć jego szczegóły.",
    key="movie_searchbox",
    placeholder="Np. Matrix, Avatar..."
)

# --- Funkcja pobrania szczegółów filmu ---
@st.cache_data(ttl=3600)
def get_movie_details(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}",
        params={"api_key": API_KEY, "language": "pl-PL"}
    )
    return r.json()

@st.cache_data(ttl=3600)
def get_movie_credits(movie_id):
        r = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}/credits",
            params={"api_key": API_KEY, "language": "pl-PL"}
        )
        return r.json()


@st.cache_data(ttl=3600)
def get_genre_ids():
    r = requests.get(
        "https://api.themoviedb.org/3/genre/movie/list",
        params={"api_key": API_KEY, "language": "pl-PL"}
    )
    genres = r.json().get("genres", [])
    # zamiana nazwa -> id
    return {g['name']: g['id'] for g in genres}

genre_name_to_id = get_genre_ids()

@st.cache_data(ttl=3600)
def get_movies_by_genres(genre_ids, language=None, n=50):
    movies = []
    page = 1
    while len(movies) < n:
        params = {
            "api_key": API_KEY,
            "with_genres": ",".join(map(str, genre_ids)),  # filtr po gatunkach
            "language": "pl-PL",
            "sort_by": "popularity.desc",
            "page": page,
            "include_adult": False
        }
        if language:
            params["with_original_language"] = language  # opcjonalnie filtr języka
        r = requests.get("https://api.themoviedb.org/3/discover/movie", params=params)
        results = r.json().get("results", [])
        for m in results:
            details = get_movie_details(m['id'])
            movies.append(details)
            if len(movies) >= n:
                break
        page += 1
    return movies[:n]


MANDATORY_GENRES = {"Animation", "Horror", "Documentary", "Fantasy", "Western",
                    "Document", "Historical", "Musical", "Sci-Fi", "War"}

def custom_recommendations(movie, candidate_movies, top_n=50):
    movie_genres = {g['name'] for g in movie.get('genres', [])}
    movie_keywords = {k['name'] for k in get_movie_keywords(movie['id'])}
    mandatory_in_movie = MANDATORY_GENRES.intersection(movie_genres)

    scored_movies = []
    for m in candidate_movies:
        if m['id'] == movie['id']:
            continue
        m_genres = {g['name'] for g in m.get('genres', [])}

        # twarde filtrowanie po gatunkach obowiązkowych
        if mandatory_in_movie and not mandatory_in_movie.issubset(m_genres):
            continue  # odrzucamy film, nie ma wymaganego gatunku
        
        score = 0

        # liczba wspólnych gatunków (większa waga)
        common_genres = movie_genres.intersection(m_genres)
        score += len(common_genres) * 2
        if len(common_genres) >= 2:
            score += 3

        m_keywords = {k['name'] for k in get_movie_keywords(m['id'])}
        common_keywords = movie_keywords.intersection(m_keywords)
        score += len(common_keywords)

        if len(common_keywords) >= 3:
            score += 4  # bonus za dużo keywords

        scored_movies.append((score, m, common_genres, common_keywords))

    scored_movies.sort(key=lambda x: x[0], reverse=True)
    return scored_movies[:top_n]


# def filtered_recommendations(base_movie, filters, candidate_movies, top_n=10):
#     """
#     Filtruje listę candidate_movies według wybranych filtrów.
#     Wszystkie wybrane filtry muszą się zgadzać.
#     """
#     recommendations = []

#     base_budget = base_movie.get('budget', 0)
#     base_revenue = base_movie.get('revenue', 0)
#     base_year = int(base_movie.get('release_date', '1900')[:4]) if base_movie.get('release_date') else 1900

#     base_genres = {g['name'] for g in base_movie.get('genres', [])}

#     for m in candidate_movies:
#         # pomijamy film bazowy
#         if m['id'] == base_movie['id']:
#             continue

#         # --- Sprawdzanie filtrów ---
#         # Gatunki - min 1 wspólny
#         m_genres = {g['name'] for g in m.get('genres', [])}
#         if 'genres' in filters and filters['genres']:
#             if not base_genres.intersection(m_genres):
#                 continue

#         # Aktorzy
#         m_cast = {c['name'] for c in m.get('credits', {}).get('cast', [])}
#         if 'cast' in filters and filters['cast']:
#             if not set(filters['cast']).issubset(m_cast):
#                 continue

#         # Crew
#         m_crew = m.get('credits', {}).get('crew', [])
#         m_dir = {c['name'] for c in m_crew if c['job'] == 'Director'}
#         m_writers = {c['name'] for c in m_crew if c['job'] in ['Writer', 'Screenplay', 'Author']}
#         m_producers = {c['name'] for c in m_crew if c['job'] == 'Producer'}

#         if 'directors' in filters and filters['directors']:
#             if not set(filters['directors']).issubset(m_dir):
#                 continue
#         if 'writers' in filters and filters['writers']:
#             if not set(filters['writers']).issubset(m_writers):
#                 continue
#         if 'producers' in filters and filters['producers']:
#             if not set(filters['producers']).issubset(m_producers):
#                 continue

#         # Keywords
#         m_keywords = {k['name'] for k in m.get('keywords', [])}
#         if 'keywords' in filters and filters['keywords']:
#             if not set(filters['keywords']).issubset(m_keywords):
#                 continue

#         # Język
#         m_languages = {l['iso_639_1'] for l in m.get('spoken_languages', [])}
#         if 'language' in filters and filters['language']:
#             if not set(filters['language']).intersection(m_languages):
#                 continue

#         # Budżet
#         m_budget = m.get('budget', 0)
#         if 'budget_category' in filters and filters['budget_category']:
#             budget_ok = False
#             for b in filters['budget_category']:
#                 if b == "mniejszy" and m_budget < base_budget:
#                     budget_ok = True
#                 elif b == "podobny" and 0.75*base_budget <= m_budget <= 1.25*base_budget:
#                     budget_ok = True
#                 elif b == "większy" and m_budget > base_budget:
#                     budget_ok = True
#             if not budget_ok:
#                 continue

#         # Przychód
#         m_revenue = m.get('revenue', 0)
#         if 'revenue_category' in filters and filters['revenue_category']:
#             revenue_ok = False
#             for r in filters['revenue_category']:
#                 if r == "mniejszy" and m_revenue < base_revenue:
#                     revenue_ok = True
#                 elif r == "podobny" and 0.75*base_revenue <= m_revenue <= 1.25*base_revenue:
#                     revenue_ok = True
#                 elif r == "większy" and m_revenue > base_revenue:
#                     revenue_ok = True
#             if not revenue_ok:
#                 continue

#         # Data
#         m_year = int(m.get('release_date', '1900')[:4]) if m.get('release_date') else 1900
#         if 'date_category' in filters and filters['date_category']:
#             date_ok = False
#             for d in filters['date_category']:
#                 if d == "starszy" and m_year < base_year:
#                     date_ok = True
#                 elif d == "w tym samym okresie" and m_year == base_year:
#                     date_ok = True
#                 elif d == "nowszy" and m_year > base_year:
#                     date_ok = True
#             if not date_ok:
#                 continue

#         # jeśli przeszło wszystkie filtry
#         recommendations.append(m)

#         if len(recommendations) >= top_n:
#             break

#     return recommendations



# --- Wyświetlanie wybranego filmu ---
if selected_movie:
    movie_id = selected_movie
    if movie_id:
        movie = get_movie_details(movie_id)
        movie_genre_ids = [genre_name_to_id[g['name']] for g in movie.get('genres', []) if g['name'] in genre_name_to_id]

        col1, col2 = st.columns([1, 3])
        with col1:
            if movie.get("poster_path"):
                st.image(f"https://image.tmdb.org/t/p/w200{movie['poster_path']}")
            else:
                st.write("Brak plakatu")

        with col2:
            st.markdown(f"### {movie.get('title', 'Brak tytułu')}")
            st.write(f"**Oryginalny tytuł:** {movie.get('original_title', '–')}")
            genres = ", ".join([g['name'] for g in movie.get('genres', [])])
            st.write(f"**Gatunki:** {genres or '–'}")
            st.write(f"**Ocena:** {movie.get('vote_average', '–')} ({movie.get('vote_count', '–')} głosów)")
            st.write(f"**Data wydania:** {movie.get('release_date', '–')}")
            runtime = movie.get('runtime')
            st.write(f"**Czas trwania:** {runtime} min" if runtime else "Czas trwania: –")
            if movie.get('tagline'):
                st.write(f"**Hasło:** {movie['tagline']}")
            if movie.get('homepage'):
                st.markdown(f"[Strona oficjalna]({movie['homepage']})")

            keywords = get_movie_keywords(movie_id)
            keyword_names = [k['name'] for k in keywords]

            if keyword_names:
                st.write("**Słowa kluczowe:**")
                st.write(", ".join(keyword_names))

            languages = ', '.join([l['name'] for l in movie.get('spoken_languages', [])])
            st.write(f"**Języki mówione:** {languages or '–'}")

            st.write(f"**Budżet:** {movie.get('budget', '–')}$")
            st.write(f"**Przychód:** {movie.get('revenue', '–')}$")
            st.markdown(f"<p style='font-size:0.9rem'>{movie.get('overview', 'Brak opisu')}</p>", unsafe_allow_html=True)

    
        action = st.pills(
            "Wybierz akcję",
            options=["Szukaj rekomendacji"],
            selection_mode="single",
            width="stretch"
        )

        if action == "Szukaj rekomendacji":
            language_code = movie.get('spoken_languages', [{}])[0].get('iso_639_1')  # np. "pl"
            candidate_movies = get_movies_by_genres(movie_genre_ids, language=language_code, n=50)

            recommendations = custom_recommendations(movie, candidate_movies, top_n=50)

            st.markdown(f"### Znalezione rekomendacje ({len(recommendations)})")
            for score, rec, common_genres, common_keywords in recommendations:
                col1, col2 = st.columns([1, 3])
                with col1:
                    if rec.get('poster_path'):
                        st.image(f"https://image.tmdb.org/t/p/w92{rec['poster_path']}")

                with col2:
                    st.write(f"**{rec['title']}** ({rec.get('release_date','')[:4]})")
                    st.write(f"Wspólne gatunki: {', '.join(common_genres) or '–'}")
                    st.write(f"Wspólne słowa kluczowe: {', '.join(list(common_keywords)[:5]) or '–'}")
                    if st.button("Zobacz szczegóły", width="stretch", key=f"details_{rec['id']}"):
                        st.switch_page(
                            "pages/movie.py",
                            query_params={"id": rec["id"]}
                        )




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
        right: 20px;
        z-index: 999;
        width: 50px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



