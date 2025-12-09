import re
from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        print("Navigating to the funds page...")
        page.goto("https://pekaotfi.pl/produkty/fundusze-inwestycyjne", timeout=60000)

        print("Looking for cookie banner...")
        try:
            cookie_banner = page.locator("#onetrust-accept-btn-handler")
            if cookie_banner.is_visible(timeout=10000):
                print("Cookie banner found, accepting...")
                cookie_banner.click()
                page.wait_for_load_state('networkidle')
            else:
                print("Cookie banner not found or not visible within the timeout.")
        except Exception as e:
            print(f"Could not handle cookie banner: {e}")


        print("Taking a snapshot of the page...")
        page.screenshot(path="pekao_fundusze_snapshot.png")
        print("Snapshot saved to 'pekao_fundusze_snapshot.png'")


        print("\nExtracting fund links...")
        
        link_elements = page.locator(".product-card__name a").all()

        if not link_elements:
            print("No fund links found with the selector '.product-card__name a'.")

        report_content = ""
        for link_element in link_elements:
            text = link_element.inner_text()
            url = link_element.get_attribute("href")
            
            if url and not url.startswith('http'):
                url = f"https://pekaotfi.pl{url}"

            print(f"- Text: \"{text}\"\n  URL: {url}\n")
            report_content += f"- Text: \"{text}\"\n  URL: {url}\n\n"

        print("Writing links to link_report.txt")
        with open("link_report.txt", "w") as f:
            f.write(report_content)
        print("Successfully wrote links to link_report.txt")


    except Exception as e:
        print(f"An error occurred: {e}")
        page.screenshot(path="error_screenshot.png")
        print("Saved an error screenshot to error_screenshot.png")

finally:
    print("Closing browser.")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)