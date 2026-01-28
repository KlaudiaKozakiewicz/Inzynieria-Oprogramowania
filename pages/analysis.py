import streamlit as st
import requests
import pandas as pd
import os

API_KEY = os.getenv("TMDB_API_KEY")

st.set_page_config(
    page_title="Analiza biznesowa",
    layout="wide"
)

st.title("Analiza biznesowa filmów")

# ===================== INICJALIZACJA ST STATE =====================
if "movies" not in st.session_state:
    st.session_state["movies"] = []

if "loading_movies" not in st.session_state:
    st.session_state["loading_movies"] = False


# ================== POBIERANIE GATUNKÓW =============
@st.cache_data
def fetch_genres():
    r = requests.get(
        "https://api.themoviedb.org/3/genre/movie/list",
        params = {"api_key": API_KEY, "language": "pl-PL"}
    )
    return r.json()["genres"]

# nazwa -> id
genres = fetch_genres()
GENRE_NAME_TO_ID = {
    g["name"]: g["id"] for g in genres
}

# ================== POBIERANIE FILMÓW =====================
def fetch_movies(genre_id=None):
    """Pobiera topowe filmy lub filmy dla wybranego gatunku"""
    params = {
        "api_key": API_KEY,
        "language": "pl-PL",
        "sort_by": "popularity.desc",
        "vote_average.gte": 6.5,
        "page": 1
    }
    if genre_id:
        params["with_genres"] = str(genre_id)

    r = requests.get("https://api.themoviedb.org/3/discover/movie", params=params)
    return r.json().get("results", [])



# ===================== WIDOK WYBORU GATUNKU =====================
selected_genres = st.multiselect(
    "🎞 Gatunek",
    list(GENRE_NAME_TO_ID.keys()),
    help="Wybierz jeden lub kilka gatunków, aby filtrować filmy",
    placeholder="Gatunek"
)



# ===================== POBIERANIE DANYCH DO ANALIZY =====================
# jeśli wybrano gatunek, pobieramy filmy dla tego gatunku
if selected_genres:
    movies_for_analysis = []
    for g_name in selected_genres:
        g_id = GENRE_NAME_TO_ID[g_name]
        movies_for_analysis.extend(fetch_movies(g_id))
    st.session_state["movies"] = movies_for_analysis
    # jeśli brak wyboru gatunku, używamy domyślnej listy popularnych filmów
if not st.session_state["movies"]:
    st.session_state["movies"] = fetch_movies()

movies = st.session_state["movies"]

if not movies:
    st.warning("Brak filmów do analizy.")
    st.stop()

# ===================== FINANSE =====================
@st.cache_data(ttl=3600)
def fetch_movie_financials(movie_id):
    r = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}",
                     params={"api_key": API_KEY})
    data = r.json()
    return data.get("budget", 0), data.get("revenue", 0)

analysis_data = []
MAX_MOVIES = 20

with st.spinner("Pobieranie danych finansowych..."):
    for m in movies:
        budget, revenue = fetch_movie_financials(m["id"])
        if budget <= 0 or revenue <= 0:
            continue
        roi = (revenue - budget) / budget
        analysis_data.append({
            "Tytuł": m["title"],
            "Budżet": budget,
            "Przychody": revenue,
            "ROI": roi
        })
        if len(analysis_data) == MAX_MOVIES:
            break

df = pd.DataFrame(analysis_data)

if df.empty:
    st.warning("Brak danych finansowych.")
    st.stop()

# ===================== METRYKI =====================
col1, col2, col3 = st.columns(3)
col1.metric("Średni budżet", f"${df['Budżet'].mean():,.0f}")
col2.metric("Średnie przychody", f"${df['Przychody'].mean():,.0f}")
col3.metric("Filmy dochodowe", f"{len(df[df['ROI'] > 0])} / {len(df)}",
            help="Liczba filmów, których przychody były wyższe niż budżet (ROI > 0)")

st.divider()

# ===================== WYKRESY =====================
st.subheader("Budżet vs Przychody")
st.bar_chart(df.set_index("Tytuł")[["Budżet", "Przychody"]])

st.subheader("ROI")
st.bar_chart(df.set_index("Tytuł")["ROI"])

st.subheader("Dane szczegółowe")
st.dataframe(
    df.style.format({
        "Budżet": "${:,.0f}",
        "Przychody": "${:,.0f}",
        "ROI": "{:.2f}"
    }),
    use_container_width=True
)

st.divider()


# ============ Powrót ================
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



