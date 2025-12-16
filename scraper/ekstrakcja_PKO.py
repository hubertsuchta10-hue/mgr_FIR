import re

import os

from pathlib import Path
 
from playwright.sync_api import Playwright, sync_playwright

from playwright._impl._errors import TimeoutError
 
from lista_funduszy_PKO import funds  # [{"text": "...", "url": "..."}, ...]
 
 
DOWNLOAD_DIR = Path("/Users/hubert/Desktop/mgr_FIR/PKO")
 
 
def run(playwright: Playwright, fund: dict) -> None:

    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context()

    page = context.new_page()
 
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
 
    fund_name = fund.get("text", "UNKNOWN")

    fund_url = fund["url"]
 
    try:

        print(f"\n=== Fundusz: {fund_name} ===")

        print(f"Opening fund page: {fund_url}")
 
        # wejście na stronę funduszu (łagodniejsze wait_until)

        try:

            page.goto(fund_url, wait_until="domcontentloaded", timeout=60_000)

        except TimeoutError:

            print("⚠️ Timeout na goto – lecę dalej z tym co się załadowało.")
 
        # cookies

        try:

            print("Looking for cookie banner...")

            page.get_by_role("button", name="Zezwól na wszystkie").click(timeout=5000)

            print("Cookie banner accepted.")

        except TimeoutError:

            print("Cookie banner not found or already accepted.")
 
        # akceptacja warunków

        try:

            page.get_by_role("link", name=re.compile("Akceptuj", re.IGNORECASE)).click(timeout=5_000)

            print("Acceptance link clicked.")

        except TimeoutError:

            print("Acceptance link not found or already clicked.")
 
        print("Attempting to download card document...")

        print("Attempting to download card document...")
 
        # szukamy linku "karta funduszu"

        try:

            karta_link = page.get_by_role("link", name=re.compile("karta funduszu", re.IGNORECASE))

            href = karta_link.get_attribute("href")

        except TimeoutError:

            print("❌ Nie znaleziono linku 'karta funduszu' (Timeout). Skipping this fund.")

            return
 
        if not href:

            raise RuntimeError("Nie znaleziono href w linku 'karta funduszu'.")
 
        if href.startswith("/"):

            href = f"https://www.pkotfi.pl{href}"
 
        # *** NAZWA PLIKU: ORYGINALNA NAZWA FUNDUSZU ***

        filename = f"{fund_name}.pdf"

        target_path = DOWNLOAD_DIR / filename  # Path, więc .exists() działa
 
        # CACHE

        if target_path.exists():

            print(f"✅ File already exists, skipping download: {target_path}")

            return
 
        print(f"Downloading from {href} as '{filename}' ...")
 
        response = page.request.get(href)

        if not response.ok:

            raise RuntimeError(f"Nie udało się pobrać PDF, status {response.status}")
 
        target_path.write_bytes(response.body())

        print(f"✅ Pobrano plik: {target_path}")
 
    except Exception as e:

        print(f"❌ An unexpected error occurred for fund '{fund_name}': {e}")
 
    finally:

        print("Closing browser.")

        context.close()

        browser.close()
 
 
if __name__ == "__main__":

    with sync_playwright() as playwright:

        for fund in funds:

            run(playwright, fund)

 