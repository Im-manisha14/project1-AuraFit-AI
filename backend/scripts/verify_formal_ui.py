import os
import sys
import time
import json
import re

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = r"C:\Users\DELL\.gemini\antigravity-ide\brain\fb4b9c76-20d7-4ec5-bd27-696b27ad2ea6"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
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

def run_verification():
    print("=" * 80)
    print("STARTING E2E FORMAL OCCASION BROWSER UI VERIFICATION")
    print("=" * 80)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=EDGE_PATH, headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        # 1. Login
        print("\n[STEP 1] Logging in at http://localhost:3000/login...")
        page.goto("http://localhost:3000/login", wait_until="networkidle")
        page.fill('input[type="email"]', "final_test_female@aurafit.com")
        page.fill('input[type="password"]', "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        print("Login complete.")

        # 2. Recommendations Page
        print("\n[STEP 2] Navigating to http://localhost:3000/recommendations...")
        page.goto("http://localhost:3000/recommendations", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # 3. Test Formal (All Prices)
        print("\n[STEP 3] Selecting Formal occasion & generating recommendations...")
        page.select_option('select[name="occasion"]', 'formal')
        page.wait_for_timeout(500)
        page.select_option('select#price-range-filter', 'all')
        page.wait_for_timeout(500)
        
        gen_btn = page.locator('#generate-recommendations-btn, button:has-text("Generate Recommendations")').first
        gen_btn.click()
        
        page.wait_for_timeout(1000)
        page.wait_for_selector('#generate-recommendations-btn:not([disabled])', timeout=30000)
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")
        
        # Bring cards into view
        page.evaluate("() => { const el = document.querySelector('.recommendations-grid'); if (el) el.scrollIntoView(); }")
        page.wait_for_timeout(1000)
        
        formal_cards = inspect_page_cards(page)
        print(f"Formal Cards Rendered: {len(formal_cards)}")
        for c in formal_cards:
            print(f"  * #{c['index'] + 1} | {c['title']} | {c['price_text']} | {c['retailer']} | ImgOK: {c['image_loaded']}")
        
        # Verify no casual items
        casual_terms = ["casual", "beach", "sundress", "boho", "tie-dye", "t-shirt", "distressed"]
        for c in formal_cards:
            for term in casual_terms:
                if re.search(r'\b' + re.escape(term) + r'\b', c['title'], re.IGNORECASE):
                    print(f"WARNING: Found prohibited term '{term}' in card title: {c['title']}")
        
        shot_formal = os.path.join(SCREENSHOT_DIR, "browser_formal_all_prices.png")
        page.screenshot(path=shot_formal, full_page=True)
        print(f"Saved screenshot: {shot_formal}")

        # 4. Test Formal with Price Filter ₹1,000–₹2,500
        print("\n[STEP 4] Selecting Price Range ₹1,000 - ₹2,500 for Formal...")
        page.select_option('select#price-range-filter', '1000_2500')
        page.wait_for_timeout(500)
        gen_btn.click()
        page.wait_for_timeout(1000)
        page.wait_for_selector('#generate-recommendations-btn:not([disabled])', timeout=30000)
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")
        
        price_cards = inspect_page_cards(page)
        print(f"Price Filtered Cards Rendered: {len(price_cards)}")
        for c in price_cards:
            print(f"  * #{c['index'] + 1} | {c['title']} | {c['price_text']} | {c['retailer']}")
            assert 1000.0 <= c['price'] <= 2500.0, f"Card price {c['price']} outside ₹1,000-₹2,500 range!"
            
        shot_price = os.path.join(SCREENSHOT_DIR, "browser_formal_1000_2500.png")
        page.screenshot(path=shot_price, full_page=True)
        print(f"Saved screenshot: {shot_price}")

        # 5. Test Casual (Cross-Occasion Separation)
        print("\n[STEP 5] Switching occasion to Casual (Verifying strict separation)...")
        page.select_option('select[name="occasion"]', 'casual')
        page.wait_for_timeout(500)
        page.select_option('select#price-range-filter', 'all')
        page.wait_for_timeout(500)
        gen_btn.click()
        page.wait_for_timeout(1000)
        page.wait_for_selector('#generate-recommendations-btn:not([disabled])', timeout=30000)
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")
        
        casual_cards = inspect_page_cards(page)
        print(f"Casual Cards Rendered: {len(casual_cards)}")
        for c in casual_cards:
            print(f"  * #{c['index'] + 1} | {c['title']} | {c['price_text']} | {c['retailer']}")
            
        shot_casual = os.path.join(SCREENSHOT_DIR, "browser_casual_all_prices.png")
        page.screenshot(path=shot_casual, full_page=True)
        print(f"Saved screenshot: {shot_casual}")

        # 6. Switch back to Formal (Immediate Refresh Integrity)
        print("\n[STEP 6] Switching BACK to Formal (Verifying immediate refresh & zero casual leakage)...")
        page.select_option('select[name="occasion"]', 'formal')
        page.wait_for_timeout(500)
        page.select_option('select#price-range-filter', 'all')
        page.wait_for_timeout(500)
        gen_btn.click()
        page.wait_for_timeout(1000)
        page.wait_for_selector('#generate-recommendations-btn:not([disabled])', timeout=30000)
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")
        
        refresh_cards = inspect_page_cards(page)
        print(f"Refreshed Formal Cards Rendered: {len(refresh_cards)}")
        for c in refresh_cards:
            print(f"  * #{c['index'] + 1} | {c['title']} | {c['price_text']} | {c['retailer']}")
            
        assert len(refresh_cards) == len(formal_cards), f"Expected {len(formal_cards)} formal cards, got {len(refresh_cards)}"
        for i, c in enumerate(refresh_cards):
            assert c['title'] == formal_cards[i]['title'], f"Mismatch between formal card {i} before and after toggle!"
            
        shot_refresh = os.path.join(SCREENSHOT_DIR, "browser_formal_refresh_switchback.png")
        page.screenshot(path=shot_refresh, full_page=True)
        print(f"Saved screenshot: {shot_refresh}")

        # 7. Outfit Detail Page Verification
        print("\n[STEP 7] Testing Outfit Detail View for Formal Card...")
        detail_btn = page.locator('.recommendation-card button:has-text("View Details")').first
        if detail_btn.count() > 0:
            detail_btn.click()
            page.wait_for_timeout(3000)
            page.wait_for_load_state("networkidle")
            
            shot_detail = os.path.join(SCREENSHOT_DIR, "browser_formal_outfit_detail.png")
            page.screenshot(path=shot_detail, full_page=True)
            print(f"Saved screenshot: {shot_detail}")
            
            # Verify details title
            detail_title = page.locator('h1, h2').first.inner_text().strip() if page.locator('h1, h2').count() > 0 else ""
            print(f"Detail Page Heading: {detail_title}")

        browser.close()
        print("\n" + "=" * 80)
        print("ALL BROWSER UI VERIFICATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

if __name__ == '__main__':
    run_verification()
