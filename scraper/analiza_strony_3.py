import argparse

import json

import os

import re

from pathlib import Path

from urllib.parse import urljoin
 
from dotenv import load_dotenv

from playwright.sync_api import Playwright, sync_playwright, TimeoutError

from google import genai
 
 
DEFAULT_URL = (

    "https://www.pkobp.pl/klient-indywidualny/oszczedzanie-inwestycje/fundusze-inwestycyjne?srsltid=AfmBOoolc1pXCLSJSdUX5TMojFuCmK8qOi6OFb7Cz7KhSyXG80RpVIAn%22%29&filter=4"

)
 
 
def collect_links(page, base_url: str):

    """Zbierz wszystkie linki <a> ze strony i znormalizuj URL-e."""

    link_elements = page.locator("a").all()

    links = []

    seen = set()
 
    for el in link_elements:

        href = el.get_attribute("href")

        if not href:

            continue

        href = href.strip()
 
        # pomijamy śmieci

        if (

            href.startswith("#")

            or href.lower().startswith("javascript:")

            or href.lower().startswith("mailto:")

        ):

            continue
 
        full_url = urljoin(base_url, href)

        text = (el.inner_text() or "").strip()
 
        key = (text, full_url)

        if key in seen:

            continue

        seen.add(key)
 
        links.append({"text": text, "url": full_url})
 
    return links
 
 
def call_gemini_filter_funds(raw_links, page_url: str, api_key: str):

    """

    Użyj Gemini 2.5 Flash, żeby z listy linków ze strony PKO

    wyciągnąć tylko linki do funduszy i nadać im sensowne nazwy.

    """

    client = genai.Client(api_key=api_key)
 
    prompt = (

        "Masz listę linków z tej strony PKO Banku Polskiego:\n"

        f"{page_url}\n\n"

        "Każdy element ma pola 'text' i 'url'. Twoje zadanie:\n"

        "1) Zidentyfikuj linki prowadzące do stron konkretnych funduszy inwestycyjnych "

        "(subfunduszy PKO TFI – opisy funduszy, a nie regulaminy, FAQ itd.).\n"

        "2) Dla każdego funduszu zwróć obiekt:\n"

        '   {\"text\": \"Nazwa funduszu\", \"url\": \"LINK\"}\n'

        "   - 'text' ma być czystą nazwą funduszu (np. 'PKO Obligacji Skarbowych Krótkoterminowy').\n"

        "   - 'url' to pełny link do opisu tego funduszu.\n\n"

        "Jeśli nazwa funduszu nie jest bezpośrednio w 'text', możesz ją odtworzyć na podstawie kontekstu.\n\n"

        "Zwróć **TYLKO** czysty JSON w formacie:\n"

        "[{\"text\": \"...\", \"url\": \"...\"}, ...]"

    )
 
    links_json = json.dumps(raw_links, ensure_ascii=False)
 
    response = client.models.generate_content(

        model="gemini-2.5-flash",

        contents=[

            prompt,

            "Oto lista linków jako JSON:",

            links_json,

        ],

    )
 
    text = response.text.strip()
 
    # Parsowanie odpowiedzi jako JSON (z awaryjnym wycięciem fragmentu)

    try:

        cleaned = json.loads(text)

    except json.JSONDecodeError:

        first = text.find("[")

        last = text.rfind("]")

        if first != -1 and last != -1 and last > first:

            snippet = text[first : last + 1]

            cleaned = json.loads(snippet)

        else:

            raise RuntimeError("Nie udało się odczytać JSON z odpowiedzi Gemini:\n" + text)
 
    return cleaned
 
 
def handle_cookies(page):

    """Spróbuj zamknąć baner cookies na pkobp.pl."""

    try:

        print("Szukam banera cookies...")

        btn = page.get_by_role(

            "button",

            name=re.compile(

                r"(Zezwól|Akceptuj|Akceptuję).*(wszystk|cookie|ciasteczk)",

                re.IGNORECASE,

            ),

        )

        btn.click(timeout=5_000)

        print("Kliknięto przycisk cookies.")

    except TimeoutError:

        print("Nie znaleziono banera cookies lub już zaakceptowany.")

    except Exception as e:

        print(f"Problem z obsługą cookies: {e}")
 
 
def run(playwright: Playwright, url: str, api_key: str) -> None:

    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context()

    page = context.new_page()
 
    raw_links = []  # <- inicjalizacja, żeby nie było UnboundLocalError
 
    try:

        print(f"Otwieram stronę: {url}")

        # Szybsze: czekamy tylko na DOM, nie na pełne networkidle

        page.goto(url, timeout=60_000, wait_until="domcontentloaded")
 
        # networkidle może się wysypać – łapiemy i ignorujemy

        try:

            page.wait_for_load_state("networkidle", timeout=15_000)

        except TimeoutError:

            print("Timeout na networkidle – ignoruję, lecę dalej.")
 
        handle_cookies(page)
 
        snapshot_path = Path("pko_fundusze_start.png")

        page.screenshot(path=str(snapshot_path), full_page=True)

        print(f"Zapisano screenshot: {snapshot_path.resolve()}")
 
        print("Zbieram wszystkie linki <a> ze strony...")

        raw_links = collect_links(page, url)

        print(f"Zebrano {len(raw_links)} linków (surowe).")
 
    finally:

        print("Zamykam przeglądarkę.")

        context.close()

        browser.close()
 
    if not raw_links:

        print("Brak zebranych linków – nie wywołuję Gemini.")

        return
 
    print("Wywołuję Gemini 2.5 Flash do przefiltrowania linków funduszy...")

    fund_links = call_gemini_filter_funds(raw_links, url, api_key)

    print(f"Gemini zwrócił {len(fund_links)} funduszy.\n")
 
    print("Wynik (fundusze):")

    for item in fund_links:

        print(f"- {item.get('text')} -> {item.get('url')}")
 
    out_path = Path("pko_fundusze_links.json")

    out_path.write_text(json.dumps(fund_links, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nZapisano: {out_path.resolve()}")
 
 
if __name__ == "__main__":

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        raise EnvironmentError("Brak GEMINI_API_KEY w .env / env.")
 
    parser = argparse.ArgumentParser(

        description="Zbierz linki do funduszy ze strony PKO i przefiltruj je Gemini 2.5 Flash."

    )

    parser.add_argument(

        "--url",

        default=DEFAULT_URL,

        help=f"URL strony z funduszami (domyślnie: {DEFAULT_URL})",

    )

    args = parser.parse_args()
 
    with sync_playwright() as playwright:

        run(playwright, args.url, api_key)

 

 

#python analiza_strony_3.py --url "https://www.pkotfi.pl/wycena-jednostek/"
