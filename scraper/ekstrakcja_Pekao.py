import re
import os
import unicodedata
import requests

from playwright.sync_api import Playwright, sync_playwright
from playwright._impl._errors import TimeoutError

from lista_funduszy_pekao import funds


# ============================================================
# 1. NORMALIZACJA NAZWY FUNDUSZU → ID MODALA
# ============================================================

def normalize_modal_id(fund_name: str) -> str:
    """
    'Pekao Akcji – Aktywna Selekcja'
    -> 'modal-pekao-akcji-aktywna-selekcja'
    """
    name = fund_name.lower().strip()

    if name.startswith("pekao "):
        name = name[6:]

    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.replace("–", "-").replace("—", "-")
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)

    return f"modal-pekao-{name}"


# ============================================================
# 2. ZAMYKANIE / USUWANIE MODALI
# ============================================================

def close_any_modal(page, fund_name: str):
    modal_id = normalize_modal_id(fund_name)

    # 1️⃣ spróbuj zamknąć po ID
    try:
        btn = page.locator(f"#{modal_id} button:has-text('×')")
        if btn.is_visible(timeout=400):
            btn.click()
            page.wait_for_selector(f"#{modal_id}", state="hidden", timeout=2000)
            return
    except:
        pass

    # 2️⃣ spróbuj globalne ×
    try:
        btn = page.locator("button:has-text('×')")
        if btn.is_visible(timeout=400):
            btn.click()
            page.wait_for_timeout(200)
            return
    except:
        pass

    # 3️⃣ HARD RESET – usuń z DOM
    try:
        page.evaluate("""
            document.querySelectorAll('.modal, .modal-backdrop')
                .forEach(e => e.remove());
        """)
    except:
        pass


# ============================================================
# 3. POBRANIE PDF PO URL (BEZ expect_download)
# ============================================================

def download_pdf_from_page(page, card_path: str):
    """
    Szuka linku do PDF w:
    - a.js-doc-download
    - a[href$='.pdf']
    i pobiera plik przez requests
    """

    pdf_href = None

    # najczęstszy przypadek Pekao
    try:
        pdf_href = page.locator("a.js-doc-download").first.get_attribute("href")
    except:
        pass

    if not pdf_href:
        try:
            pdf_href = page.locator("a[href$='.pdf']").first.get_attribute("href")
        except:
            pass

    if not pdf_href:
        raise TimeoutError("Nie znaleziono linku PDF na stronie / w modalu.")

    if pdf_href.startswith("/"):
        pdf_url = "https://pekaotfi.pl" + pdf_href
    else:
        pdf_url = pdf_href

    print(f"📄 PDF URL found: {pdf_url}")

    r = requests.get(pdf_url, timeout=30)
    r.raise_for_status()

    with open(card_path, "wb") as f:
        f.write(r.content)


# ============================================================
# 4. GŁÓWNA FUNKCJA
# ============================================================

def run(playwright: Playwright, fund) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    download_dir = "/Users/hubert/Desktop/mgr_FIR/Pekao"
    card_path = os.path.join(download_dir, fund["text"] + "_karta.pdf")

    try:
        # ====================================================
        # FAST PATH – PLIK JUŻ ISTNIEJE
        # ====================================================
        if os.path.exists(card_path):
            print(f"✅ File already exists — skipping: {fund['text']}")
            return

        print(f"\nNavigating to fund page: {fund['text']}")
        page.goto(fund["url"], wait_until="networkidle", timeout=60000)

        # cookies
        try:
            page.get_by_role("button", name="Zezwól na wszystkie").click(timeout=5000)
        except TimeoutError:
            pass

        # upewnij się, że nic nie blokuje
        close_any_modal(page, fund["text"])

        # kliknij trigger (jeśli istnieje)
        try:
            link = page.get_by_role(
                "link", name=re.compile("Karta subfunduszu", re.I)
            ).first
            link.click(timeout=5000)
            page.wait_for_timeout(500)
        except:
            pass

        # popup „Akceptuję” (czasem)
        try:
            page.get_by_text("Akceptuję").first.click(timeout=3000)
        except:
            pass

        # usuń modale jeszcze raz
        close_any_modal(page, fund["text"])

        # ====================================================
        # POBIERANIE PDF
        # ====================================================
        print(f"⬇️ Downloading card for: {fund['text']}")
        download_pdf_from_page(page, card_path)

        print(f"✅ Saved: {card_path}")

    except Exception as e:
        print(f"❌ ERROR for '{fund['text']}': {e}")
        debug = os.path.join(download_dir, f"DEBUG_{fund['text']}.png")
        page.screenshot(path=debug)
        print(f"📷 Screenshot saved: {debug}")

    finally:
        context.close()
        browser.close()


# ============================================================
# 5. RUN
# ============================================================

with sync_playwright() as playwright:
    for fund in funds:
        run(playwright, fund)

