import streamlit as st
from streamlit_searchbox import st_searchbox
import requests
from datetime import datetime
import os

API_KEY = os.getenv("TMDB_API_KEY")

# Aplikacja korzysta z danych TMDB API, ale nie jest oficjalnie powiązana z TMDB.

# Ustawienia strony
st.set_page_config(page_title="Co obejrzeć?", page_icon="🎬", layout="wide")

st.title("🎬 Co obejrzeć?", text_alignment="center")
st.caption("Wyszukaj film na podstawie filtrów.", text_alignment="center")

# Ukrycie paska bocznego
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header > div:nth-of-type(1) {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

### Funkcje

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

# Funkcja do wyszukania aktorów
@st.cache_data(ttl=3600)
def search_actors(query):
    if not query or len(query) < 1:
        return []

    r = requests.get(
        "https://api.themoviedb.org/3/search/person",
        params={
            "api_key": API_KEY,
            "query": query,
            "language": "pl-PL",
            "page": 1
        }
    )

    results = r.json().get("results", [])

    # sortuj po popularności
    results = sorted(
        results,
        key=lambda x: x.get("popularity", 0),
        reverse=True
    )

    names = []
    for a in results[:50]:
        name = a["name"]
        names.append(name)
        st.session_state.actor_name_to_id[name] = a["id"]
    
    return names

# Funkcja do wyszukania obsady technicznej
@st.cache_data(ttl=3600)
def search_crew(query):
    if not query or len(query) < 1:
        return []

    r = requests.get(
        "https://api.themoviedb.org/3/search/person",
        params={
            "api_key": API_KEY,
            "query": query,
            "language": "pl-PL",
            "page": 1
        }
    )

    results = r.json().get("results", [])

    # tylko osoby z OBSADY TECHNICZNEJ
    results = [
        p for p in results
        if p.get("known_for_department") != "Acting"
    ]

    results = sorted(results, key=lambda x: x.get("popularity", 0), reverse=True)

    names = []
    for p in results[:50]:
        name = p["name"]
        names.append(name)
        st.session_state.crew_name_to_id[name] = p["id"]

    return names

# Funkcja do wyszukania słów kluczowych
@st.cache_data(ttl=3600)
def search_keywords(query):
    if not query or len(query) < 1:
        return []  # albo top 50 najpopularniejszych keywords jeśli masz listę

    r = requests.get(
        "https://api.themoviedb.org/3/search/keyword",
        params={
            "api_key": API_KEY,
            "query": query,
            "page": 1
        }
    )

    results = r.json().get("results", [])
    results = sorted(results, key=lambda x: x.get("movie_count", 0), reverse=True)  # sortuj po popularności w filmach

    names = []
    for k in results[:50]:
        name = k["name"]
        names.append(name)
        st.session_state.keyword_name_to_id[name] = k["id"]

    return names

# Funkcja do wyszukania filmów na podstawie filtrów
@st.cache_data(ttl=600)
def search_movies(genre_ids, year_from, year_to, runtime, min_rating, min_vote_count, language,
                  actors, crew, keywords, excluded_keywords, popular_only, adult_only, trending, 
                  time_window, new_releases, page=1):
    params = {
        "api_key": API_KEY,
        "language": "pl-PL",
        "page": 1,
        "vote_average.gte": min_rating,
        "vote_count.gte": min_vote_count,
        "include_adult": adult_only,
        "sort_by": "popularity.desc"
    }

    url = "https://api.themoviedb.org/3/discover/movie"
    
    if trending:
        url = f"https://api.themoviedb.org/3/trending/movie/{time_window}"
        params.pop("sort_by", None)

    # sortowanie
    if popular_only:
        params["sort_by"] = "popularity.desc"
    else:
        params["sort_by"] = "vote_average.desc"

    # nowości
    if new_releases:
        today = datetime.date.today()
        thirty_days_ago = today - datetime.timedelta(days=30)
        params["primary_release_date.gte"] = thirty_days_ago
        params["primary_release_date.lte"] = today
    else:
        params["primary_release_date.gte"] = f"{year_from}-01-01"
        params["primary_release_date.lte"] = f"{year_to}-12-31"

    # gatunki
    if genre_ids:
        params["with_genres"] = ",".join(map(str, genre_ids))

    # język
    if language:
        params["with_original_language"] = language

    # aktorzy
    if actors:
        params["with_cast"] = ",".join(map(str, actors))

    # obsada techniczna
    if crew:
        params["with_crew"] = ",".join(map(str, crew))

    # słowa kluczowe
    if keywords:
        params["with_keywords"] = ",".join(map(str, keywords))

    if excluded_keywords:
        params["without_keywords"] = ",".join(map(str, excluded_keywords))

    if runtime:
        params["with_runtime.gte"] = runtime[0]
        params["with_runtime.lte"] = runtime[1]

    params["page"] = page

    r = requests.get(url, params=params)
    return r.json().get("results", [])[:20]


# Pobranie gatunków (słowniki)
genres = fetch_genres()
# Zamiana słownika w format name : id
GENRE_NAME_TO_ID = {g["name"]: g["id"] for g in genres}


## Ustawienie stanów:

# Aktorzy
if "selected_actors" not in st.session_state:
    st.session_state.selected_actors = []

if "actor_name_to_id" not in st.session_state:
    st.session_state.actor_name_to_id = {}

if "actor_search_key" not in st.session_state:
    st.session_state.actor_search_key = 0


# Obsada techniczna
if "selected_crew" not in st.session_state:
    st.session_state.selected_crew = []

if "crew_name_to_id" not in st.session_state:
    st.session_state.crew_name_to_id = {}

if "crew_search_key" not in st.session_state:
    st.session_state.crew_search_key = 0


# Słowa kluczowe
if "selected_keywords" not in st.session_state:
    st.session_state.selected_keywords = []

if "keyword_name_to_id" not in st.session_state:
    st.session_state.keyword_name_to_id = {}

if "keyword_search_key" not in st.session_state:
    st.session_state.keyword_search_key = 0


# Słowa wykluczone
if "excluded_keywords" not in st.session_state:
    st.session_state.excluded_keywords = []

if "excluded_keyword_name_to_id" not in st.session_state:
    st.session_state.excluded_keyword_name_to_id = {}

if "excluded_keyword_search_key" not in st.session_state:
    st.session_state.excluded_keyword_search_key = 0


# Minimalna liczba głosów
if "min_vote_count" not in st.session_state:
    st.session_state.min_vote_count = 0

# Przycisk dla nowości
if "new_releases_toggle" not in st.session_state:
    st.session_state.new_releases_toggle = False

# Wyszukiwanie
if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "search_clicked" not in st.session_state:
    st.session_state.search_clicked = False

if "search_page" not in st.session_state:
    st.session_state.search_page = 1


# Słownik języków
LANG_PL_TO_CODE = {
    "Wszystkie języki": None,

    "Angielski": "en",
    "Hiszpański": "es",
    "Francuski": "fr",
    "Niemiecki": "de",
    "Włoski": "it",
    "Portugalski": "pt",
    "Rosyjski": "ru",
    "Japoński": "ja",
    "Koreański": "ko",
    "Chiński": "zh",
    "Hindi": "hi",

    "Arabski": "ar",
    "Turecki": "tr",
    "Holenderski": "nl",
    "Szwedzki": "sv",
    "Norweski": "no",
    "Duński": "da",
    "Fiński": "fi",
    "Polski": "pl",
    "Czeski": "cs",
    "Węgierski": "hu",

    "Grecki": "el",
    "Hebrajski": "he",
    "Perski": "fa",
    "Tajski": "th",
    "Wietnamski": "vi",
    "Indonezyjski": "id",
    "Malajski": "ms",
    "Filipiński": "tl",

    "Rumuński": "ro",
    "Bułgarski": "bg",
    "Serbski": "sr",
    "Chorwacki": "hr",
    "Słoweński": "sl",
    "Ukraiński": "uk",
    "Litewski": "lt",
    "Łotewski": "lv",
    "Estoński": "et",

    "Islandzki": "is",
    "Irlandzki": "ga",
    "Walijski": "cy",
    "Kataloński": "ca",
    "Baskijski": "eu",
}


### Wyświetlanie filtrów

col1, div1, col2, div2, col3 = st.columns([4, 0.5, 4,0.5, 4])
with col1:
    genre_names = st.multiselect("Gatunek", list(GENRE_NAME_TO_ID.keys()),
                                 help="Wybierz jeden lub kilka gatunków, aby filtrować filmy",
                                 placeholder = "Gatunek")

with div1:
        st.markdown("<div style='border-left:1px solid #ddd; height:100%;'></div>",
                        unsafe_allow_html=True)    
        
with col2:
    year_from, year_to = st.slider("Rok wydania", min_value=1940, max_value=2026, value=(2016, 2026), step=1,
                                   help="Wybierz zakres lat wydania filmu",
                                   disabled=st.session_state.new_releases_toggle) # wyłączone, jeśli wybrano opcję "nowości'

with div2:
    st.markdown("<div style='border-left:1px solid #ddd; height:100%;'></div>",
                    unsafe_allow_html=True) 

with col3:
    min_rating = st.slider("Minimalna ocena", min_value=0.0, max_value=10.0, 
                           value=6.5, step=0.5)
    

col4, div3, col5, div4, col6 = st.columns([4, 0.5, 4,0.5, 4])
with col4:
    selected_lang_label = st.selectbox("Język", options=list(LANG_PL_TO_CODE.keys()),
                                       help="Wybierz język oryginalny filmu (możesz wrócić do wszystkich)")
    selected_language_code = LANG_PL_TO_CODE[selected_lang_label] # Zamiana kodu na nazwę języka

with div3:
    st.markdown("<div style='border-left:1px solid #ddd; height:100%;'></div>",
                    unsafe_allow_html=True)    

with col5:
    runtime = st.slider("Czas trwania filmu", 0, 400, (60, 240),
                        help="Dostosuj minimalny i maksymalny czas trwania filmu.")

with div4:
    st.markdown("<div style='border-left:1px solid #ddd; height:100%;'></div>",
                    unsafe_allow_html=True)       

with col6:
    st.session_state.min_vote_count = st.slider("Minimalna liczba głosów", min_value=0, max_value=5000,
                                                value=1000, step=50,
                                                help="Filmy z mniejszą liczbą ocen mogą być mniej wiarygodne")
         
with st.expander("Filtry dodatkowe"):

    col7, col8, col9, col10 = st.columns(4)

    with col7:
        popular_only = st.toggle("Tylko popularne filmy", help="Filmy oznaczane jako popularne oceniane są na podstawie aktywności użytkowników")
        
    with col8:
        adult_only = st.toggle("Tylko filmy z ograniczeniem wiekowym (18+)")
        
    with col9:
        trending = st.toggle("Tylko trending", help="'Trending' odnosi się do popularności dziennej lub tygodniowej")

        if trending:
            time_window = st.radio("Wybierz okres:", ["Dzisiaj", "W tym tygodniu"], horizontal=True)
        else:
            time_window = None

    with col10:
        new_releases = st.toggle("Tylko nowości", key="new_releases_toggle",
                                 help="Jeśli włączone, pokażą się tylko filmy premierowe w ostatnich 30 dniach") 
        
    st.divider()

    col_left, col_divider, col_right = st.columns([4, 0.5, 4])

    with col_left:
        st.markdown("<h5 style='text-align: center;'>Obsada</h5>",
                    unsafe_allow_html=True)
        
        col11, col12 = st.columns(2)

        with col11:
            st.markdown("Aktor", text_alignment="center")

            new_actor = st_searchbox(search_actors, placeholder= "Wpisz imię lub nazwisko aktora...",
                                     key=f"actor_search_{st.session_state.actor_search_key}")

            if new_actor and new_actor not in st.session_state.selected_actors:
                st.session_state.selected_actors.append(new_actor)
                st.session_state.actor_search_key += 1
                st.rerun()

            if st.session_state.selected_actors:
                actor_to_remove = st.pills(label="Wybrani aktorzy:", options=st.session_state.selected_actors,
                                           key="selected_actors_pills", help="Kliknij aktora, aby go usunąć")
                if actor_to_remove:
                    st.session_state.selected_actors.remove(actor_to_remove)
                    st.rerun()

        with col12:
            st.markdown("Obsada techniczna", text_alignment="center")

            new_crew = st_searchbox(search_crew,
                                    placeholder="Wpisz imię lub nazwisko (reżyser, scenarzysta, producent...)",
                                    key=f"crew_search_{st.session_state.crew_search_key}")

            if new_crew and new_crew not in st.session_state.selected_crew:
                st.session_state.selected_crew.append(new_crew)
                st.session_state.crew_search_key += 1
                st.rerun()

            if st.session_state.selected_crew:
                selected_to_remove = st.pills("Wybrana obsada techniczna", st.session_state.selected_crew,
                                              help="Kliknij nazwisko, aby je usunąć", key="selected_crew_pills")
                if selected_to_remove:
                    st.session_state.selected_crew.remove(selected_to_remove)
                    st.rerun()

            if len(st.session_state.selected_crew) > 1:
                st.warning("Wybranie kilku osób z obsady technicznej może znacząco ograniczyć liczbę wyników.")

    with col_divider:
        st.markdown("<div style='border-left:1px solid #ddd; height:100%;'></div>",
                    unsafe_allow_html=True)

    with col_right:
        st.markdown("<h5 style='text-align: center;'>Słowa kluczowe</h5>",
                    unsafe_allow_html=True)
        
        col13, col14 = st.columns(2)

        with col13:
            st.markdown("Uwzględnij słowa:", text_alignment="center")
            new_keyword = st_searchbox(search_keywords,
                                       placeholder="Np. ogre, time travel...",
                                       key=f"keyword_search_{st.session_state.keyword_search_key}")

            if new_keyword and new_keyword not in st.session_state.selected_keywords:
                st.session_state.selected_keywords.append(new_keyword)
                st.session_state.keyword_search_key += 1
                st.rerun()

            if st.session_state.selected_keywords:
                to_remove = st.pills("Wybrane słowa kluczowe:", st.session_state.selected_keywords,
                                     help="Kliknij, aby usunąć", key="selected_keywords_pills")
                if to_remove:
                    st.session_state.selected_keywords.remove(to_remove)
                    st.rerun()
        
        with col14:
            st.markdown("Nie względniaj słów:", text_alignment="center")
            exclude_keyword = st_searchbox(search_keywords, placeholder="Np. sequel, remake, superhero...",
                                           key=f"exclude_keyword_search_{st.session_state.excluded_keyword_search_key}")

            if exclude_keyword and exclude_keyword not in st.session_state.excluded_keywords:
                st.session_state.excluded_keywords.append(exclude_keyword)
                st.session_state.excluded_keyword_search_key += 1
                st.rerun()

            if st.session_state.excluded_keywords:
                to_remove = st.pills("Wykluczone słowa:", st.session_state.excluded_keywords,
                                     help="Kliknij, aby usunąć", key="excluded_keywords_pills")
                if to_remove:
                    st.session_state.excluded_keywords.remove(to_remove)
                    st.rerun()
 
        conflicting_keywords = set(st.session_state.selected_keywords) & set(st.session_state.excluded_keywords)

        if conflicting_keywords:
            st.warning("Te same słowa kluczowe są jednocześnie wybrane i wykluczone: " + ", ".join(conflicting_keywords))


genre_ids = [GENRE_NAME_TO_ID[g] for g in genre_names]
        
selected_actor_ids = [
    st.session_state.actor_name_to_id[name]
    for name in st.session_state.selected_actors
    if name in st.session_state.actor_name_to_id
]

selected_keyword_ids = [
    st.session_state.keyword_name_to_id[name]
    for name in st.session_state.selected_keywords
    if name in st.session_state.keyword_name_to_id
]

excluded_keyword_ids = [
    st.session_state.excluded_keyword_name_to_id[name]
    for name in st.session_state.excluded_keywords
    if name in st.session_state.excluded_keyword_name_to_id
]

# Zamiana wartości dla 'time_window'
time_window_dict = {"Dzisiaj": "day", "W tym tygodniu": "week"}
time_window_new = time_window_dict.get(time_window) if time_window else "day"

if st.button("Szukaj", use_container_width=True):
    st.session_state.search_page = 1
    st.session_state.search_results = search_movies(
        genre_ids=genre_ids,
        year_from=year_from,
        year_to=year_to,
        runtime=runtime,
        min_rating=min_rating,
        min_vote_count=st.session_state.min_vote_count,
        language=selected_language_code,
        actors=selected_actor_ids,
        crew=[st.session_state.crew_name_to_id[n] for n in st.session_state.selected_crew],
        keywords=selected_keyword_ids,
        excluded_keywords=excluded_keyword_ids,
        popular_only=popular_only,
        adult_only=adult_only,
        trending=trending,
        time_window=time_window_new,
        new_releases=st.session_state.new_releases_toggle,
        page=st.session_state.search_page
    )

    st.session_state.search_clicked = True


if st.session_state.search_clicked:
    if st.session_state.search_results:
        st.subheader("Wyniki wyszukiwania", text_alignment="center")

        st.markdown(
                "<hr style='border: 0.5px solid #ddd; margin-top: 4px; margin-bottom: 20px;'>",
                unsafe_allow_html=True
            )

        for movie in st.session_state.search_results:
            col1, col2 = st.columns([1, 4])
            with col1:
                if movie.get("poster_path"):
                    st.image(f"https://image.tmdb.org/t/p/w200{movie['poster_path']}")
            with col2:
                # Tytuł
                st.markdown(f"### {movie.get('title', 'Brak tytułu')}")

                # Gatunki
                movie_genres = [g['name'] for g in genres if g['id'] in movie.get('genre_ids', [])]
                if movie_genres:
                    st.markdown("**Gatunki:** " + ", ".join(movie_genres))

                # Ocena i liczba głosów
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
                st.markdown(f"<p style='text-align: justify; font-size:0.85rem;'>{overview}</p>", unsafe_allow_html=True)

            if st.button("Zobacz szczegóły", width="stretch", key=f"movie_{movie['id']}"):
                        st.switch_page("pages/movie.py", query_params={"id": movie["id"]})

            st.divider()

    else:
        st.warning("Nie znaleziono filmów dla wybranych filtrów.")



# Przycisk powrotu do strony głównej
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
