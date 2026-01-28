import streamlit as st
import pandas as pd
import altair as alt
import requests
from streamlit_searchbox import st_searchbox
from datetime import date
import os

API_KEY = os.getenv("TMDB_API_KEY")

# === Test poprawności API ===
#if not API_KEY:
#    st.error("Brak TMDB_API_KEY! Dodaj go w ustawieniach Streamlit.")
#else:
#    st.success("API key załadowany poprawnie")
    
# Aplikacja korzysta z danych TMDB API, ale nie jest oficjalnie powiązana z TMDB.


### Zdjęcie w tle
st.markdown(
    """
    <div style="
        background-image: url('https://image.tmdb.org/t/p/original/vm4H1DivjQoNIm0Vs6i3CTzFxQ0.jpg');
        background-size: cover;
        background-position: 50% 70%;
        padding: 15px;
        border-radius: 10px;
    ">
        <h1 style="color:white; text-align:center;">🎬 Filmy</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# Ustawienia strony
st.set_page_config(page_title="Filmy", page_icon="🎬", layout="wide")

# Ukrycie paska bocznego
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header > div:nth-of-type(1) {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Pobranie dzisiejszej daty
today = date.today().isoformat()

### Funkcje 

# Funkcja do wyszukiwania filmów
@st.cache_data(ttl=3600)
def search_movies(query: str):
    if not query or len(query) < 1:
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

    # Sortowanie po popularności
    results = sorted(results, key=lambda x: x.get("popularity", 0), reverse=True)

    titles = []
    for movie in results[:20]:
        title = movie["title"]
        year = movie.get("release_date", "")[:4]
        label = f"{title} ({year})" if year else title

        titles.append(label)
        st.session_state.movie_title_to_id[label] = movie["id"]

    return titles

# Funkcja do odczytania czasu trwania filmu
@st.cache_data(ttl=3600)
def get_runtime(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}",
        params={"api_key": API_KEY}
    )
    return r.json().get("runtime", 0)

# Funkcja do wyszukiwania najbardziej popularnych filmów
@st.cache_data(ttl=3600)
def fetch_top_movies(category, genre_id=None, min_votes=500, limit=20):
    params = {
        "api_key": API_KEY,
        "language": "pl-PL",
        "page": 1,
        "vote_count.gte": min_votes
    }

    url = "https://api.themoviedb.org/3/discover/movie"

    if category == "Popularne":
        params["sort_by"] = "popularity.desc"

    elif category == "Najwyżej oceniane":
        params["sort_by"] = "vote_average.desc"
        params["primary_release_date.lte"] = today  # tylko filmy, które już wyszły

    elif category == "Nowości":
        params["sort_by"] = "primary_release_date.desc"


    if genre_id:
        params["with_genres"] = genre_id

    r = requests.get(url, params=params)
    results = r.json().get("results", [])

    return results[:limit]

# Funkcja do odczytania gatunków
@st.cache_data(ttl=3600)
def fetch_genres():
    r = requests.get(
        "https://api.themoviedb.org/3/genre/movie/list",
        params = {"api_key": API_KEY, "language": "pl-PL"}
    )
    return r.json()["genres"]



# Header
st.subheader("Wyszukiwarka filmów", text_alignment="center",
             help="Zacznij wpisywać tytuł filmu, aby pokazały się dostępne opcje.")


## SEARCHBOX (wyszukiwarka filmów)

# stan dla klucza szukanego filmu
# 'licznik'
if "movie_search_key" not in st.session_state:
    st.session_state.movie_search_key = 0
# mapowanie
if "movie_title_to_id" not in st.session_state: 
    st.session_state.movie_title_to_id = {}

# Searchbox (wyszukiwarka filmów)
selected_movie = st_searchbox(search_movies,
                              key=f"movie_searchbox_{st.session_state.movie_search_key}",
                              placeholder="Np. Shrek, Avatar, Zmierzch ...")

# Sprawdzenie czy użytkownik wybrał film
if selected_movie:
    movie_id = st.session_state.movie_title_to_id.get(selected_movie)
    # jeśli tak, zmieniana jest strona
    if movie_id:
        st.session_state.movie_search_key += 1  # reset 'searchbox'
        st.switch_page("pages/movie.py", query_params={"id": movie_id})


# Przyciski 'co obejrzeć?', 'rekomendacje', 'analiza' - odnośniki
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Co obejrzeć?", width = "stretch",
                 help="Przejdź do strony, aby znaleźć film na podstawie filtrów."):
        st.switch_page("pages/what2watch.py")
with col2:
    if st.button("Rekomendacje", width = "stretch",
                 help="Przejdź do strony, aby znaleźć rekomendacje na podstawie filmu."):
        st.switch_page("pages/recommendations.py")
with col3:
    if st.button("Analizy filmów", width = "stretch",
              help="Przejdź do strony, aby znaleźć analizy filmów."):
        st.switch_page("pages/analysis.py")

st.divider()

# Pobranie gatunków (słowniki)
genres = fetch_genres()
# Zamiana słownika w format name : id
GENRE_NAME_TO_ID = {g["name"]: g["id"] for g in genres}


# Wyświetlanie 'Top' filmów

left, div, right = st.columns([10, 1, 10])

with left:
    st.subheader("TOP filmy", text_alignment="center", 
             help="Wybierz kategorię i/lub gatunek, aby znaleźć filmy.")

    # Wyświetlenie opcji do wyboru
    selected_tab = st.pills(label="Kategoria", width="stretch",
            options=["Najwyżej oceniane", "Popularne", "Nowości"],
            key="top_movies_pills", default="Najwyżej oceniane")

    selected_genre = st.pills("Gatunek", list(GENRE_NAME_TO_ID.keys()),
                              help="Wybierz gatunek, aby filtrować filmy lub zostaw niezaznaczone, aby zobaczyć wszystkie.")
    
    # Ustawienie wartości "id gatunku"
    genre_id = GENRE_NAME_TO_ID[selected_genre] if selected_genre else None

    # Wyszukanie filmów na podstawie wybranych parametrów
    movies = fetch_top_movies(category=selected_tab, genre_id=genre_id, min_votes=1000, limit=20)

    st.subheader(f"Top 20 – {selected_tab}" + (f" / {selected_genre}" if selected_genre else ""),
                 text_alignment="center")

    ## Wyświetlanie wyszukanych filmów:
    for movie in movies:
        col1, col2 = st.columns([1, 3], gap="small")

        with col1:
            # Plakat
            if movie.get("poster_path"):
                st.image(f"https://image.tmdb.org/t/p/w200{movie['poster_path']}")
            else:
                st.write("Brak plakatu")

        with col2:
            # Tytuł
            st.markdown(f"### {movie.get('title', 'Brak tytułu')}")

            # Gatunki
            movie_genres = [g['name'] for g in genres if g['id'] in movie.get('genre_ids', [])]
            if movie_genres:
                st.markdown("**Gatunki:** " + ", ".join(movie_genres))

            # ocena i liczba głosów
            vote_avg = movie.get("vote_average", 0)
            vote_count = movie.get("vote_count", 0)
            st.markdown(f"**Ocena:** {vote_avg} ({vote_count} głosów)")

            # Data wydania
            release_date = movie.get("release_date", "Brak")
            st.markdown(f"**Data wydania:** {release_date}")

            # Czas trwania
            runtime = get_runtime(movie['id']) if movie.get('id') else 0
            if runtime:
                st.markdown(f"**Czas trwania:** {runtime} min")

        # Opis filmu
        overview = movie.get("overview", "Brak opisu")
        st.markdown(f"<p style='text-align: justify; 'font-size:0.85rem'>{overview}</p>", unsafe_allow_html=True) 

        if st.button("Pokaż szczegóły", width = "stretch", key=f"details_{movie['id']}"):
            st.session_state.movie_search_key += 1  # opcjonalny reset searchboxa
            st.switch_page("pages/movie.py", query_params={"id": movie["id"]})   

        st.divider()

with div:
    st.markdown("<div style='border-left:1px solid #ddd; height:100%;'></div>",
                        unsafe_allow_html=True)    

# Wyświetlenie dashboardów
with right:
    st.subheader("Dashboard filmów")
    
    # Jeśli nie ma danych 
    if not movies:
        st.info("Brak danych do wizualizacji")
        st.stop()

    # zmiana listy słowników na Dataframe
    df = pd.DataFrame(movies)
    
    df["release_year"] = pd.to_datetime(
        df["release_date"], errors="coerce" # zabezpieczenie przed pustymi datami
    ).dt.year
    
    # zakładki
    tab1, tab2, tab3 = st.tabs([
        "Popularność",
        "Oceny",
        "Gatunki"
    ])

    
    with tab1:
        st.markdown("### Popularność filmów", help=("Popularność to dynamiczny wskaźnik TMDB oparty o aktywność i zainteresowanie użytkowników"))

        # 20 najpopularniejszych filmów 
        top_popular = df.sort_values(
            "popularity", ascending=False
        ).head(20)

        # wykres słupkowy
        chart = alt.Chart(top_popular).mark_bar().encode(
            x=alt.X("popularity:Q", title="Popularność"),
            y=alt.Y("title:N", sort="-x", title="Film"),
            tooltip=[
        alt.Tooltip("title:N", title="Tytuł"),
        alt.Tooltip("popularity:Q", title="Popularność")
        ]
        )

        st.altair_chart(chart, use_container_width=True)

        col1, col2 = st.columns(2)
        col1.metric(
            "Średnia popularność",
            f"{df['popularity'].mean():.1f}",
            help="Średnia popularność filmów w aktualnym zestawie"
        )
        col2.metric(
            "Najpopularniejszy film",
            top_popular.iloc[0]["title"]
        )


    with tab2:
        st.markdown("### Rozkład ocen")

        rating_hist = alt.Chart(df).mark_bar().encode(
            x=alt.X(
                "vote_average:Q",
                bin=alt.Bin(maxbins=10), # ustalenie maksymalnej liczby przedziałów
                title="Ocena"
            ),
            y=alt.Y("count()", title="Liczba filmów"),
            tooltip=[alt.Tooltip("count():Q", title="Liczba filmów")]
        )

        st.altair_chart(rating_hist, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Średnia ocena", f"{df['vote_average'].mean():.2f}")
        col2.metric("Mediana", f"{df['vote_average'].median():.2f}")
        col3.metric(
            "Filmy > 7.5",
            f"{len(df[df['vote_average'] > 7.5])}"
        )


    with tab3:
        st.markdown("### Dominujące gatunki")

        # mapowanie Id gatunków z ich nazwami
        genre_map = {g["id"]: g["name"] for g in genres}

        # gatunki w filmie
        genre_rows = []
        for _, row in df.iterrows():
            for gid in row.get("genre_ids", []):
                genre_rows.append({
                    "Gatunek": genre_map.get(gid, "Inne"),
                    "Film": row["title"]
                })

        genre_df = pd.DataFrame(genre_rows)

        genre_count = (
            genre_df
            .groupby("Gatunek")
            .count()
            .reset_index()
            .rename(columns={"Film": "Liczba filmów"})
            .sort_values("Liczba filmów", ascending=False)
        )

        chart = alt.Chart(genre_count).mark_bar().encode(
            x=alt.X("Liczba filmów:Q"),
            y=alt.Y("Gatunek:N", sort="-x"),
            tooltip=["Gatunek", "Liczba filmów"]
        )

        st.altair_chart(chart, use_container_width=True)

        top_genre = genre_count.iloc[0]
        st.metric(
            "Dominujący gatunek",
            f"{top_genre['Gatunek']} ({top_genre['Liczba filmów']})"
        )
