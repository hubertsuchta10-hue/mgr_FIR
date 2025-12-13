import argparse

import json

import os

from pathlib import Path

from typing import Any, Dict, List, Union
 
import pandas as pd
 
 
def find_json_files(dirs: List[Path]) -> List[Path]:

    """Znajdź wszystkie pliki .json w podanych katalogach (rekurencyjnie)."""

    json_files: List[Path] = []

    for d in dirs:

        if not d.exists() or not d.is_dir():

            print(f"⚠️  Ostrzeżenie: katalog nie istnieje lub nie jest katalogiem: {d}")

            continue

        for path in d.rglob("*.json"):

            json_files.append(path)

    return json_files
 
 
def load_records_from_json(path: Path) -> List[Dict[str, Any]]:

    """

    Wczytaj plik JSON i zwróć listę rekordów (słowników).

    Obsługa:

      - dict  -> [dict]

      - list[dict] -> list[dict]

      - cokolwiek innego -> []

    """

    try:

        with path.open("r", encoding="utf-8") as f:

            data = json.load(f)

    except Exception as e:

        print(f"❌ Problem z wczytaniem JSON z pliku {path}: {e}")

        return []
 
    if isinstance(data, dict):

        return [data]

    if isinstance(data, list):

        # filtrujemy tylko dict-y

        return [item for item in data if isinstance(item, dict)]
 
    print(f"⚠️  Plik {path} zawiera JSON innego typu niż dict/list – pomijam.")

    return []
 
 
def jsons_to_excel(dirs: List[str], out_path: str) -> None:

    dir_paths = [Path(d) for d in dirs]

    json_files = find_json_files(dir_paths)
 
    if not json_files:

        print("❗ Nie znaleziono żadnych plików .json w podanych katalogach.")

        return
 
    print(f"Znaleziono {len(json_files)} plików JSON.")
 
    all_records: List[Dict[str, Any]] = []
 
    for path in json_files:

        records = load_records_from_json(path)

        if not records:

            continue
 
        # Możesz dodać info o źródłowym pliku

        for r in records:

            r["_source_file"] = str(path)

        all_records.extend(records)
 
    if not all_records:

        print("❗ Nie udało się wczytać żadnych rekordów z JSON-ów.")

        return
 
    # pandas.json_normalize spłaszcza zagnieżdżone struktury (dict w dict)

    df = pd.json_normalize(all_records)
 
    # zapis do Excela

    out = Path(out_path)

    out.parent.mkdir(parents=True, exist_ok=True)
 
    df.to_excel(out, index=False)

    print(f"✅ Zapisano {len(df)} wierszy do pliku: {out.resolve()}")
 
 
def main():

    parser = argparse.ArgumentParser(

        description="Zbierz wszystkie pliki JSON z podanych folderów i zapisz jako jedną tabelę w Excelu."

    )

    parser.add_argument(

        "--dirs",

        nargs="+",

        required=True,

        help="Lista katalogów, w których szukamy plików .json (rekurencyjnie).",

    )

    parser.add_argument(

        "--out",

        required=True,

        help="Ścieżka do pliku wyjściowego .xlsx (np. /tmp/dane.xlsx).",

    )
 
    args = parser.parse_args()

    jsons_to_excel(args.dirs, args.out)
 
 
if __name__ == "__main__":

    main()

 #python json2excel.py --dirs /Users/hubert/Desktop/mgr_FIR/Pekao /Users/hubert/Desktop/mgr_FIR/PKO /Users/hubert/Desktop/mgr_FIR/Santander --out dane_fundusze.xlsx
 #python json2excel.py --dirs /Users/hubert/Desktop/mgr_FIR/Pekao --out dane_fundusze.xlsx