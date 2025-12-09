# Plan Projektu: Analiza Danych z Funduszy Inwestycyjnych

## Faza 1: Ekstrakcja Danych

### 1.1. Cel
Celem tej fazy jest zautomatyzowane pobranie dwóch kluczowych typów danych ze stron internetowych wybranych Towarzystw Funduszy Inwestycyjnych (TFI): danych ilościowych (notowania) oraz danych jakościowych (dokumenty KID).

### 1.2. Zadania
- **Zadanie 1a: Ekstrakcja Notowań Historycznych**
  - **Opis:** Stworzenie skryptów (np. w Pythonie z użyciem bibliotek `requests` i `BeautifulSoup`/`Scrapy`) do zidentyfikowania i pobrania danych o historycznych notowaniach jednostek uczestnictwa funduszy.
  - **Format wyjściowy:** Pliki `.csv` dla każdego funduszu, zawierające co najmniej datę i cenę zamknięcia.
  - **Kryteria sukcesu:** Pobrane dane z co najmniej 6 ostatnich lat dla każdego analizowanego funduszu.

- **Zadanie 1b: Ekstrakcja Kart Funduszy (KID)**
  - **Opis:** Opracowanie mechanizmu do lokalizowania i pobierania dokumentów typu KID (Key Investor Document) dla każdego funduszu. Zazwyczaj są to pliki `.pdf`.
  - **Format wyjściowy:** Katalog z plikami `.pdf` (lub `.txt` po wstępnym przetworzeniu), jednoznacznie powiązanymi z konkretnym funduszem.
  - **Kryteria sukcesu:** Pobranie aktualnego dokumentu KID dla każdego funduszu z portfolio.

## Faza 2: Analiza i Transformacja Danych

### 2.1. Cel
Przetworzenie zebranych danych w celu wyliczenia kluczowych wskaźników ryzyka i rentowności oraz ustrukturyzowanie informacji zawartych w dokumentach KID przy użyciu modelu językowego.

### 2.2. Zadania
- **Zadanie 2a: Obliczenia Wskaźników Ilościowych**
  - **Opis:** Implementacja algorytmów do analizy szeregów czasowych notowań.
  - **Narzędzia:** Python z bibliotekami `pandas`, `numpy`, `scipy`.
  - **Wskaźniki do obliczenia:**
    1.  **Średnioroczna stopa zwrotu:** Na podstawie danych z ostatnich 6 lat.
    2.  **Value at Risk (VaR):**
        - Metoda symulacji historycznej.
        - Metoda Monte Carlo.
    3.  **Wskaźnik Sharpe'a.**
    4.  **Wskaźnik Sortino.**
    5.  **Estimated Shortfall (Conditional VaR).**
  - **Format wyjściowy:** Tabela lub plik `.json`/`.csv` z obliczonymi metrykami dla każdego funduszu.

- **Zadanie 2b: Analiza Jakościowa Kart Funduszy z Użyciem Gemini**
  - **Opis:** Wykorzystanie API Gemini do przetworzenia treści dokumentów KID. Celem jest ekstrakcja i standaryzacja kluczowych informacji o polityce inwestycyjnej.
  - **Proces:**
    1.  Przygotowanie promptu dla Gemini, który precyzyjnie definiuje, jakie informacje mają zostać wyodrębnione.
    2.  Przesłanie treści każdego dokumentu KID do API.
    3.  Odebranie i zapisanie ustrukturyzowanych danych.
  - **Struktura danych wyjściowych (dla każdego funduszu):**
    - `zakres_oferty`:
      - `rodzaje_funduszy`: Lista dostępnych typów (np. "akcyjny", "obligacyjny", "mieszany").
      - `ekspozycja_na_ryzyko`: Opis lub kategoria (np. "agresywny", "stabilnego wzrostu", "hedgingowy").
      - `pokrycie_geograficzne`: Lista lub opis (np. ["Polska", "Europa Wschodząca", "rynki rozwinięte"]).
      - `pokrycie_sektorowe`: Opis i flaga `czy_sektor_zbrojeniowy` (true/false).
      - `wykorzystywane_instrumenty`: Lista lub opis (np. ["akcje", "obligacje skarbowe", "instrumenty pochodne"]).
  - **Format wyjściowy:** Plik `.json` zawierający ustrukturyzowane dane dla wszystkich funduszy.

## Faza 3: Wizualizacja i Raportowanie (Opcjonalnie)

### 3.1. Cel
Prezentacja wyników analizy w przystępnej formie.

### 3.2. Zadania
- Stworzenie dashboardu (np. przy użyciu `Streamlit`, `Dash` lub `Tableau`) prezentującego ranking funduszy według wybranych metryk.
- Generowanie automatycznych raportów podsumowujących analizę ilościową i jakościową.
