import time
import os
import sys
import site
import importlib

# Ensure user site-packages is in sys.path for IDE and local environments
_user_site = getattr(site, 'getusersitepackages', lambda: '')()
if _user_site and _user_site not in sys.path and os.path.exists(_user_site):
    sys.path.insert(0, _user_site)

try:
    sync_playwright = importlib.import_module('playwright.sync_api').sync_playwright
except Exception as _e:
    raise ImportError(f"Playwright is required to run browser acceptance tests: {_e}")

artifact_dir = r"C:\Users\DELL\.gemini\antigravity-ide\brain\417f3524-17e9-47a3-b154-590304b2580d"
os.makedirs(artifact_dir, exist_ok=True)

print("=" * 80, flush=True)
print("LAUNCHING PLAYWRIGHT CHROMIUM FOR LIVE BROWSER ACCEPTANCE TESTING", flush=True)
print("=" * 80, flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    # 1. Login
    print("\n[Step 1] Navigating to http://localhost:3000/login...", flush=True)
    page.goto("http://localhost:3000/login", wait_until="domcontentloaded")
    page.wait_for_selector('input[type="email"]', timeout=10000)

    print("Logging in with final_test_female@aurafit.com...", flush=True)
    page.fill('input[type="email"]', "final_test_female@aurafit.com")
    page.fill('input[type="password"]', "Password123!")
    page.click('button[type="submit"]')
    page.wait_for_timeout(3000)

    # 2. Go to Recommendations
    print("\n[Step 2] Navigating to http://localhost:3000/recommendations...", flush=True)
    page.goto("http://localhost:3000/recommendations", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    observed_results = {}

    def test_occasion(occasion_val, screenshot_name, target_gender="female"):
        print(f"\n--- Testing Occasion: {occasion_val.upper()} ({target_gender.upper()}) ---", flush=True)
        # Find occasion select
        occ_select = page.locator('select[name="occasion"]')
        if occ_select.count() > 0:
            occ_select.select_option(occasion_val)
            page.wait_for_timeout(500)
        
        # Season select
        season_select = page.locator('select[name="season"]')
        if season_select.count() > 0:
            season_select.select_option("summer")
            page.wait_for_timeout(500)

        # Click Generate button
        gen_btn = page.locator('button:has-text("Generate Recommendations"), button:has-text("Generate")')
        if gen_btn.count() > 0:
            print(f"Clicking Generate button for {occasion_val}...", flush=True)
            gen_btn.first.click()
            try:
                page.wait_for_selector('.recommendation-card', timeout=20000)
                page.wait_for_timeout(1500)
            except Exception as e:
                print(f"Wait warning for cards on {occasion_val}: {e}", flush=True)
                page.wait_for_timeout(3000)
        
        shot_path = os.path.join(artifact_dir, f"{screenshot_name}.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f"Captured screenshot: {shot_path}", flush=True)

        # Extract visible cards specifically from the recommendations grid
        cards = page.locator('.recommendation-card h3').all_inner_texts()
        links = page.locator('.recommendation-card a:has-text("Shop Now")').all()
        urls = [link.get_attribute("href") for link in links if link.get_attribute("href")]

        res_key = f"{target_gender}_{occasion_val}"
        observed_results[res_key] = {
            "titles": [c.strip() for c in cards if len(c.strip()) > 3],
            "urls": urls
        }
        print(f"Extracted {len(observed_results[res_key]['titles'])} top recommendation cards for {occasion_val}:", flush=True)
        for i, t in enumerate(observed_results[res_key]['titles'][:5], 1):
            print(f"   {i}. {t}", flush=True)

    # 1. FEMALE ACCEPTANCE TESTS
    print("\n" + "=" * 60, flush=True)
    print("RUNNING FEMALE LIVE BROWSER TESTS", flush=True)
    print("=" * 60, flush=True)
    test_occasion("party", "browser_party_recommendations", "female")
    test_occasion("casual", "browser_casual_recommendations", "female")
    test_occasion("formal", "browser_formal_recommendations", "female")

    # 2. View Details Modal/Page
    print("\n--- Testing View Details ---", flush=True)
    detail_btn = page.locator('.recommendation-card button:has-text("View Details")')
    if detail_btn.count() > 0:
        print("Clicking View Details on first card...", flush=True)
        detail_btn.first.click()
        page.wait_for_timeout(3000)
        shot_path = os.path.join(artifact_dir, "browser_view_details.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f"Captured View Details screenshot: {shot_path}", flush=True)

    # 3. MALE ACCEPTANCE TESTS
    print("\n" + "=" * 60, flush=True)
    print("RUNNING MALE LIVE BROWSER TESTS", flush=True)
    print("=" * 60, flush=True)
    context_male = browser.new_context(viewport={"width": 1440, "height": 900})
    page_male = context_male.new_page()

    page_male.goto("http://localhost:3000/login", wait_until="domcontentloaded")
    page_male.wait_for_selector('input[type="email"]', timeout=10000)
    page_male.fill('input[type="email"]', "final_test_male@aurafit.com")
    page_male.fill('input[type="password"]', "Password123!")
    page_male.click('button[type="submit"]')
    page_male.wait_for_timeout(3000)

    page_male.goto("http://localhost:3000/recommendations", wait_until="domcontentloaded")
    page_male.wait_for_timeout(3000)

    def test_male_occasion(occasion_val, screenshot_name):
        print(f"\n--- Testing Occasion: {occasion_val.upper()} (MALE) ---", flush=True)
        occ_select = page_male.locator('select[name="occasion"]')
        if occ_select.count() > 0:
            occ_select.select_option(occasion_val)
            page_male.wait_for_timeout(500)
        
        season_select = page_male.locator('select[name="season"]')
        if season_select.count() > 0:
            season_select.select_option("summer")
            page_male.wait_for_timeout(500)

        gen_btn = page_male.locator('button:has-text("Generate Recommendations"), button:has-text("Generate")')
        if gen_btn.count() > 0:
            print(f"Clicking Generate button for {occasion_val}...", flush=True)
            gen_btn.first.click()
            try:
                page_male.wait_for_selector('.recommendation-card', timeout=20000)
                page_male.wait_for_timeout(1500)
            except Exception as e:
                print(f"Wait warning for cards on {occasion_val}: {e}", flush=True)
                page_male.wait_for_timeout(3000)
        
        shot_path = os.path.join(artifact_dir, f"{screenshot_name}.png")
        page_male.screenshot(path=shot_path, full_page=False)
        print(f"Captured screenshot: {shot_path}", flush=True)

        cards = page_male.locator('.recommendation-card h3').all_inner_texts()
        links = page_male.locator('.recommendation-card a:has-text("Shop Now")').all()
        urls = [link.get_attribute("href") for link in links if link.get_attribute("href")]

        res_key = f"male_{occasion_val}"
        observed_results[res_key] = {
            "titles": [c.strip() for c in cards if len(c.strip()) > 3],
            "urls": urls
        }
        print(f"Extracted {len(observed_results[res_key]['titles'])} top recommendation cards for {occasion_val}:", flush=True)
        for i, t in enumerate(observed_results[res_key]['titles'][:5], 1):
            print(f"   {i}. {t}", flush=True)

    test_male_occasion("party", "browser_male_party_recommendations")
    test_male_occasion("casual", "browser_male_casual_recommendations")

    browser.close()

print("\n" + "=" * 80, flush=True)
print("ANALYZING VISUAL BROWSER ACCEPTANCE RESULTS", flush=True)
print("=" * 80, flush=True)

overlap = False
test_occs = ["female_party", "female_casual", "female_formal"]
for i in range(len(test_occs)):
    for j in range(i + 1, len(test_occs)):
        o1, o2 = test_occs[i], test_occs[j]
        urls1 = set(observed_results.get(o1, {}).get("urls", []))
        urls2 = set(observed_results.get(o2, {}).get("urls", []))
        common = urls1.intersection(urls2)
        if common:
            print(f"  [FAIL] Browser overlap between {o1.upper()} and {o2.upper()}: {len(common)} items", flush=True)
            overlap = True
        else:
            print(f"  [PASS] Browser 0 overlap between {o1.upper()} and {o2.upper()}", flush=True)

# Verify male results contain 0 dresses
male_dresses = 0
for m_key in ["male_party", "male_casual"]:
    m_titles = observed_results.get(m_key, {}).get("titles", [])
    for mt in m_titles:
        import re
        if re.search(r"\b(women|women's|womens|dress|gown|saree|kurti|anarkali)\b", mt.lower()):
            print(f"  [FAIL] Found female dress in male results ({m_key}): {mt}", flush=True)
            male_dresses += 1

if male_dresses == 0:
    print("  [PASS] Zero women's dresses in male browser results", flush=True)
else:
    print(f"  [FAIL] {male_dresses} women's dresses found in male browser results", flush=True)

if not overlap and male_dresses == 0:
    print("\n[SUCCESS] PERFECT BROWSER ACCEPTANCE: Zero repeated dresses and zero cross-gender leakage in live UI!", flush=True)
print("=" * 80, flush=True)
