import re
from playwright.sync_api import Playwright, sync_playwright, expect
from playwright._impl._errors import TimeoutError
import os
from lista_funduszy_pekao import funds
def run(playwright: Playwright, fund) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    # Define download directory
    download_dir = "/Users/hubert/Desktop/mgr_FIR/Pekao_KID"

    try:
        # Navigate directly to the fund page, which is more reliable
        print(f"Navigating to the fund page for '{fund['text']}'...")
        page.goto(fund["url"], wait_until="networkidle")

        # Wait for the cookie banner and accept it.
        # This might fail if the banner doesn't appear, so wrap in a try/except.
        try:
            print("Looking for cookie banner...")
            page.get_by_role("button", name="Zezwól na wszystkie").click(timeout=5000)
            print("Cookie banner accepted.")
        except TimeoutError:
            print("Cookie banner not found or already accepted.")

        # --- Download KID document ---
        print("\nAttempting to download KID document...")
        kid_path = os.path.join(download_dir, fund["text"] + "_KID.pdf")
        if os.path.exists(kid_path):
            print(f"✅ KID document already exists, skipping download: {kid_path}")
        else:
            try:
                with page.expect_download(timeout=20000) as download_info:
                    # This selector is more robust. It finds the first link with "KID" in its text.
                    print("Searching for KID link and clicking...")
                    page.get_by_role("link", name=re.compile("KID", re.IGNORECASE)).first.click()
                
                download = download_info.value
                # Save the file to the specified directory
                download.save_as(kid_path)
                print(f"✅ Successfully downloaded KID document to: {kid_path}")

            except TimeoutError:
                print("❌ ERROR: Timed out waiting for the KID document download.")
                print("   The script could not find a clickable link containing 'KID' that started a download.")
                screenshot_path = os.path.join(download_dir, "debug_screenshot_kid_error.png")
                page.screenshot(path=screenshot_path)
                print(f"   A screenshot has been saved to {screenshot_path} for debugging.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # ---------------------
        print("\nClosing browser.")
        context.close()
        browser.close()


with sync_playwright() as playwright:  
    for fund in funds:
        run(playwright, fund)
