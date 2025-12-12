import os
import sys
from pathlib import Path
import argparse
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

#sposób odpalenia kodu: python ./LLM.py "/Users/hubert/Desktop/mgr_FIR/Pekao_KID/Pekao Konserwatywny Plus_karta.pdf"
# ---------- JEDEN, PŁASKI SCHEMAT ---------- 
# double check - czy jest tak jak w KID
# predefiniowana lista pól do wyciągnięcia z KID

class FundKIDFlat(BaseModel):

    # Identyfikacja

    fund_name: str = Field(description="Pełna nazwa funduszu.")

    isin: str = Field(description="Kod ISIN funduszu.")

    management_company: str = Field(

        description="Podmiot zarządzający (TFI / towarzystwo funduszy inwestycyjnych)."

    )
 
    # 1. Typ funduszu

    fund_type: Literal["Akcyjny", "Mieszany", "Dłużny"] = Field(

        description="Typ funduszu: Akcyjny, Mieszany lub Dłużny (obligacyjny)."

    )
 
    # 2. Geografia + udział procentowy

    geography_allocation: str = Field(

        description=(

            "Struktura geograficzna aktywów w formacie 'region: procent', "

            "rozdzielona średnikami, np. 'Polska: 40; USA: 30; Europa: 30'."

        )

    )
 
    # 3. Sektor / klasa aktywów + udział

    sector_allocation: str = Field(

        description=(

            "Struktura sektorowa (dla funduszy akcyjnych/mieszanych) lub klas aktywów, "

            "w formacie 'sektor/klasa: procent', rozdzielona średnikami, np. "

            "'AI: 25; Zbrojeniowy: 15; Konsumpcyjny: 20; Instrumenty pieniężne: 40'."

        )

    )

    fixed_income_share_percent: float = Field(

        description=(

            "Udział części dłużnej (obligacyjnej) w portfelu w %, istotny szczególnie dla funduszy mieszanych."

        )

    )
 
    # 4. Ratingi kredytowe

    credit_rating_breakdown: str = Field(

        description=(

            "Rozkład wewnętrznego ratingu kredytowego lub zewnętrznych ratingów "

            "w formacie 'rating: procent', np. 'AAA: 20; AA: 30; A: 25; BBB i niżej: 25'."

        )

    )
 
    # 5. Struktura walutowa

    currency_allocation: str = Field(

        description=(

            "Struktura walutowa aktywów w formacie 'waluta: procent', rozdzielona średnikami, "

            "np. 'PLN: 60; USD: 25; EUR: 15'."

        )

    )
 
    # 6. Opłaty

    entry_fee_percent: float = Field(

        description="Maksymalna opłata wejściowa w % (jeśli brak – 0.0)."

    )

    management_fee_percent: float = Field(

        description="Roczna opłata za zarządzanie w % (TER/management fee)."

    )

    performance_fee_percent: float = Field(

        description="Roczna opłata za wyniki (performance fee) w % (jeśli brak – 0.0)."

    )

    other_fees_percent: float = Field(

        description="Pozostałe koszty bieżące w % (np. koszty administracyjne, depozytariusza)."

    )

    total_expense_ratio_percent: float = Field(

        description="Całkowity wskaźnik kosztów (TER) w % w skali roku."

    )
 
    # 7. Stopa zwrotu (5 lat)

    return_5y_percent: float = Field(

        description="Skumulowana stopa zwrotu za ostatnie 5 lat w % (jeśli dostępna)."

    )
 
    # 8. Wewnętrzne wskaźniki ryzyka

    internal_risk_indicators: str = Field(

        description=(

            "Opisowe lub ilościowe wewnętrzne wskaźniki ryzyka, rozdzielone średnikami, np. "

            "'maksymalne obsunięcie kapitału; VaR; tracking error'."

        )

    )
 
    # 9. Wskaźnik Sharpe’a

    sharpe_ratio_5y: float = Field(

        description="Wskaźnik Sharpe’a liczony dla horyzontu 5-letniego."

    )
 
    # 10. Odchylenie standardowe

    volatility_5y_percent: float = Field(

        description="Roczne odchylenie standardowe stóp zwrotu (volatility) w % dla okresu 5 lat."

    )
 


# ---------- WYWOŁANIE GEMINI NA PDF ----------

def extract_fund_kid_from_pdf(pdf_path: str, model_name: str = "gemini-2.5-flash") -> FundKIDFlat:
    """
    Czyta lokalny plik PDF z KID-em, wysyła do Gemini i zwraca obiekt FundKIDFlat.
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

    prompt = """
Jesteś analitykiem funduszy inwestycyjnych.

Na podstawie załączonego dokumentu KID (Kluczowe Informacje dla Inwestorów)
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
            "response_json_schema": FundKIDFlat.model_json_schema(),
        },
    )

    # response.text = JSON zgodny ze schematem FundKIDFlat
    return FundKIDFlat.model_validate_json(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Przetwarzanie plików KID PDF z danego folderu."
    )
    parser.add_argument(
        "folder_path", type=str, help="Ścieżka do folderu z plikami PDF."
    )
    parser.add_argument(
        "--max_files",
        type=int,
        default=1,
        help="Maksymalna liczba plików do przetworzenia.",
    )
    args = parser.parse_args()

    input_dir = Path(args.folder_path)
    if not input_dir.is_dir():
        print(f"Błąd: Podana ścieżka '{input_dir}' nie jest folderem.")
        sys.exit(1)

    pdf_files = sorted([f for f in input_dir.glob("*.pdf")])[: args.max_files]

    for pdf_path in pdf_files:
        print(f"\n--- Przetwarzanie pliku: {pdf_path.name} ---")
        fund_data = extract_fund_kid_from_pdf(str(pdf_path))
        output_filename = f"Podsumowanie_{pdf_path.stem}.json"
        output_path = input_dir / output_filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(fund_data.model_dump_json(indent=2, ensure_ascii=False))
        print(f"✅ Zapisano podsumowanie do: {output_path}")


if __name__ == "__main__":
    main()
 