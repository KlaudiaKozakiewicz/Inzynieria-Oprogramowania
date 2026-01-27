import streamlit as st
import requests
import pandas as pd
import altair as alt # biblioteka wykresów
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

# Aplikacja korzysta z danych TMDB API, ale nie jest oficjalnie powiązana z TMDB.


query_params = st.query_params
movie_id = query_params.get("id")

if not movie_id:
    st.error("Brak ID filmu")
    st.stop()

@st.cache_data(ttl=3600)
def fetch_movie_details(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}",
        params={
            "api_key": API_KEY,
            "language": "pl-PL",
            "append_to_response": "credits"
        }
    )
    return r.json()

movie = fetch_movie_details(movie_id)

# pobieranie filmów z tych samych gatunków
@st.cache_data(ttl=3600)
def fetch_similar_genre_movies(genre_ids):
    r = requests.get(
        "https://api.themoviedb.org/3/discover/movie",
        params={
            "api_key": API_KEY,
            "with_genres": ",".join(map(str, genre_ids)),
            "vote_count.gte": 100,
            "language": "pl-PL"
        }
    )
    return r.json().get("results", [])


MANDATORY_GENRES = {"Animation", "Horror", "Documentary", "Fantasy", "Western",
                    "Document", "Historical", "Musical", "Sci-Fi", "War"}

@st.cache_data(ttl=3600)
def get_movie_keywords(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}/keywords",
        params={"api_key": API_KEY}
    )
    return r.json().get("keywords", [])  # lista słowników: {"id":..., "name":...}

def custom_recommendations(movie, candidate_movies, top_n=5):
    movie_genres = {g['name'] for g in movie.get('genres', [])}
    scored_movies = []
    
    for m in candidate_movies:
        if m['id'] == movie['id']:
            continue
        m_genres = {g['name'] for g in m.get('genres', [])}
        common_genres = movie_genres.intersection(m_genres)
        score = len(common_genres)
        scored_movies.append((score, m, common_genres))  # <-- krotka z 3 elementami
    
    scored_movies.sort(key=lambda x: x[0], reverse=True)
    return scored_movies[:top_n]

# pobieranie kandydatów
movie_genre_ids = [g['id'] for g in movie.get('genres', [])]
candidate_movies = fetch_similar_genre_movies(movie_genre_ids)

# konwertujemy, żeby każde movie miało wspólne gatunki
recommendations = custom_recommendations(movie, candidate_movies, top_n=5)

st.set_page_config(
    page_title="movie",
    page_icon="🎬",
    layout="wide"
)

st.title(movie["title"])

col1, col2 = st.columns([1, 3])

with col1:
    if movie.get("poster_path"):
        st.image(
            f"https://image.tmdb.org/t/p/w300{movie['poster_path']}"
        )

with col2:
    st.write(f"**Ocena:** {movie['vote_average']} ({movie['vote_count']} głosów)")
    st.write(f"**Premiera:** {movie.get('release_date')}")
    st.write(f"**Czas trwania:** {movie.get('runtime')} min")
    st.write("**Gatunki:** " + ", ".join(g["name"] for g in movie["genres"]))
    st.markdown(
        f"<p style='font-size:0.9rem'>{movie.get('overview','Brak opisu')}</p>",
        unsafe_allow_html=True
    )

@st.cache_data(ttl=3600)
def fetch_genres():
    r = requests.get(
        "https://api.themoviedb.org/3/genre/movie/list",
        params = {"api_key": API_KEY, "language": "pl-PL"}
    )
    return r.json()["genres"]

@st.cache_data(ttl=3600)
def get_runtime(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}",
        params={"api_key": API_KEY}
    )
    return r.json().get("runtime", 0)

st.divider()

selected_tab = st.pills(options=["Rekomendacje na podstawie filmu", "Analiza"], 
         label="Wybierz opcję:",
         default="Rekomendacje na podstawie filmu",
         width="stretch")

genres = fetch_genres()



if selected_tab == "Rekomendacje na podstawie filmu":
    if recommendations:
        
        for score, rec, common_genres in recommendations:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if rec.get("poster_path"):
                    st.image(f"https://image.tmdb.org/t/p/w200{rec['poster_path']}")
                else:
                    st.write("Brak plakatu")
            
            with col2:
                st.markdown(f"**{rec.get('title', 'Brak tytułu')} ({rec.get('release_date','')[:4]})**")
                st.write(f"Wspólne gatunki: {', '.join(common_genres) or '–'}")
                
                if st.button("Zobacz szczegóły", key=f"rec_{rec['id']}"):
                    st.switch_page("pages/movie.py", query_params={"id": rec["id"]})

            st.divider()
                



