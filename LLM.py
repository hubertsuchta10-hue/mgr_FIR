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
        description="Pełna nazwa subfunduszu z nagłówka karty funduszu."
    )

    towarzystwo: str = Field(
        description="Podmiot zarządzający (PKO TFI / Santander TFI / Pekao TFI)."
    )

    kategoria_funduszu: Optional[str] = Field(
        description=(
            "Deklaratywna kategoria funduszu nadana przez TFI, np. "
            "'akcyjny rynków zagranicznych', "
            "'obligacji wysokodochodowych', "
            "'fundusz cyklu życia', "
            "'PPK'."
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
            "Czy fundusz jest częścią programu Pracowniczych Planów Kapitałowych (PPK)."
        )
    )

    data_publikacji: Optional[str] = Field(
        description="Data publikacji karty funduszu (YYYY-MM-DD)."
    )

    # =========================================================
    # 2. OGÓLNY WSKAŹNIK RYZYKA
    # =========================================================

    ogolny_wskaznik_ryzyka: Optional[
        Literal[1, 2, 3, 4, 5, 6, 7]
    ] = Field(
        description=(
            "Ogólny wskaźnik ryzyka w skali 1–7, "
            "przepisany bezpośrednio z karty funduszu. "
            "Jeżeli brak – null."
        )
    )

    # =========================================================
    # 3. DANE OGÓLNE
    # =========================================================

    aktywa_netto_mln: Optional[float] = Field(
        description="Aktywa netto funduszu w mln zł."
    )

    cena_jednostki: Optional[float] = Field(
        description="Cena jednostki uczestnictwa."
    )

    minimalna_wplata_pierwsza: Optional[float] = Field(
        description="Minimalna pierwsza wpłata."
    )

    data_pierwszej_wyceny: Optional[str] = Field(
        description="Data pierwszej wyceny funduszu (YYYY-MM-DD)."
    )

    sugerowany_czas_inwestycji_lata: Optional[int] = Field(
        description="Sugerowany minimalny czas inwestycji w latach."
    )

    # =========================================================
    # 4. OPŁATY
    # =========================================================

    oplata_za_zarzadzanie: Optional[float] = Field(
        description="Roczna opłata za zarządzanie w %, jako float np. 3% zapisz jako 0.03."
    )

    oplata_za_wynik: Optional[str] = Field(
        description="Opisowa informacja o opłacie za wynik."
    )

    oplata_manipulacyjna: Optional[float] = Field(
        description="Opłata manipulacyjna (wejściowa) w %, jako float np. 3% zapisz jako 0.03."
    )

    # =========================================================
    # 5. BENCHMARK
    # =========================================================

    benchmark_nazwa: Optional[str] = Field(
        description="Nazwa benchmarku funduszu, jeśli występuje."
    )

    benchmark_sklad: List[str] = Field(
        default_factory=list,
        description="Skład benchmarku, np. ['WIG: 90%', 'POLONIA: 10%']."
    )

    benchmark_waluta: Optional[str] = Field(
        description="Waluta benchmarku (PLN, EUR, USD)."
    )

    # =========================================================
    # 6. POLITYKA INWESTYCYJNA – STRESZCZENIE
    # =========================================================

    polityka_inwestycyjna_streszczenie: Optional[str] = Field(
        description=(
            "Krótki (2–3 zdania) opis polityki inwestycyjnej, "
            "stworzony jako streszczenie treści karty funduszu."
        )
    )

    # =========================================================
    # 7. RODZAJE INSTRUMENTÓW
    # =========================================================

    rodzaje_instrumentow: List[str] = Field(
        default_factory=list,
        description=(
            "Rodzaje instrumentów finansowych występujących w portfelu, "
            "np. akcje notowane, obligacje skarbowe, obligacje korporacyjne, "
            "obligacje wysokodochodowe, ETF, fundusze, "
            "depozyty bankowe, instrumenty rynku pieniężnego."
        )
    )

    # =========================================================
    # 8. STRUKTURA PORTFELA
    # =========================================================

    alokacja_geograficzna: List[str] = Field(
        default_factory=list,
        description="Struktura geograficzna portfela."
    )

    alokacja_walutowa: List[str] = Field(
        default_factory=list,
        description="Struktura walutowa portfela."
    )

    alokacja_sektorowa: List[str] = Field(
        default_factory=list,
        description="Struktura sektorowa portfela."
    )

    top10: List[str] = Field(
        default_factory=list,
        description="Lista 10 największych pozycji w portfelu."
    )

    klasy_instrumentow: List[str] = Field(
        default_factory=list,
        description="Struktura klas instrumentów."
    )

    # =========================================================
    # 9. KATEGORIE JEDNOSTEK
    # =========================================================

    kategoria_A: Literal["tak", "nie"] = Field(
        description="Czy fundusz posiada kategorię jednostek A."
    )

    inne_kategorie: List[str] = Field(
        default_factory=list,
        description="Pozostałe kategorie jednostek (np. S, T, B, D)."
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
 