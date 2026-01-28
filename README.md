# Inzynieria-Oprogramowania
Projekt z inżynierii oprogramowania 

# CineMate: Aplikacja do rekomendacji i analizy popularności filmów

Interaktywna aplikacja webowa do **wyszukiwania, analizy i wizualizacji danych filmowych** z wykorzystaniem oficjalnego API serwisu **The Movie Database (TMDB)**.  
Projekt został zrealizowany w celach **edukacyjnych i demonstracyjnych**.

Aplikacja została opublikowana w chmurze Streamlit Cloud i jest dostępna online adresem:

<https://inzynieria-oprogramowania-k4grvgfz3appppcnhaqvdndw.streamlit.app/>

---

## Opis projektu

Celem projektu jest stworzenie aplikacji webowej umożliwiającej **pobieranie, przetwarzanie oraz prezentowanie danych filmowych** pochodzących z serwisu **The Movie Database (TMDB)** za pomocą oficjalnego interfejsu API.

Aplikacja pozwala użytkownikom:
- wyszukiwać filmy po tytule,
- przeglądać rankingi popularnych, najlepiej ocenianych i najnowszych filmów,
- filtrować filmy według gatunków,
- analizować dane statystyczne (popularność, oceny, liczba głosów),
- przeprowadzać **podstawowe analizy biznesowe** (budżet, przychody, ROI),
- otrzymywać rekomendacje filmów na podstawie wybranego tytułu lub gatunku.

Projekt ma charakter **edukacyjny**, pokazując:
- integrację z zewnętrznym API,
- przetwarzanie danych w Pythonie,
- wizualizację danych,
- budowę wielostronicowej aplikacji webowej.

---

## Cele projektu

- nauka pracy z REST API (TMDB),
- praktyczne wykorzystanie biblioteki **Streamlit**,
- analiza i wizualizacja danych filmowych,
- prezentacja wskaźników popularności i prostych metryk biznesowych,
- stworzenie czytelnego dashboardu analitycznego.

---

## Źródło danych – TMDB

Projekt korzysta z oficjalnego API serwisu **The Movie Database (TMDB)**:

- Strona TMDB:  
  <https://www.themoviedb.org/>

- Dokumentacja API:  
  <https://developer.themoviedb.org/docs>

Dane obejmują m.in.:
- filmy,
- gatunki,
- popularność,
- oceny użytkowników,
- budżety i przychody (jeśli dostępne).

> Uwaga: Nie wszystkie filmy posiadają kompletne dane finansowe – jest to ograniczenie API TMDB.

---

## Funkcjonalności

### Wyszukiwanie filmów
- wyszukiwanie po tytule z podpowiedziami (autocomplete),
- sortowanie wyników według popularności.

### Rankingi filmów
- Najwyżej oceniane
- Popularne
- Nowości
- filtrowanie według gatunków.

### Dashboard analityczny
- popularność filmów (wykresy słupkowe),
- rozkład ocen,
- dominujące gatunki,
- metryki statystyczne (średnia, mediana).

### Analiza biznesowa
- budżet vs przychody,
- obliczanie ROI (Return on Investment),
- porównanie filmów w obrębie gatunku.

### Szczegóły filmu
- plakat, opis, czas trwania,
- ocena i liczba głosów,
- analiza popularności na tle podobnych filmów,
- rekomendacje na podstawie gatunków.

---

## Wykorzystane technologie

- **Python 3**
- **Streamlit** – interfejs webowy
- **Pandas** – przetwarzanie danych
- **Altair** – wizualizacja danych
- **Streamlit Searchbox** - Autocomplete wyszukiwania filmów w UI
- **Requests** – komunikacja HTTP
- **OS** - Obsługa zmiennych środowiskowych (TMDB API key)
- **TMDB API** – źródło danych filmowych

---

## Struktura projektu

```text
Inżynieria-Oprogramownia/
├── main.py          # Strona główna aplikacji
├── .streamlit/
    ├── config.toml         # Color theme
├── pages/
    ├── analysis.py         # Strona z analizami
    ├── movie.py            # Strona wybranego filmu
    ├── recommendations.py  # Strona z rekomendacjami
    ├── what2watch.py
├── requirements.txt
├── .gitignore        # lista plików, które GitHub ma ignorować
├── Streamlit.pdf     # Prezentacja streamlit      
└── README.md     
```
---

## Wymagania

Aby zaimportować biblioteki potrzebne do lokalnego otworzenia projektu, należy wykonać polecenie
```sh
pip install -r requirements.txt
```

