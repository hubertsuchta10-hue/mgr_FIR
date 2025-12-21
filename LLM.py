import os
import sys
from pathlib import Path
import argparse
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

#sposób odpalenia kodu: python /Users/hubert/Desktop/mgr_FIR/LLM.py "/Users/hubert/Desktop/mgr_FIR/Pekao" --max_files 3
#sposób odpalenia kodu: python /Users/hubert/Desktop/mgr_FIR/LLM.py "/Users/hubert/Desktop/mgr_FIR/PKO"
# ---------- JEDEN, PŁASKI SCHEMAT ---------- #zmieniam
# double check - czy jest tak jak w karcie funduszu
# predefiniowana lista pól do wyciągnięcia z karty funduszu

class FundcardFlat(BaseModel):

# =========================================================
# 1. IDENTYFIKACJA FUNDUSZU
# =========================================================

    nazwa_funduszu: str = Field(
        description="Pełna, dokładna nazwa subfunduszu przepisana z nagłówka karty funduszu. "
        "Nie skracaj, nie parafrazuj, nie dodawaj nazwy TFI. "
        "Musi odpowiadać 1:1 nazwie podanej w karcie."
    )

    towarzystwo: Literal[
    "PKO TFI",
    "Santander TFI",
    "Pekao TFI"] = Field(
        description="Podmiot zarządzający (TFI), np. 'PKO TFI', 'Santander TFI', 'Pekao TFI'. "
        "Ustalany na podstawie logotypu, stopki lub strony tytułowej karty funduszu."
    )

    kategoria_funduszu: Optional[str] = Field(
        description=(
            "Deklaratywna kategoria funduszu podana przez TFI, opisująca charakter strategii "
        "lub grupę docelową produktu. Może zawierać tematy i etykiety takie jak: "
        "akcyjny rynków zagranicznych, obligacji wysokodochodowych, fundusz cyklu życia, "
        "zdefiniowanej daty, PPK, absolutnej stopy zwrotu. "
        "Pole to NIE określa struktury aktywów i NIE zastępuje typu funduszu."
        )
    )

    typ_funduszu: Literal["akcyjny", "dłużny", "mieszany"] = Field(
        description=(
            "Typ funduszu wynikający z dominującej klasy aktywów "
            "(akcyjny / dłużny / mieszany). "
            "PPK i cykl życia NIE są typem funduszu."
        )
    )

    forma_prawna: Optional[Literal["FIO", "SFIO"]] = Field(
        description="Forma prawna funduszu (FIO lub SFIO), jeśli wskazana w karcie funduszu."
    )

    parasolowy: Literal["tak", "nie"] = Field(
        description=(
            "Czy fundusz jest subfunduszem w ramach funduszu parasolowego, "
            "zgodnie z informacją z karty funduszu."
        )
    )

    czy_PPK: Literal["tak", "nie"] = Field(
        description=(
            "Czy fundusz jest częścią programu PPK. "
        "Ustaw 'tak' WYŁĄCZNIE jeśli karta funduszu wprost zawiera frazę 'PPK'. "
        "Fundusze cyklu życia lub zdefiniowanej daty NIE są automatycznie funduszami PPK."
        )
    )

    data_publikacji: Optional[str] = Field(
        description="Data publikacji karty funduszu w formacie YYYY-MM-DD. "
        "Jeżeli występuje w formacie dziennym (np. 31.10.2025), należy ją przekonwertować."
    )

    # =========================================================
    # 2. OGÓLNY WSKAŹNIK RYZYKA
    # =========================================================

    ogolny_wskaznik_ryzyka: Optional[
        Literal[1, 2, 3, 4, 5, 6, 7]
    ] = Field(
        description=(
            "Ogólny wskaźnik ryzyka SRI (1–7) prezentowany w karcie funduszu, zwykle "
        "w formie graficznej skali lub w opisie. Należy wybrać wyłącznie liczbę, "
        "która jest oznaczona jako ryzyko funduszu. "
        "1 oznacza najniższe ryzyko, 7 najwyższe. "
        "Jeżeli karta funduszu nie podaje wskaźnika → null."
        )
    )

    # =========================================================
    # 3. DANE OGÓLNE
    # =========================================================

    aktywa_netto_mln: Optional[float] = Field(
        description="Aktywa netto funduszu w mln zł. "
        "Należy zamienić zapis '773,98 mln PLN' na wartość float 773.98."
    )

    cena_jednostki: Optional[float] = Field(
        description="Aktualna cena jednostki uczestnictwa, wyrażona jako liczba zmiennoprzecinkowa."
    )

    minimalna_wplata_pierwsza: Optional[float] = Field(
        description="Minimalna pierwsza wpłata do funduszu, zgodnie z kartą funduszu."
    )

    data_pierwszej_wyceny: Optional[str] = Field(
        description="Data pierwszej wyceny funduszu (YYYY-MM-DD)."
    )

    sugerowany_czas_inwestycji_lata: Optional[int] = Field(
        description="Minimalny sugerowany czas inwestycji wyrażony w latach. "
        "LLM powinien wyciągnąć liczbę z fraz typu: 'co najmniej 5 lat', 'min. 3 lata'."
    )

    # =========================================================
    # 4. OPŁATY
    # =========================================================

    oplata_za_zarzadzanie: Optional[float] = Field(
        description="Roczna opłata za zarządzanie wyrażona w procentach, którą należy "
        "zawsze konwertować na format dziesiętny typu float: np. 3% zapisz jako 0.03, 2.5% zapisz jako 0.025. "
        "Jeżeli w karcie funduszu podano zakres lub wartość maksymalną "
        "(np. 'maksymalnie 4%'), należy użyć liczby podanej w karcie i przeliczyć ją "
        "na format dziesiętny. "
        "Jeżeli informacja nie występuje w karcie funduszu → null. "
        "LLM nie może zgadywać opłaty ani stosować wartości domyślnych."
    )

    oplata_za_wynik: Optional[str] = Field(
        description="Opisowa informacja o opłacie za wynik (performance fee) dokładnie tak, "
        "jak podano w karcie funduszu. "
        "Może przyjmować formę: 'brak', 'nie dotyczy', 'tak – model Alfa', "
        "'tak – high-water mark', 'tak – X% od nadwyżki ponad benchmark'. "
        "Jeżeli w karcie funduszu występuje liczba procentowa (np. 20%), "
        "należy przepisać ją w formacie tekstowym '20%'. "
        "Jeżeli karta funduszu nie podaje żadnej informacji o opłacie za wynik, "
        "należy zwrócić null. "
        "LLM nie może zakładać istnienia opłaty za wynik na podstawie typu funduszu "
        "ani wnioskować jej procentowej wysokości."
    )

    oplata_manipulacyjna: Optional[float] = Field(
        description="Opłata manipulacyjna (wejściowa) wyrażona w procentach, konwertowana na float "
        "w formacie dziesiętnym: np. 3% zapisz jako 0.03, 5% zapisz jako 0.05, 1,5% zapisz jako 0.015. "
        "Wartość ZAWSZE musi być floatem, nigdy tekstem ani liczbą z procentem. "
        "Jeżeli karta funduszu zawiera sformułowania 'do X%', 'maksymalnie X%' lub "
        "'zgodnie z tabelą opłat – X%', należy użyć liczby X i przeliczyć ją na float. "
        "Jeżeli w karcie widnieje '0%' lub 'brak opłaty', należy wpisać 0.0. "
        "Jeśli karta nie podaje żadnej informacji → null. "
        "LLM nie może zgadywać wartości."
    )

    # =========================================================
    # 5. BENCHMARK
    # =========================================================

    benchmark_nazwa: Optional[str] = Field(
        description="Pełna nazwa benchmarku lub wskaźnika referencyjnego dokładnie tak, jak podano "
        "w karcie funduszu. Jeśli benchmark ma jedną nazwę (np. '100% Euro Stoxx 50 INDEX EUR'), "
        "należy przepisać ją w całości. "
        "Jeśli benchmark składa się z wielu komponentów procentowych, benchmark_nazwa może "
        "pozostać null. "
        "Jeżeli benchmark jest tabelaryczny, benchmark_nazwa może pozostać pusta."
    )

    benchmark_sklad: List[str] = Field(
        default_factory=list,
        description="Lista składników benchmarku w formacie 'nazwa indeksu: procent'. "
        "Przykłady: 'mWIG40TR: 60%', 'sWIG80TR: 30%', 'WIBOR O/N: 10%'. "
        "Jeżeli karta podaje benchmark jako jedno zdanie bez listy, np. "
        "'100% Euro Stoxx 50 INDEX EUR', wtedy benchmark_sklad powinno zawierać jedną pozycję: "
        "'Euro Stoxx 50 INDEX EUR: 100%'. "
        "Jeżeli benchmark nie występuje → lista pusta. "
        "W przypadku tabeli (np. Pekao) należy dokładnie przepisać każdy składnik."
    )

    benchmark_waluta: Optional[str] = Field(
        description="Waluta benchmarku, jeśli jest wyraźnie wskazana (np. PLN, EUR, USD). "
        "Jeżeli komponenty benchmarku mają różne waluty, wybierz dominującą "
        "lub pozostaw null."
    )

    # =========================================================
    # 6. POLITYKA INWESTYCYJNA – STRESZCZENIE
    # =========================================================

    polityka_inwestycyjna_streszczenie: Optional[str] = Field(
        description=(
            "Krótkie streszczenie (2–3 zdania) polityki inwestycyjnej funduszu "
        "stworzone przez LLM własnymi słowami. "
        "Streszczenie musi zawierać trzy elementy: "
        "1) dominująca klasa aktywów, 2) zakres geograficzny, "
        "3) charakter strategii (np. aktywna selekcja, inwestowanie pasywne, wysoka zmienność). "
        "Nie wolno cytować karty funduszu – opis musi być parafrazą."
        )
    )

    # =========================================================
    # 7. RODZAJE INSTRUMENTÓW
    # =========================================================

    rodzaje_instrumentow: List[str] = Field(
        default_factory=list,
        description=(
            "Lista rodzajów instrumentów występujących w portfelu funduszu. "
        "Do przykładowych kategorii należą: akcje notowane, akcje nienotowane, "
        "obligacje skarbowe, obligacje korporacyjne, obligacje wysokodochodowe (HY), "
        "obligacje komunalne, listy zastawne, ETF, fundusze (tytuły uczestnictwa), "
        "instrumenty pochodne, depozyty bankowe, instrumenty rynku pieniężnego. "
        "Jeżeli rodzaj instrumentu NIE jest podany wprost, LLM powinien wnioskować "
        "kategorię na podstawie nazwy instrumentu (np. ETF po nazwie), "
        "lub kontekstu tabeli (np. fundusze HY → obligacje HY). "
        "Jeżeli kategoria nie może być ustalona jednoznacznie – pominąć instrument."
        )
    )

    # =========================================================
    # 8. STRUKTURA PORTFELA
    # =========================================================

    alokacja_geograficzna: List[str] = Field(
        default_factory=list,
        description="Struktura geograficzna portfela w formacie 'kraj/region: procent'. "
        "Należy przepisywać wartości dokładnie z kart funduszy. "
        "np. Polska, Strefa Euro, Europa Zachodnia, USA."
    )

    alokacja_walutowa: List[str] = Field(
        default_factory=list,
        description="Struktura walutowa w formacie 'waluta: procent'. "
        "Jeżeli karta funduszu nie podaje danych → lista pusta."
    )

    alokacja_sektorowa: List[str] = Field(
        default_factory=list,
        description="Struktura sektorowa portfela w formacie 'sektor: procent'. "
        "Jeśli karta funduszu nie podaje sektorów (np. PKO), należy wnioskować "
        "sektor na podstawie nazw spółek, używając ogólnych kategorii: "
        "Technologie, Finanse, Przemysł, Surowce, Zdrowie, Energetyka, Konsumpcyjne, Usługi. "
        "Jeśli sektor nie jest możliwy do określenia jednoznacznie → pominąć."
    )

    top10: List[str] = Field(
        default_factory=list,
        description="Lista 10 największych pozycji w portfelu. "
        "Format: 'nazwa: procent', np. 'ASML: 6.5%'. "
        "LLM powinien przepisać pozycje w kolejności od największej. "
        "Jeżeli procent jest podany bez znaku %, należy go dodać."
    )

    klasy_instrumentow: List[str] = Field(
        default_factory=list,
        description="Struktura klas instrumentów w formacie 'klasa: procent', np. "
        "'akcje: 90%', 'obligacje: 10%'. "
        "Jeśli karta funduszu nie podaje takich danych → lista pusta."
    )

    # =========================================================
    # 9. KATEGORIE JEDNOSTEK
    # =========================================================

    kategoria_A: Literal["tak", "nie"] = Field(
        description="Czy fundusz posiada jednostki kategorii A. "
        "Należy ustalić na podstawie tabeli opłat lub sekcji 'Klasy jednostek'."
    )

    inne_kategorie: List[str] = Field(
        default_factory=list,
        description="Pozostałe klasy jednostek (np. S, T, B, D). "
        "LLM ma wypisać tylko te, które są faktycznie podane w karcie funduszu."
    )


