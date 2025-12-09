import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ---------- JEDEN, PŁASKI SCHEMAT ---------- 
# double check - czy jest tak jak w KID
# predefiniowana lista pól do wyciągnięcia z KID

class FundKIDFlat(BaseModel):
    fund_name: str = Field(description="Pełna nazwa funduszu.")
    isin: str = Field(description="Kod ISIN funduszu.")
    kid_date: str = Field(
        description="Data dokumentu KID w formacie RRRR-MM-DD."
    )

    # Market / coverage
    fund_type: str = Field(
        description="Typ funduszu, np. 'short-term debt fund'."
    )
    target_assets: str = Field(
        description="Klasy aktywów, rozdzielone średnikami, np. 'obligacje; depozyty bankowe; ...'."
    )
    geographic_markets: str = Field(
        description="Rynki geograficzne, rozdzielone średnikami."
    )
    benchmark: str = Field(
        description="Benchmark funduszu, np. '100% POLONIA + 40bp'."
    )

    # Performance / ryzyko
    investment_horizon: str = Field(
        description="Rekomendowany horyzont inwestycyjny, np. '1 year'."
    )
    risk_indicator: int = Field(
        description="Syntetyczny wskaźnik ryzyka z KID (1–7)."
    )

    scenario_extreme_final_value: int = Field(
        description="Końcowa wartość inwestycji w scenariuszu skrajnym (PLN)."
    )
    scenario_extreme_return_percent: float = Field(
        description="Stopa zwrotu w scenariuszu skrajnym (%)."
    )

    scenario_unfavourable_final_value: int = Field(
        description="Końcowa wartość w scenariuszu niekorzystnym (PLN)."
    )
    scenario_unfavourable_return_percent: float = Field(
        description="Stopa zwrotu w scenariuszu niekorzystnym (%)."
    )

    scenario_moderate_final_value: int = Field(
        description="Końcowa wartość w scenariuszu umiarkowanym (PLN)."
    )
    scenario_moderate_return_percent: float = Field(
        description="Stopa zwrotu w scenariuszu umiarkowanym (%)."
    )

    scenario_favourable_final_value: int = Field(
        description="Końcowa wartość w scenariuszu korzystnym (PLN)."
    )
    scenario_favourable_return_percent: float = Field(
        description="Stopa zwrotu w scenariuszu korzystnym (%)."
    )

    # Koszty
    entry_fee_percent: float = Field(
        description="Maksymalna opłata wejściowa w %."
    )

    annual_transaction_costs_percent: float = Field(
        description="Roczne koszty transakcyjne w %."
    )
    annual_management_and_admin_percent: float = Field(
        description="Roczne koszty zarządzania i administracji w %."
    )
    annual_performance_fee_percent: float = Field(
        description="Roczna opłata za wyniki w %."
    )
    performance_fee_rate: float = Field(
        description="Stawka performance fee w %, np. 20.0."
    )

    annual_transaction_costs_pln: int = Field(
        description="Koszty transakcyjne po 1 roku w PLN."
    )
    annual_management_costs_pln: int = Field(
        description="Koszty zarządzania po 1 roku w PLN."
    )
    annual_performance_costs_pln: int = Field(
        description="Performance fee po 1 roku w PLN."
    )

    total_costs_after_1_year_pln: int = Field(
        description="Łączne koszty po 1 roku w PLN."
    )
    total_costs_after_1_year_percent: float = Field(
        description="Łączne koszty po 1 roku w %."
    )

    # Ryzyko opisowe
    risk_class: int = Field(
        description="Klasa ryzyka (1–7) zgodna z KID."
    )
    other_risks: str = Field(
        description="Inne istotne ryzyka, rozdzielone średnikami."
    )

    # Wnioski strategiczne (też spłaszczone)
    covered_segments: str = Field(
        description="Segmenty rynku pokrywane przez fundusz, rozdzielone średnikami."
    )
    not_covered_segments: str = Field(
        description="Segmenty rynku niepokrywane, rozdzielone średnikami."
    )
    efficiency_indicators_needed: str = Field(
        description="Dodatkowe wskaźniki efektywności potrzebne do analizy, rozdzielone średnikami."
    )
    peer_group: str = Field(
        description="Grupa porównawcza, np. 'fundusze dłużne krótkoterminowe'."
    )
    comparison_metrics: str = Field(
        description="Metryki porównania z konkurencją, rozdzielone średnikami."
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
    if len(sys.argv) < 2 or not sys.argv[-1].lower().endswith(".pdf"):
        print(f"Użycie: python {Path(__file__).name} path/do/pliku.pdf")
        raise SystemExit(1)

    pdf_path = sys.argv[-1]
    fund = extract_fund_kid_from_pdf(pdf_path)

    # Ładny JSON na stdout
    print(fund.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
 