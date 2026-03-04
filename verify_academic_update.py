from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto("http://localhost:8050")
            page.wait_for_selector("#tabs-main", timeout=10000)

            # Screenshot Sidebar/Metadata
            print("Capturing Sidebar Metadata...")
            page.screenshot(path="verification_metadata.png", full_page=True)

            # Navigate to Systems Analytics
            page.get_by_text("Systems Analytics").click()
            page.wait_for_selector("#scatter-capacity-adj", timeout=10000)

            print("Checking WPI graph controls...")
            page.locator("#y-axis-selector").click()
            page.get_by_text("GHEI (Adjusted)").click()
            page.locator("#trendline-toggle label").filter(has_text="Show Trendline (OLS)").click()

            time.sleep(3)
            print("Capturing Systems Analytics...")
            page.screenshot(path="verification_systems_analytics_academic.png", full_page=True)

            # Navigate to Robustness
            page.get_by_text("Robustness and Limits").click()
            time.sleep(2)
            print("Capturing Robustness...")
            page.screenshot(path="verification_robustness.png", full_page=True)

            print("Done.")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="error_verification.png", full_page=True)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
