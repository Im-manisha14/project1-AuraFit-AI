from playwright.sync_api import sync_playwright

def scrape_sample():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.google.com/search?q=women+formal+dress&tbm=shop", wait_until="domcontentloaded")
        print("Page title:", page.title())
        print("Page URL:", page.url)
        browser.close()

if __name__ == "__main__":
    scrape_sample()

