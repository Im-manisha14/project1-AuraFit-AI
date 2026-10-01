import os
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from extensions import db
from models.user import User, UserProfile, StylePreference
from models.outfit import Outfit
from services.shopping_service import (
    SerpApiShoppingService,
    ProductValidator,
    detect_product_gender,
    parse_price_range,
    validate_price,
    validate_retailer,
    SKIN_TONE_PALETTES
)
from services.recommendation_engine import RecommendationEngine

def run_all_tests():
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("AURAFIT AI: FINAL LIVE SHOPPING RECOMMENDATION ENGINE TEST SUITE (Section 28)")
        print("=" * 80)

        service = SerpApiShoppingService()
        engine = RecommendationEngine()

        if not service.is_configured():
            print("ERROR: SERPAPI_KEY is not configured in backend/.env")
            return False

        # Create or fetch test mock user profiles for Female & Male
        female_user = User.query.filter_by(email="test_engine_female@aurafit.com").first()
        if not female_user:
            female_user = User(username="test_female", email="test_engine_female@aurafit.com")
            female_user.set_password("Password123!")
            db.session.add(female_user)
            db.session.commit()

        female_profile = UserProfile.query.filter_by(user_id=female_user.id).first()
        if not female_profile:
            female_profile = UserProfile(
                user_id=female_user.id,
                gender="female",
                age=25,
                body_type="hourglass",
                skin_tone="medium"
            )
            db.session.add(female_profile)
            db.session.commit()

        female_pref = StylePreference.query.filter_by(user_id=female_user.id).first()
        if not female_pref:
            female_pref = StylePreference(
                user_id=female_user.id,
                preferred_styles=["casual", "party"],
                preferred_colors=["olive", "emerald"]
            )
            db.session.add(female_pref)
            db.session.commit()

        male_user = User.query.filter_by(email="test_engine_male@aurafit.com").first()
        if not male_user:
            male_user = User(username="test_male", email="test_engine_male@aurafit.com")
            male_user.set_password("Password123!")
            db.session.add(male_user)
            db.session.commit()

        male_profile = UserProfile.query.filter_by(user_id=male_user.id).first()
        if not male_profile:
            male_profile = UserProfile(
                user_id=male_user.id,
                gender="male",
                age=28,
                body_type="athletic",
                skin_tone="fair"
            )
            db.session.add(male_profile)
            db.session.commit()

        male_pref = StylePreference.query.filter_by(user_id=male_user.id).first()
        if not male_pref:
            male_pref = StylePreference(
                user_id=male_user.id,
                preferred_styles=["casual", "smart-casual"],
                preferred_colors=["navy", "burgundy"]
            )
            db.session.add(male_pref)
            db.session.commit()

        passed_tests = 0
        total_tests = 10

        # ----------------------------------------------------------------------
        # TEST 6: Different skin tones (Fair / Medium / Deep)
        # Verify color query generation and palette influence (Section 5 & 6)
        # ----------------------------------------------------------------------
        print("\n--- TEST 6: Skin Tone Color Search Strategies (Fair / Medium / Deep) ---")
        t6_pass = True
        for tone in ['fair', 'medium', 'deep']:
            female_profile.skin_tone = tone
            palette = SKIN_TONE_PALETTES[tone]
            queries = service.generate_multi_queries('female', 'Party', 'Summer', palette, 'dress')
            print(f"Skin Tone '{tone}' generated {len(queries)} queries:")
            for q in queries[:4]:
                print(f"   * {q}")
            # Verify queries contain distinct colors from palette
            matched_colors_in_queries = [col for col in palette if any(col in q for q in queries)]
            if len(matched_colors_in_queries) >= 3:
                print(f"   [PASS] Found {len(matched_colors_in_queries)} compatible colors in search queries: {matched_colors_in_queries[:4]}")
            else:
                print(f"   [FAIL] Insufficient palette colors in queries for {tone}")
                t6_pass = False

        if t6_pass:
            print(">>> TEST 6 PASSED")
            passed_tests += 1
        else:
            print(">>> TEST 6 FAILED")

        # ----------------------------------------------------------------------
        # TEST 1: Female + Party + Summer + Under ₹500
        # Expected: Only real women's dresses, price <= 500, live retailer products, no men, no accessories
        # ----------------------------------------------------------------------
        print("\n--- TEST 1: Female + Party + Summer + Under ₹500 ---")
        female_profile.skin_tone = "medium"
        t0 = time.time()
        recs1 = service.fetch_live_recommendations(
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            compatible_colors=["olive", "emerald"],
            target_category="dress",
            limit=25,
            price_range="under_500"
        )
        duration1 = time.time() - t0
        print(f"Fetched {len(recs1)} products in {duration1:.2f}s")
        
        t1_pass = True
        if not recs1:
            print("[WARN] 0 items under 500 live right now (market dependent), checking honesty...")
        for p in recs1:
            price = p.get('price')
            gender = p.get('gender')
            cat = p.get('category')
            title = p.get('title', '').lower()
            store = p.get('store') or p.get('retailer')
            url = p.get('product_url')
            # Check conditions
            if price is None or price > 500:
                print(f"[FAIL] Product price ₹{price} exceeds ₹500: {title}")
                t1_pass = False
            if gender == 'male' or 'men' in title.split():
                print(f"[FAIL] Male product found: {title}")
                t1_pass = False
            if store and 'aurafit official' in store.lower():
                print(f"[FAIL] Mock store found: {store}")
                t1_pass = False
            if not service.is_valid_direct_url(url):
                print(f"[FAIL] Invalid direct URL: {url}")
                t1_pass = False
        
        if t1_pass:
            print(f">>> TEST 1 PASSED ({len(recs1)} valid live products <= ₹500)")
            passed_tests += 1
        else:
            print(">>> TEST 1 FAILED")

        # ----------------------------------------------------------------------
        # TEST 2: Female + Party + Summer + ₹500–₹1,000
        # Expected: Only valid live products in range
        # ----------------------------------------------------------------------
        print("\n--- TEST 2: Female + Party + Summer + ₹500–₹1,000 ---")
        t0 = time.time()
        recs2 = service.fetch_live_recommendations(
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            compatible_colors=["olive", "emerald"],
            target_category="dress",
            limit=25,
            price_range="500_1000"
        )
        duration2 = time.time() - t0
        print(f"Fetched {len(recs2)} products in {duration2:.2f}s")

        t2_pass = True
        for p in recs2:
            price = p.get('price')
            if price is None or price < 500 or price > 1000:
                print(f"[FAIL] Price ₹{price} outside 500-1000: {p.get('title')}")
                t2_pass = False
            if p.get('gender') == 'male':
                t2_pass = False
            if not service.is_valid_direct_url(p.get('product_url')):
                t2_pass = False

        if t2_pass and len(recs2) > 0:
            print(f">>> TEST 2 PASSED ({len(recs2)} products in ₹500-₹1,000 range)")
            passed_tests += 1
        else:
            print(">>> TEST 2 FAILED")

        # ----------------------------------------------------------------------
        # TEST 3: Female + Party + Summer + ₹1,000–₹2,500
        # Expected: Only valid live products in range (large recommendation pool target 25+)
        # ----------------------------------------------------------------------
        print("\n--- TEST 3: Female + Party + Summer + ₹1,000–₹2,500 ---")
        t0 = time.time()
        recs3 = service.fetch_live_recommendations(
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            compatible_colors=["olive", "emerald", "navy"],
            target_category="dress",
            limit=25,
            price_range="1000_2500"
        )
        duration3 = time.time() - t0
        print(f"Fetched {len(recs3)} products in {duration3:.2f}s")

        t3_pass = True
        for p in recs3:
            price = p.get('price')
            if price is None or price < 1000 or price > 2500:
                print(f"[FAIL] Price ₹{price} outside 1000-2500: {p.get('title')}")
                t3_pass = False
            if p.get('gender') == 'male':
                t3_pass = False
            if not service.is_valid_direct_url(p.get('product_url')):
                t3_pass = False

        if t3_pass and len(recs3) >= 15:
            print(f">>> TEST 3 PASSED ({len(recs3)} live products in ₹1,000-₹2,500 range, targeted 25+)")
            passed_tests += 1
        else:
            print(">>> TEST 3 FAILED")

        # ----------------------------------------------------------------------
        # TEST 4: Male + Party + Summer
        # Expected: Only valid men's clothing
        # ----------------------------------------------------------------------
        print("\n--- TEST 4: Male + Party + Summer ---")
        t0 = time.time()
        recs4 = service.fetch_live_recommendations(
            profile=male_profile,
            preferences=male_pref,
            occasion="party",
            season="summer",
            compatible_colors=["navy", "burgundy"],
            target_category="clothing",
            limit=20,
            price_range="all"
        )
        duration4 = time.time() - t0
        print(f"Fetched {len(recs4)} products in {duration4:.2f}s")

        t4_pass = True
        for p in recs4:
            gender = p.get('gender')
            title = p.get('title', '').lower()
            if gender == 'female' or any(bad in title for bad in ['women', 'woman', "women's", 'ladies', 'gown', 'lehenga']):
                print(f"[FAIL] Female product in male query: {title}")
                t4_pass = False

        if t4_pass and len(recs4) > 0:
            print(f">>> TEST 4 PASSED ({len(recs4)} valid men's products)")
            passed_tests += 1
        else:
            print(">>> TEST 4 FAILED")

        # ----------------------------------------------------------------------
        # TEST 5: Female + Winter
        # Expected: Winter-relevant women's dresses
        # ----------------------------------------------------------------------
        print("\n--- TEST 5: Female + Winter ---")
        t0 = time.time()
        recs5 = service.fetch_live_recommendations(
            profile=female_profile,
            preferences=female_pref,
            occasion="casual",
            season="winter",
            compatible_colors=["burgundy", "wine", "emerald"],
            target_category="dress",
            limit=20,
            price_range="all"
        )
        duration5 = time.time() - t0
        print(f"Fetched {len(recs5)} products in {duration5:.2f}s")

        t5_pass = True
        for p in recs5:
            if p.get('gender') == 'male':
                t5_pass = False
            cat_ok, _ = ProductValidator.validate_category(p.get('title'), target_category='dress', target_gender='female')
            if not cat_ok:
                t5_pass = False

        if t5_pass and len(recs5) > 0:
            print(f">>> TEST 5 PASSED ({len(recs5)} valid winter women's dresses)")
            passed_tests += 1
        else:
            print(">>> TEST 5 FAILED")

        # ----------------------------------------------------------------------
        # TEST 7: All Retailers Diversity
        # Expected: Multiple available retailers where API data permits
        # ----------------------------------------------------------------------
        print("\n--- TEST 7: Retailer Diversity under 'All Retailers' ---")
        # Check recs3 retailers
        retailers_found = set(p.get('store') or p.get('retailer') for p in recs3 if p.get('store') or p.get('retailer'))
        print(f"Distinct Retailers Found: {retailers_found}")
        if len(retailers_found) >= 2:
            print(f">>> TEST 7 PASSED (Found {len(retailers_found)} diverse retailers: {list(retailers_found)[:5]})")
            passed_tests += 1
        else:
            print(f"[FAIL] Only {len(retailers_found)} retailer found")

        # ----------------------------------------------------------------------
        # TEST 8: Specific Retailer (e.g. Myntra or Amazon)
        # Expected: Only selected retailer returned
        # ----------------------------------------------------------------------
        print("\n--- TEST 8: Specific Retailer Filter (Myntra) ---")
        recs8 = service.fetch_live_recommendations(
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            compatible_colors=["emerald", "navy"],
            target_category="dress",
            limit=15,
            price_range="all",
            retailer="Myntra"
        )
        print(f"Fetched {len(recs8)} products for retailer 'Myntra'")
        t8_pass = True
        for p in recs8:
            ret = (p.get('store') or p.get('retailer') or '').lower()
            if 'myntra' not in ret:
                print(f"[FAIL] Non-Myntra product returned: {ret} - {p.get('title')}")
                t8_pass = False

        if t8_pass and len(recs8) > 0:
            print(f">>> TEST 8 PASSED (100% Myntra products)")
            passed_tests += 1
        else:
            print(">>> TEST 8 FAILED")

        # ----------------------------------------------------------------------
        # TEST 9: Image consistency
        # Expected: Card image == persisted product image == detail page image
        # ----------------------------------------------------------------------
        print("\n--- TEST 9: Image Consistency (Card == DB == Detail) ---")
        sample_prod = recs3[0] if recs3 else recs2[0]
        ext_id = sample_prod['external_id']
        card_image = sample_prod['image_url']
        db_outfit = Outfit.query.filter_by(external_id=ext_id).first()
        t9_pass = False
        if db_outfit:
            db_image = db_outfit.image_url
            detail_dict = db_outfit.to_dict()
            detail_image = detail_dict['image_url']
            print(f"Card image:   {card_image}")
            print(f"DB image:     {db_image}")
            print(f"Detail image: {detail_image}")
            if card_image == db_image == detail_image and ProductValidator.validate_image(card_image)[0]:
                print(">>> TEST 9 PASSED (Exact image consistency preserved)")
                t9_pass = True
                passed_tests += 1
            else:
                print("[FAIL] Image mismatch between card, DB, or detail dict")
        else:
            print("[FAIL] Product not persisted in DB")

        # ----------------------------------------------------------------------
        # TEST 10: URL consistency
        # Expected: SHOP NOW == exact persisted direct product URL
        # ----------------------------------------------------------------------
        print("\n--- TEST 10: Direct URL Consistency (SHOP NOW == DB product_url) ---")
        card_url = sample_prod['product_url']
        shopping_url = sample_prod['shopping_url']
        db_url = db_outfit.product_url if db_outfit else None
        print(f"Card URL:     {card_url}")
        print(f"Shopping URL: {shopping_url}")
        print(f"DB URL:       {db_url}")
        if card_url == shopping_url == db_url and service.is_valid_direct_url(card_url):
            print(">>> TEST 10 PASSED (Exact direct retailer product URL preserved)")
            passed_tests += 1
        else:
            print("[FAIL] URL mismatch or non-direct URL detected")

        # ----------------------------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------------------------
        print("\n" + "=" * 80)
        print(f"FINAL TEST RESULTS: {passed_tests}/{total_tests} TESTS PASSED")
        print("=" * 80)
        return passed_tests == total_tests

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
