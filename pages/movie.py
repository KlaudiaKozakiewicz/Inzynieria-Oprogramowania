import streamlit as st
import requests
import pandas as pd
import altair as alt # biblioteka wykresów
import os

API_KEY = os.getenv("TMDB_API_KEY")

# Aplikacja korzysta z danych TMDB API, ale nie jest oficjalnie powiązana z TMDB.

# Ukrycie paska bocznego
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header > div:nth-of-type(1) {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Ustawienia strony
st.set_page_config(page_title="Film", page_icon="🎬", layout="wide")

# Wyszukanie filmu na podstawie ID
query_params = st.query_params
movie_id = query_params.get("id")

if not movie_id:
    st.error("Brak ID filmu")
    st.stop()

# Funkcja pobierająca szczegóły filmu
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

# Funkcja znajdująca słowa kluczowe dla filmu
@st.cache_data(ttl=3600)
def get_movie_keywords(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}/keywords",
        params={"api_key": API_KEY}
    )
    return r.json().get("keywords", [])

# Funkcja do odczytania gatunków
@st.cache_data(ttl=3600)
def fetch_genres():
    r = requests.get(
        "https://api.themoviedb.org/3/genre/movie/list",
        params = {"api_key": API_KEY, "language": "pl-PL"}
    )
    return r.json()["genres"]

# Funkcja do odczytania czasu trwania filmu
@st.cache_data(ttl=3600)
def get_runtime(movie_id):
    r = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}",
        params={"api_key": API_KEY}
    )
    return r.json().get("runtime", 0)

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
            details = fetch_movie_details(m['id'])
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

# Pobranie szczegółów filmu
movie = fetch_movie_details(movie_id)
# Stworzenie słownika gatunek: ID
genre_name_to_id = get_genre_ids()
# Lista ID gatunków
movie_genre_ids = [genre_name_to_id[g['name']] for g in movie.get('genres', []) if g['name'] in genre_name_to_id]


## Wyświetlanie informacji o filmie:

st.title(movie["title"], text_alignment="center")

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


st.divider()

# Przycisk do wyboru rekomendacji lub analizy
selected_tab = st.pills(options=["Rekomendacje na podstawie filmu", "Analiza"], 
         label="Wybierz opcję:", default="Rekomendacje na podstawie filmu",
         width="stretch")


# Pobranie gatunków
genres = fetch_genres()

st.divider()

# Wyświetlenie 10 rekomendowanych filmów
if selected_tab == "Rekomendacje na podstawie filmu":
    language_code = movie.get('spoken_languages', [{}])[0].get('iso_639_1')
    candidate_movies = get_movies_by_genres(movie_genre_ids, language=language_code, n=10)

    recommendations = custom_recommendations(movie, candidate_movies, top_n=10)

    for score, rec, common_genres, common_keywords in recommendations:
        col1, div, col2 = st.columns([1, 0.2, 4])
        st.markdown("<hr style='border: 0.5px solid #ddd; margin-top: 4px; margin-bottom: 30px;'>",
                    unsafe_allow_html=True)
        with col1:
            if rec.get('poster_path'):
                st.image(f"https://image.tmdb.org/t/p/w200{rec['poster_path']}")
        with div:
            st.markdown("<div style='border-left:1px solid #ddd; height:100%;'></div>", unsafe_allow_html=True) 
        with col2:
            st.markdown(f"<h3>{rec['title']} ({rec.get('release_date','')[:4]})</h3>", unsafe_allow_html=True)
            st.markdown("<hr style='border: 0.5px solid #ddd; margin-top: 4px; margin-bottom: 30px;'>",
                    unsafe_allow_html=True)
            st.write(f"*Ocena:* {rec.get('vote_average', '–')} ({movie.get('vote_count', '–')} głosów)")
            st.write(f"*Wspólne gatunki:* {', '.join(common_genres) or '–'}")
            st.write(f"*Wspólne słowa kluczowe:* {', '.join(list(common_keywords)[:5]) or '–'}")
            if st.button("Zobacz szczegóły", key=f"details_{rec['id']}"):
                st.switch_page("pages/movie.py", query_params={"id": rec["id"]})
        
                

# Analizy 
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
            alt.value("#5d2266"),  # ciemnofioletowy
            alt.value("#9b6dc6")   # jasnofioletowy
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
        range=["#5d2266", "#9b6dc6"]
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



# Przycisk powrotu do menu 
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
