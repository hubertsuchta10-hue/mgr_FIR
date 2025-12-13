import argparse

import json

import os

from urllib.parse import urljoin
 
from dotenv import load_dotenv   # <--- NOWE

from playwright.sync_api import sync_playwright

from google import genai
import re
 
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

        if href.startswith("#") or href.lower().startswith("javascript:") or href.lower().startswith("mailto:"):

            continue
 
        full_url = urljoin(base_url, href)

        text = el.inner_text().strip() if el.inner_text() else ""
 
        key = (text, full_url)

        if key in seen:

            continue

        seen.add(key)
 
        links.append({"text": text, "url": full_url})
 
    return links
 
 
def call_gemini_filter_funds(raw_links, page_url: str):

    """Użyj Gemini 2.5 Flash do wybrania i oczyszczenia linków do funduszy."""

    client = genai.Client()  # pobiera GEMINI_API_KEY z env
 
    prompt = (

        "Masz listę linków z jednej strony internetowej.\n"

        "Każdy element ma pola 'text' i 'url'.\n\n"

        f"Strona startowa: {page_url}\n\n"

        "Twoje zadanie:\n"

        "1) Zidentyfikuj linki prowadzące do stron funduszy inwestycyjnych.\n"

        "2) Dla każdego takiego linku zwróć obiekt:\n"

        '   {\"text\": \"Nazwa funduszu\", \"url\": \"LINK\"}\n'

        "   - 'text' to czysta nazwa funduszu.\n"

        "   - 'url' to pełny link.\n\n"

        "Zwróć **TYLKO** JSON bez dodatkowych komentarzy."

    )
 
    links_json = json.dumps(raw_links, ensure_ascii=False)
 
    response = client.models.generate_content(

        model="gemini-2.5-flash",

        contents=[prompt, "Oto lista linków jako JSON:", links_json],

    )
 
    text = response.text.strip()
 
    # spróbuj parsować JSON

    try:

        cleaned = json.loads(text)

    except json.JSONDecodeError:

        first = text.find("[")

        last = text.rfind("]")

        if first != -1 and last != -1 and last > first:

            snippet = text[first:last+1]

            cleaned = json.loads(snippet)

        else:

            raise RuntimeError("Nie udało się odczytać JSON z odpowiedzi Gemini:\n" + text)
 
    return cleaned
 
 

    

def run(url: str):

    print(f"Start – zbieram linki ze strony: {url}")
 
    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(headless=False)

        context = browser.new_context()

        page = context.new_page()
 
        try:

            page.goto(url, timeout=60000)

            page.wait_for_load_state("networkidle")
 
            page.screenshot(path="snapshot.png")

            print("Zapisano screenshot: snapshot.png")
            try:
                page.get_by_test_id("uc-accept-all-button").first.click(timeout=5_000)
            except Exception:
                pass  # popup may have been previously accepted
            try:
                page.get_by_role("link", name=re.compile("Akceptuj", re.IGNORECASE)).first.click(timeout=5_000)
            except Exception:
                pass
            raw_links = collect_links(page, url)

            print(f"Zebrano {len(raw_links)} linków (surowe).")
 
        except Exception as e:
            print(f"Wystąpił błąd podczas interakcji z Playwright: {e}")
        finally:

            print("Zamykam przeglądarkę.")

            browser.close()
 
    print("Wywołuję Gemini 2.5 Flash...")

    fund_links = call_gemini_filter_funds(raw_links, url)

    print(f"Gemini zwrócił {len(fund_links)} linków.\n")
 
    print("Wynik:")

    for item in fund_links:

        print(f"- {item.get('text')} -> {item.get('url')}")
 
    with open("fund_links_clean.json", "w", encoding="utf-8") as f:

        json.dump(fund_links, f, ensure_ascii=False, indent=2)
 
    print("\nZapisano fund_links_clean.json")
 
 
if __name__ == "__main__":

    # Załaduj .env (NOWE)

    load_dotenv()
 
    parser = argparse.ArgumentParser(description="Scraper + filtr LLM (Gemini).")

    parser.add_argument(

        "--url",

        required=True,

        help="URL strony do scrapowania",

    )
 
    args = parser.parse_args()
 
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        raise EnvironmentError("Brak GEMINI_API_KEY w .env lub zmiennych środowiskowych.")
 
    run(args.url)
#python analiza_strony_2.py --url https://pekaotfi.pl/produkty/fundusze-inwestycyjne
#python analiza_strony_2.py --url https://www.santander.pl/tfi/fundusze-inwestycyjne
#python analiza_strony_2.py --url "https://www.pkobp.pl/klient-indywidualny/oszczedzanie-inwestycje/fundusze-inwestycyjne?srsltid=AfmBOoolc1pXCLSJSdUX5TMojFuCmK8qOi6OFb7Cz7KhSyXG80RpVIAn%22%29&filter=1"
