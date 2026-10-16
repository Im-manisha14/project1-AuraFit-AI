import os
import sys
import time
import json
import re
import importlib

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    _pw = importlib.import_module("playwright.sync_api")
    sync_playwright = getattr(_pw, "sync_playwright")
except ImportError:
    import site
    user_site = site.getusersitepackages()
    if user_site not in sys.path:
        sys.path.insert(0, user_site)
    _pw = importlib.import_module("playwright.sync_api")
    sync_playwright = getattr(_pw, "sync_playwright")

SCREENSHOT_DIR = r"C:\Users\DELL\.gemini\antigravity-ide\brain\fb4b9c76-20d7-4ec5-bd27-696b27ad2ea6"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def inspect_page_cards(page):
    cards = page.locator('.recommendation-card')
    count = cards.count()
    items = []
    for i in range(count):
        c = cards.nth(i)
        title_el = c.locator('h3').first
        title = title_el.inner_text().strip() if title_el.count() > 0 else ""
        
        price_text = ""
        price_val = 0.0
        price_el = c.locator('span.text-lg.font-bold.text-amber-600').first
        if price_el.count() > 0:
            price_text = price_el.inner_text().strip()
            match = re.search(r'[\d,]+(?:\.\d+)?', price_text)
            if match:
                price_val = float(match.group(0).replace(',', ''))
                
        ret_el = c.locator('.text-gray-800').first
        retailer = ret_el.inner_text().strip() if ret_el.count() > 0 else ""
        
        img_el = c.locator('img').first
        img_src = img_el.get_attribute('src') if img_el.count() > 0 else ""
        img_loaded = False
        if img_el.count() > 0:
            try:
                img_loaded = page.evaluate("(img) => img.complete && img.naturalWidth > 0", img_el.element_handle())
            except Exception:
                img_loaded = False
                
        shop_el = c.locator('a:has-text("Shop Now")').first
        shop_url = shop_el.get_attribute('href') if shop_el.count() > 0 else ""
        
        items.append({
            'index': i,
            'title': title,
            'price': price_val,
            'price_text': price_text,
            'retailer': retailer,
            'image_url': img_src,
            'image_loaded': img_loaded,
            'shop_url': shop_url
        })
    return items

def test_and_capture():
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        page = context.new_page()

        print("[LOGIN] Authenticating as final_test_female@aurafit.com...")
        page.goto("http://localhost:3000/login", wait_until="networkidle")
        page.fill('input[type="email"]', "final_test_female@aurafit.com")
        page.fill('input[type="password"]', "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)

        print("[NAVIGATE] Going to /recommendations...")
        page.goto("http://localhost:3000/recommendations", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # List of test cases: (name, occasion, price_range, screenshot_name)
        test_cases = [
            ("Formal Dresses (₹500–₹1,000)", "formal", "500_1000", "browser_formal_500_1000.png"),
            ("Formal Dresses (₹1,000–₹2,500)", "formal", "1000_2500", "browser_formal_1000_2500.png"),
            ("Formal Dresses (₹2,500–₹5,000)", "formal", "2500_5000", "browser_formal_2500_5000.png"),
            ("Formal Dresses (All Prices)", "formal", "all", "browser_formal_all_prices.png"),
            ("Formal Dresses Empty State (Under ₹500)", "formal", "under_500", "browser_empty_state_formal_under500.png"),
            ("Office Dresses", "office", "all", "browser_office_dresses.png"),
            ("Casual Dresses", "casual", "all", "browser_casual_dresses.png"),
            ("Party Dresses", "party", "all", "browser_party_dresses.png"),
            ("Wedding Dresses", "wedding", "all", "browser_wedding_dresses.png"),
            ("Date Dresses", "date", "all", "browser_date_dresses.png"),
            ("Evening Dresses", "evening", "all", "browser_evening_dresses.png"),
            ("Traditional Dresses", "traditional", "all", "browser_traditional_dresses.png"),
        ]

        for label, occ, pr, img_name in test_cases:
            print(f"\n==================================================")
            print(f"RUNNING TEST: {label} (Occasion={occ}, Price={pr})")
            print(f"==================================================")

            # Select Occasion
            page.select_option('select[name="occasion"]', occ)
            page.wait_for_timeout(500)

            # Select Price Range
            page.select_option('select#price-range-filter', pr)
            page.wait_for_timeout(500)

            # Click Generate Button
            gen_btn = page.locator('#generate-recommendations-btn, button:has-text("Generate Recommendations")').first
            gen_btn.click()
            
            # Wait for button to transition through loading and become enabled again
            page.wait_for_timeout(1000)
            page.wait_for_selector('#generate-recommendations-btn:not([disabled])', timeout=30000)
            page.wait_for_timeout(2000)
            page.wait_for_load_state("networkidle")

            # Scroll down to bring cards into view for framer-motion whileInView
            page.evaluate("() => { const el = document.querySelector('.recommendations-grid'); if (el) el.scrollIntoView(); }")
            page.wait_for_timeout(1000)

            # Check for cards or empty state
            cards = inspect_page_cards(page)
            empty_state = page.locator('text=No outfits found matching your exact filters').count() > 0 or page.locator('text=No Outfits Found').count() > 0

            print(f"Rendered Cards: {len(cards)} | Empty State Displayed: {empty_state}")
            for c in cards:
                print(f"  * [{c['index'] + 1}] {c['title']} | Price: {c['price_text']} | Retailer: {c['retailer']} | ImgOK: {c['image_loaded']}")

            # Capture Screenshot
            shot_path = os.path.join(SCREENSHOT_DIR, img_name)
            page.screenshot(path=shot_path, full_page=True)
            print(f"Saved Screenshot: {shot_path}")

            results[label] = {
                'occasion': occ,
                'price_range': pr,
                'card_count': len(cards),
                'empty_state': empty_state,
                'screenshot': img_name,
                'items': cards
            }

        # ----------------------------------------------------
        # TEST: Outfit Details Page & Similar Recommendations Isolation
        # ----------------------------------------------------
        print("\n==================================================")
        print("RUNNING TEST: Outfit Details Page (Formal) & Similar Isolation")
        print("==================================================")
        page.select_option('select[name="occasion"]', 'formal')
        page.locator('#generate-recommendations-btn, button:has-text("Generate Recommendations")').first.click()
        page.wait_for_timeout(1000)
        page.wait_for_selector('#generate-recommendations-btn:not([disabled])', timeout=30000)
        page.wait_for_timeout(2000)

        # Click View Details on first card
        detail_btn = page.locator('.recommendation-card button:has-text("View Details")').first
        if detail_btn.count() > 0:
            detail_btn.click()
            page.wait_for_timeout(3000)
            page.wait_for_load_state("networkidle")
            
            detail_shot_path = os.path.join(SCREENSHOT_DIR, "browser_formal_outfit_detail.png")
            page.screenshot(path=detail_shot_path, full_page=True)
            print(f"Saved Detail Screenshot: {detail_shot_path}")
            
            # Check similar cards on detail page
            sim_cards = page.locator('.similar-outfit-card, .recommendation-card')
            print(f"Similar outfit cards found on detail page: {sim_cards.count()}")

        browser.close()

    # Save summary report
    summary_path = os.path.join(SCREENSHOT_DIR, "browser_verification_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n[DONE] Browser verification complete. Summary saved to {summary_path}")

if __name__ == '__main__':
    test_and_capture()