# ========= Analizy ============
if selected_tab == "Analiza":

    st.subheader("Popularność na tle podobnych filmów", help = "Popularność to dynamiczny wskaźnik TMDB oparty o aktywność i zainteresowanie użytkowników")

    genre_ids = [g["id"] for g in movie["genres"]]
    similar_movies = fetch_similar_genre_movies(genre_ids)

    df_similar = pd.DataFrame(similar_movies)

    if not df_similar.empty:
        avg_popularity = df_similar["popularity"].mean()

        col1, col2 = st.columns(2)
        col1.metric(
            "Popularność filmu",
            f"{movie['popularity']:.1f}"
        )
        col2.metric(
            "Średnia popularność gatunku",
            f"{avg_popularity:.1f}",
            delta=f"{movie['popularity'] - avg_popularity:+.1f}"
        )





    st.subheader("Popularność filmu wg liczby głosów", help = "Na tle podobnych topowych filmów")

    # Pobieramy ID gatunków filmu
    genre_ids = [g["id"] for g in movie["genres"]]

    @st.cache_data(ttl=3600)
    def fetch_genre_top_votes(genre_ids, limit=10):
        """Pobiera top filmy z tych samych gatunków posortowane po liczbie głosów"""
        r = requests.get(
            "https://api.themoviedb.org/3/discover/movie",
            params={
                "api_key": API_KEY,
                "with_genres": ",".join(map(str, genre_ids)),
                "sort_by": "vote_count.desc",
                "vote_count.gte": 50,
                "language": "pl-PL",
                "page": 1
            }
        )
        return r.json().get("results", [])[:limit]

    top_genre_votes = fetch_genre_top_votes(genre_ids)

    # Dodajemy nasz film, jeśli nie jest w top
    if movie not in top_genre_votes:
        top_genre_votes.append(movie)

    df_votes = pd.DataFrame(top_genre_votes)
    df_votes["highlight"] = df_votes["id"] == movie["id"]  # podświetlenie wybranego filmu

    # Wykres słupkowy z kolorami
    import altair as alt

    chart_votes = alt.Chart(df_votes).mark_bar().encode(
        x=alt.X("title:N", sort="-y", title="Film"),
        y=alt.Y("vote_count:Q", title="Liczba głosów"),
        color=alt.condition(
            alt.datum.highlight,
            alt.value("#9b6dc6"),  # jasnofioletowy
            alt.value("#90CAF9")   # jasnoniebieski 
        ),
        tooltip=["title", "vote_count", "vote_average"]
    )

    st.altair_chart(chart_votes, use_container_width=True)

    # Dodatkowa metryka
    highlight_votes = movie.get("vote_count", 0)
    st.metric(
        "Liczba głosów wybranego filmu",
        f"{highlight_votes}",
        help="Porównanie liczby głosów Twojego filmu z innymi top filmami w tym samym gatunku"
    )


    st.subheader("Budżet vs Przychody")

    budget = movie.get("budget", 0)
    revenue = movie.get("revenue", 0)
    roi = (revenue - budget) / budget if budget > 0 else None

    df_fin = pd.DataFrame([
        {"Kategoria": "Budżet", "Kwota": budget},
        {"Kategoria": "Przychody", "Kwota": revenue}
    ])

    # Ustawienie kolorów według kategorii
    color_scale = alt.Scale(
        domain=["Budżet", "Przychody"],
        range=["#3f2893", "#9b6dc6"]  #
    )

    chart_fin = alt.Chart(df_fin).mark_bar(color="#1f77b4").encode(
        x=alt.X("Kategoria:N", title=""),
        y=alt.Y("Kwota:Q", title="Kwota ($)"),
        tooltip=["Kategoria", "Kwota"],
        color=alt.Color("Kategoria:N", scale=color_scale, legend=None)
    )


    st.altair_chart(chart_fin, use_container_width=True)

    if roi is not None:
        st.metric(
            label="ROI (zwrot z inwestycji)",
            value=f"{roi*100:.1f}%",
            help="ROI = (Przychody - Budżet) / Budżet"
        )



# ======== Przycisk powrotu do menu ===========
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