# ---------- WYWOŁANIE GEMINI NA PDF ----------

def extract_fund_card_from_pdf(pdf_path: str, model_name: str = "gemini-2.5-flash") -> FundcardFlat:
    """
    Czyta lokalny plik PDF z kartami funduszy, wysyła do Gemini i zwraca obiekt FundcardFlat.
    """
    load_dotenv()  # Wczytuje zmienne środowiskowe z pliku .env
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Brak zmiennej środowiskowej GEMINI_API_KEY.")

    client = genai.Client(api_key=api_key)

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {pdf_file}")

    pdf_bytes = pdf_file.read_bytes()
#zmieniam
    prompt = """
Jesteś analitykiem funduszy inwestycyjnych.

Na podstawie załączonego dokumentu karta funduszu inwestycyjnego wyobierz i wypisz
dla jednego funduszu:

1. Odczytaj wszystkie wymagane pola.
2. Jeśli jakiegoś pola nie ma wprost, zostaw je możliwie prosto (np. pusty string albo 0),
   ale NIE wymyślaj rzeczy sprzecznych z dokumentem.
3. Pola typu lista (aktywa, rynki, ryzyka, segmenty, metryki) zwracaj jako
   pojedynczy string z elementami rozdzielonymi średnikami, np.:
   "obligacje skarbowe; obligacje korporacyjne; depozyty bankowe".
4. Zwróć odpowiedź dokładnie w schemacie JSON dostarczonym w konfiguracji.
"""

    response = client.models.generate_content(
        model=model_name,
        contents=[
            types.Part.from_bytes(
                data=pdf_bytes,
                mime_type="application/pdf",
            ),
            prompt,
        ],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": FundcardFlat.model_json_schema(),
        },
    )

    # response.text = JSON zgodny ze schematem FundcardFlat
    return FundcardFlat.model_validate_json(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Przetwarzanie plików karty funduszu z pliku PDF z danego folderu."
    )
    parser.add_argument(
        "folder_path", type=str, help="Ścieżka do folderu z plikami PDF."
    )
    parser.add_argument(
        "--max_files",
        type=int,
        default=None,
        help="Maksymalna liczba plików do przetworzenia.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Nadpisz istniejące pliki JSON.",
    )
    args = parser.parse_args()

    input_dir = Path(args.folder_path)
    if not input_dir.is_dir():
        print(f"Błąd: Podana ścieżka '{input_dir}' nie jest folderem.")
        sys.exit(1)

    pdf_files = sorted([f for f in input_dir.glob("*.pdf")])[: args.max_files]

    for pdf_path in pdf_files:
        output_filename = f"Podsumowanie_{pdf_path.stem}.json"
        output_path = input_dir / output_filename

        if output_path.exists() and not args.overwrite:
            print(f"⏩ Pomijam (plik istnieje): {output_filename}")
            continue

        print(f"\n--- Przetwarzanie pliku: {pdf_path.name} ---")
        fund_data = extract_fund_card_from_pdf(str(pdf_path))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(fund_data.model_dump_json(indent=2, ensure_ascii=False))
        print(f"✅ Zapisano podsumowanie do: {output_path}")


if __name__ == "__main__":
    main()
 