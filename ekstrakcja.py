import re
from playwright.sync_api import Playwright, sync_playwright, expect
from playwright._impl._errors import TimeoutError
import os

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    # Define download directory
    download_dir = "/Users/hubert/Desktop/mgr_FIR"

    try:
        # Navigate directly to the fund page, which is more reliable
        print("Navigating to the fund page for 'Pekao Konserwatywny'...")
        page.goto("https://pekaotfi.pl/produkty/fundusze-inwestycyjne/pekao-konserwatywny?currency=PLN")

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
        try:
            with page.expect_download(timeout=20000) as download_info:
                # This selector is more robust. It finds the first link with "KID" in its text.
                print("Searching for KID link and clicking...")
                page.get_by_role("link", name=re.compile("KID", re.IGNORECASE)).first.click()
            
            download = download_info.value
            # Save the file to the specified directory
            kid_path = os.path.join(download_dir, download.suggested_filename)
            download.save_as(kid_path)
            print(f"✅ Successfully downloaded KID document to: {kid_path}")

        except TimeoutError:
            print("❌ ERROR: Timed out waiting for the KID document download.")
            print("   The script could not find a clickable link containing 'KID' that started a download.")
            screenshot_path = os.path.join(download_dir, "debug_screenshot_kid_error.png")
            page.screenshot(path=screenshot_path)
            print(f"   A screenshot has been saved to {screenshot_path} for debugging.")

        # --- Download CSV data ---
        print("\nAttempting to download CSV data...")
        try:
            # This action opens a new tab/popup that triggers the download.
            # We listen for both events happening as a result of the click.
            # A generous timeout is used as the process can be slow.
            with page.expect_download(timeout=45000) as download_info:
                with page.expect_popup(timeout=10000) as popup_info:
                    print("Searching for 'Pobierz csv' link and clicking...")
                    page.get_by_role("link", name="Pobierz csv").click()
                
                popup = popup_info.value
                print(f"Popup window opened with URL: {popup.url}")
                # Wait for the popup to finish its work before closing, just in case
                popup.wait_for_load_state()
            
            download = download_info.value
            csv_path = os.path.join(download_dir, download.suggested_filename)
            download.save_as(csv_path)
            print(f"✅ Successfully downloaded CSV data to: {csv_path}")
            # It's good practice to close the popup page
            popup.close()

        except TimeoutError:
            print("❌ ERROR: Timed out waiting for the CSV data download.")
            print("   The script could not download the CSV file after clicking the link.")
            screenshot_path = os.path.join(download_dir, "debug_screenshot_csv_error.png")
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
    run(playwright)
