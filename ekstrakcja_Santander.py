import re

import os

from typing import Dict, Any, List, Union
 
from playwright.sync_api import Playwright, sync_playwright, TimeoutError, expect

from lista_funduszy_Santander import funds  # <- DOPASUJ NAZWĘ PLIKU Z LISTĄ FUNDUSZY
 
 
START_URL = "https://www.santander.pl/tfi/fundusze-inwestycyjne"

DOWNLOAD_DIR = "/Users/hubert/Desktop/mgr_FIR/Santander"
 
 
def normalize_fund_entry(fund: Union[str, Dict[str, Any]]) -> Dict[str, Any]:

    """

    Pozwala używać zarówno:

    - "Fundusz XYZ"

    - {"text": "Fundusz XYZ", ...}

    Zwraca zawsze dict z kluczem "text".

    """

    if isinstance(fund, str):

        return {"text": fund}

    return fund
 
 
def build_link_pattern(full_name: str, prefix_len: int = 18) -> re.Pattern:

    """

    Tworzy regex, który ma trafić w uciętą nazwę na stronie.

    Bierzemy pierwsze N znaków pełnej nazwy i robimy z tego ^prefix.* (case-insensitive).

    """

    prefix = full_name.strip()[:prefix_len]

    escaped = re.escape(prefix)

    pattern = re.compile(rf"^{escaped}.*", re.IGNORECASE)

    return pattern
 
 
def check_name_match(page_link_text: str, full_name: str) -> bool:

    """

    Sprawdzenie spójności:

    - na stronie: ucięta nazwa (page_link_text)

    - w liście: pełna nazwa (full_name)
 
    Warunek OK: tekst ze strony jest prefiksem pełnej nazwy

    (po znormalizowaniu spacji i case).

    """

    a = re.sub(r"\s+", " ", page_link_text).strip().casefold()

    b = re.sub(r"\s+", " ", full_name).strip().casefold()

    return b.startswith(a)
 
 
def run_single(playwright: Playwright, fund_raw: Union[str, Dict[str, Any]]) -> None:

    fund = normalize_fund_entry(fund_raw)

    fund_name = fund["text"]
 
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    target_path = os.path.join(DOWNLOAD_DIR, f"{fund_name}_karta.pdf")
 
    print(f"\n=== Fundusz (Santander): {fund_name} ===")
 
    # Skip jeśli już pobrane

    if os.path.exists(target_path):

        print(f"✅ Plik już istnieje, pomijam: {target_path}")

        return
 
    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context()

    page = context.new_page()
 
    try:

        # 1. Wejście na stronę główną funduszy

        print(f"Otwieram stronę startową: {START_URL}")

        page.goto(START_URL, wait_until="networkidle", timeout=60_000)
 
        # 2. Cookies

        try:

            print("Szukam banera cookies...")

            page.get_by_role("button", name="Akceptuję ustawienia cookies").first.click(timeout=5_000)

            print("✅ Cookies zaakceptowane.")

        except TimeoutError:

            print("ℹ️ Baner cookies nie pojawił się lub już zaakceptowany.")
 
        # 3. Szukanie linku do funduszu

        print("Szukam linku do funduszu na liście...")

        pattern = build_link_pattern(fund_name, prefix_len=18)

        locator = page.get_by_role("link", name=pattern)
 
        try:

            link = locator.first

            link_text = link.inner_text().strip()

            print(f"Znaleziony link na stronie: '{link_text}'")
 
            # Walidacja nazwy

            if not check_name_match(link_text, fund_name):

                print(

                    f"⚠️ UWAGA: nazwa na stronie ('{link_text}') nie wygląda jak ucięcie pełnej nazwy ('{fund_name}')."

                )

            else:

                print("✅ Nazwa na stronie jest spójnym ucięciem pełnej nazwy z listy.")
 
            print("Przechodzę do strony funduszu...")

            link.click(timeout=5_000)
 
        except TimeoutError:

            print("❌ Nie udało się znaleźć / kliknąć linku funduszu. Zapisuję screenshot.")

            screenshot_path = os.path.join(DOWNLOAD_DIR, f"debug_{fund_name}_not_found.png")

            page.screenshot(path=screenshot_path, full_page=True)

            print(f"   Screenshot: {screenshot_path}")

            return
 
        # 4. Pobranie „Karta subfunduszu”

        print("Próbuję pobrać 'Karta subfunduszu'...")
 
        try:

            with page.expect_download(timeout=20_000) as download_info:

                page.get_by_role("link", name="Karta subfunduszu").first.click(timeout=5_000)
 
            download = download_info.value

            download.save_as(target_path)

            print(f"✅ Pobrano kartę subfunduszu do: {target_path}")
 
        except TimeoutError:

            print("❌ Timeout przy pobieraniu 'Karta subfunduszu'. Zapisuję screenshot.")

            screenshot_path = os.path.join(DOWNLOAD_DIR, f"debug_{fund_name}_card_timeout.png")

            page.screenshot(path=screenshot_path, full_page=True)

            print(f"   Screenshot: {screenshot_path}")
 
    except Exception as e:

        print(f"❌ Nieoczekiwany błąd dla funduszu '{fund_name}': {e}")

        try:

            screenshot_path = os.path.join(DOWNLOAD_DIR, f"debug_{fund_name}_unexpected.png")

            page.screenshot(path=screenshot_path, full_page=True)

            print(f"   Screenshot: {screenshot_path}")

        except Exception:

            pass
 
    finally:

        print("Zamykam przeglądarkę.")

        context.close()

        browser.close()
 
 
if __name__ == "__main__":

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    with sync_playwright() as playwright:

        for f in funds:

            run_single(playwright, f)

 