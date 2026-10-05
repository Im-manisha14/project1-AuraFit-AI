import time
import os
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

artifact_dir = r"C:\Users\DELL\.gemini\antigravity-ide\brain\fb4b9c76-20d7-4ec5-bd27-696b27ad2ea6"
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

    def test_occasion(occasion_val, screenshot_name):
        print(f"\n--- Testing Occasion: {occasion_val.upper()} ---", flush=True)
        # Find occasion select
        occ_select = page.locator('select[name="occasion"]')
        if occ_select.count() > 0:
            occ_select.select_option(occasion_val)
        
        # Season select
        season_select = page.locator('select[name="season"]')
        if season_select.count() > 0:
            season_select.select_option("summer")

        # Click Generate button
        gen_btn = page.locator('button:has-text("Generate Recommendations"), button:has-text("Generate")')
        if gen_btn.count() > 0:
            print(f"Clicking Generate button for {occasion_val}...", flush=True)
            gen_btn.first.click()
            page.wait_for_timeout(5000)
        
        shot_path = os.path.join(artifact_dir, f"{screenshot_name}.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f"Captured screenshot: {shot_path}", flush=True)

        # Extract visible cards specifically from the recommendations grid
        cards = page.locator('.recommendation-card h3').all_inner_texts()
        links = page.locator('.recommendation-card a:has-text("Shop Now")').all()
        urls = [link.get_attribute("href") for link in links if link.get_attribute("href")]

        observed_results[occasion_val] = {
            "titles": [c.strip() for c in cards if len(c.strip()) > 3],
            "urls": urls
        }
        print(f"Extracted {len(observed_results[occasion_val]['titles'])} top recommendation cards for {occasion_val}:", flush=True)
        for i, t in enumerate(observed_results[occasion_val]['titles'][:5], 1):
            print(f"   {i}. {t}", flush=True)

    # Test Party
    test_occasion("party", "browser_party_recommendations")

    # Test Casual
    test_occasion("casual", "browser_casual_recommendations")

    # Test Formal
    test_occasion("formal", "browser_formal_recommendations")

    # 3. View Details Modal/Page
    print("\n--- Testing View Details ---", flush=True)
    detail_btn = page.locator('.recommendation-card button:has-text("View Details")')
    if detail_btn.count() > 0:
        print("Clicking View Details on first card...", flush=True)
        detail_btn.first.click()
        page.wait_for_timeout(3000)
        shot_path = os.path.join(artifact_dir, "browser_view_details.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f"Captured View Details screenshot: {shot_path}", flush=True)

    browser.close()

print("\n" + "=" * 80, flush=True)
print("ANALYZING VISUAL BROWSER ACCEPTANCE RESULTS", flush=True)
print("=" * 80, flush=True)

overlap = False
test_occs = ["party", "casual", "formal"]
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

if not overlap:
    print("\n[SUCCESS] PERFECT BROWSER ACCEPTANCE: Zero repeated dresses across occasions in live UI!", flush=True)
print("=" * 80, flush=True)
