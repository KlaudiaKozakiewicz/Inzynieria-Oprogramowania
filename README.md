# Inzynieria-Oprogramowania
Projekt z inżynierii oprogramowania 

# Aplikacja do rekomendacji i analizy filmów – Streamlit + TMDB API

Interaktywna aplikacja webowa do **wyszukiwania, analizy i wizualizacji danych filmowych** z wykorzystaniem oficjalnego API serwisu **The Movie Database (TMDB)**.  
Projekt został zrealizowany w celach **edukacyjnych i demonstracyjnych**.

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
- stworzenie czytelnego dashboardu analitycznego,
- demonstracja dobrych praktyk (cache, obsługa braków danych).

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
- **Requests** – komunikacja HTTP
- **TMDB API** – źródło danych filmowych

---

## Źródło danych – TMDB

Projekt korzysta z oficjalnego API serwisu **The Movie Database (TMDB)**:

- Strona TMDB:  
  https://www.themoviedb.org/

- Dokumentacja API:  
  https://developer.themoviedb.org/docs

Dane obejmują m.in.:
- filmy,
- gatunki,
- popularność,
- oceny użytkowników,
- budżety i przychody (jeśli dostępne).

> Uwaga: Nie wszystkie filmy posiadają kompletne dane finansowe – jest to ograniczenie API TMDB.

---

## Struktura projektu

├── main.py                 # Strona główna aplikacji
├── pages/
│   ├── movie.py            # Szczegóły i analiza filmu
│   ├── analysis.py         # Analiza biznesowa
│   ├── what2watch.py       # Wyszukiwanie po filtrach
│   └── recommendations.py  # Rekomendacje
├── requirements.txt
└── README.md



