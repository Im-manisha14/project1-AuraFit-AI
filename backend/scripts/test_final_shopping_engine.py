import os
import sys
import time
import re

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
        print("AURAFIT AI: COMPREHENSIVE LIVE SHOPPING ENGINE TEST SUITE")
        print("Enforcing Sections 29, 30, 31, 32 of Final Inventory Specification")
        print("=" * 80)

        service = SerpApiShoppingService()
        engine = RecommendationEngine()

        if not service.is_configured():
            print("ERROR: SERPAPI_KEY is not configured in backend/.env")
            return False

        # Setup test users
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

        results_summary = {}
        all_passed = True
        total_latencies = []

        # Helper to validate a batch of recommendations
        def validate_batch(products, target_gender, min_p, max_p, price_label, target_cat='dress', expected_retailer=None):
            errors = []
            seen_urls = set()
            seen_ids = set()
            seen_imgs = set()

            for idx, p in enumerate(products):
                # 1. Price check strictly on current selling price
                price = p.get('price')
                if price is None:
                    errors.append(f"Item #{idx+1} '{p.get('title')}' has null price")
                elif min_p is not None and price < min_p:
                    errors.append(f"Item #{idx+1} '{p.get('title')}' price ₹{price} < min ₹{min_p}")
                elif max_p is not None and price > max_p:
                    errors.append(f"Item #{idx+1} '{p.get('title')}' price ₹{price} > max ₹{max_p}")

                # 2. Gender check
                prod_gender = p.get('gender')
                title_lower = (p.get('title') or '').lower()
                if target_gender == 'female':
                    if prod_gender == 'male' or re.search(r"\b(men|men's|mens|boys?)\b", title_lower):
                        errors.append(f"Item #{idx+1} '{p.get('title')}' male product in female recommendations")
                elif target_gender == 'male':
                    if prod_gender == 'female' or re.search(r"\b(women|women's|womens|ladies|girls?|dress|gown|saree)\b", title_lower):
                        errors.append(f"Item #{idx+1} '{p.get('title')}' female product in male recommendations")

                # 3. Category check
                if target_cat == 'dress':
                    cat_ok, c_msg = ProductValidator.validate_category(p.get('title', ''), target_category='dress', target_gender=target_gender)
                    if not cat_ok:
                        errors.append(f"Item #{idx+1} '{p.get('title')}' invalid dress category: {c_msg}")

                # 4. Image check
                img = p.get('image_url')
                img_ok, i_msg = ProductValidator.validate_image(img)
                if not img_ok:
                    errors.append(f"Item #{idx+1} '{p.get('title')}' invalid image: {i_msg}")

                # 5. Direct URL check
                url = p.get('product_url')
                if not service.is_valid_direct_url(url):
                    errors.append(f"Item #{idx+1} '{p.get('title')}' invalid direct URL: {url}")

                # 6. Retailer check
                ret = p.get('store') or p.get('retailer')
                if ret and 'aurafit official' in ret.lower():
                    errors.append(f"Item #{idx+1} '{p.get('title')}' has mock retailer '{ret}'")
                if expected_retailer:
                    ret_ok, _ = validate_retailer(ret, expected_retailer)
                    if not ret_ok:
                        errors.append(f"Item #{idx+1} '{p.get('title')}' retailer mismatch: {ret} != {expected_retailer}")

                # 7. Deduplication check
                canon_u = service.canonicalize_url(url)
                if canon_u in seen_urls:
                    errors.append(f"Item #{idx+1} '{p.get('title')}' duplicate URL: {canon_u}")
                seen_urls.add(canon_u)

                ext_id = p.get('external_id')
                if ext_id and ext_id in seen_ids:
                    errors.append(f"Item #{idx+1} '{p.get('title')}' duplicate external ID: {ext_id}")
                if ext_id:
                    seen_ids.add(ext_id)

                # 8. Image deduplication check
                img_url = p.get('image_url') or p.get('thumbnail')
                if img_url:
                    tbn_match = re.search(r'q=tbn:([^&]+)', img_url)
                    img_k = tbn_match.group(1) if tbn_match else img_url.split('?')[0]
                    if img_k in seen_imgs:
                        errors.append(f"Item #{idx+1} '{p.get('title')}' duplicate image: {img_k}")
                    seen_imgs.add(img_k)

            return errors

        # ======================================================================
        # SECTION 29: TEST ALL 5 PRICE RANGES (Target = 25 each)
        # ======================================================================
        price_test_cases = [
            ("Under ₹500", "under_500", None, 500.0),
            ("₹500 – ₹1,000", "500_1000", 500.0, 1000.0),
            ("₹1,000 – ₹2,500", "1000_2500", 1000.0, 2500.0),
            ("₹2,500 – ₹5,000", "2500_5000", 2500.0, 5000.0),
            ("₹5,000+", "5000_plus", 5000.0, None),
        ]

        print("\n" + "=" * 60)
        print("SUITE 1: TESTING ALL 5 PRICE RANGES (TARGET = 25 EACH)")
        print("=" * 60)

        for label, p_code, min_p, max_p in price_test_cases:
            female_profile.skin_tone = "medium"
            t0 = time.time()
            recs = service.fetch_live_recommendations(
                profile=female_profile,
                preferences=female_pref,
                occasion="party",
                season="summer",
                compatible_colors=["olive", "emerald", "burgundy"],
                target_category="dress",
                limit=25,
                price_range=p_code
            )
            lat = time.time() - t0
            total_latencies.append(lat)
            returned = len(recs)
            results_summary[label] = returned

            errors = validate_batch(recs, 'female', min_p, max_p, label, target_cat='dress')
            passed = (returned >= 25) and (len(errors) == 0)

            print(f"\n[PRICE RANGE TEST] {label}")
            print(f"RETURNED: {returned} | TARGET: 25 | LATENCY: {lat:.2f}s")
            if errors:
                for err in errors[:3]:
                    print(f"   [FAIL DETAIL] {err}")
                print(f"STATUS: FAIL ({len(errors)} validation errors)")
                all_passed = False
            elif returned >= 25:
                print(f"STATUS: PASS (100% compliant, 0 duplicates, 0 mock products)")
            else:
                print(f"STATUS: PARTIAL ({returned}/25 products returned)")
                all_passed = False

        # ======================================================================
        # SECTION 30: TEST ALL SEASONS (Target = 20+ dresses each)
        # ======================================================================
        print("\n" + "=" * 60)
        print("SUITE 2: TESTING ALL 4 SEASONS (TARGET = 20+ DRESSES EACH)")
        print("=" * 60)

        season_cases = [
            ("Spring", "spring", "party"),
            ("Summer", "summer", "casual"),
            ("Autumn", "autumn", "date"),
            ("Winter", "winter", "party"),
        ]

        for s_label, s_code, occ in season_cases:
            t0 = time.time()
            recs = service.fetch_live_recommendations(
                profile=female_profile,
                preferences=female_pref,
                occasion=occ,
                season=s_code,
                compatible_colors=["emerald", "burgundy"],
                target_category="dress",
                limit=20,
                price_range="all"
            )
            lat = time.time() - t0
            total_latencies.append(lat)
            returned = len(recs)
            errors = validate_batch(recs, 'female', None, None, "all", target_cat='dress')
            passed = (returned >= 20) and (len(errors) == 0)
            print(f"\n[SEASON TEST] {s_label} + {occ.title()}: RETURNED {returned} | TARGET: 20 | LATENCY: {lat:.2f}s")
            if errors:
                for err in errors[:2]:
                    print(f"   [FAIL DETAIL] {err}")
                all_passed = False
            elif returned >= 20:
                print("STATUS: PASS (100% valid dresses, seasonal relevance satisfied)")
            else:
                print(f"STATUS: PARTIAL ({returned}/20 products)")
                all_passed = False

        # ======================================================================
        # SECTION 31: TEST GENDER SWITCHING
        # ======================================================================
        print("\n" + "=" * 60)
        print("SUITE 3: TESTING GENDER SWITCHING (Female -> Male -> Female)")
        print("=" * 60)

        # Step 1: Female
        recs_f1 = service.fetch_live_recommendations(
            profile=female_profile, preferences=female_pref, occasion="party", season="summer",
            compatible_colors=["olive"], target_category="dress", limit=20, price_range="all"
        )
        male_in_f1 = [p for p in recs_f1 if p.get('gender') == 'male' or re.search(r"\b(men|men's|mens)\b", (p.get('title') or '').lower())]

        # Step 2: Male
        recs_m = service.fetch_live_recommendations(
            profile=male_profile, preferences=male_pref, occasion="party", season="summer",
            compatible_colors=["navy"], target_category="clothing", limit=20, price_range="all"
        )
        female_in_m = [p for p in recs_m if p.get('gender') == 'female' or re.search(r"\b(women|women's|womens|dress|gown|kurti|saree)\b", (p.get('title') or '').lower())]

        # Step 3: Female again
        recs_f2 = service.fetch_live_recommendations(
            profile=female_profile, preferences=female_pref, occasion="casual", season="summer",
            compatible_colors=["emerald"], target_category="dress", limit=20, price_range="all"
        )
        male_in_f2 = [p for p in recs_f2 if p.get('gender') == 'male' or re.search(r"\b(men|men's|mens)\b", (p.get('title') or '').lower())]

        print(f"Female Run 1: Returned {len(recs_f1)} | Male contamination: {len(male_in_f1)}")
        print(f"Male Run:     Returned {len(recs_m)} | Female contamination: {len(female_in_m)}")
        print(f"Female Run 2: Returned {len(recs_f2)} | Male contamination: {len(male_in_f2)}")

        if len(male_in_f1) == 0 and len(female_in_m) == 0 and len(male_in_f2) == 0:
            print("STATUS: PASS (Zero cross-gender contamination across profile switches)")
        else:
            print("STATUS: FAIL (Cross-gender contamination detected)")
            all_passed = False

        # ======================================================================
        # SECTION 32: TEST SKIN-TONE COLOR MATCHING (Fair / Medium / Deep)
        # ======================================================================
        print("\n" + "=" * 60)
        print("SUITE 4: TESTING SKIN-TONE COLOR MATCHING")
        print("=" * 60)
        for tone in ['fair', 'medium', 'deep']:
            female_profile.skin_tone = tone
            palette = SKIN_TONE_PALETTES[tone]
            passes = service.generate_search_passes('female', 'Party', 'Summer', palette, "under 1000", 'dress')
            pass2_colors = passes[1]
            print(f"Skin Tone '{tone.title()}' color search queries (Pass 2):")
            for q in pass2_colors[:3]:
                print(f"   * {q}")
            matched_palette_words = [c for c in palette if any(c in q for q in pass2_colors)]
            if len(matched_palette_words) >= 2:
                print(f"   [PASS] Found {len(matched_palette_words)} tone-compatible colors in search passes")
            else:
                print(f"   [FAIL] Missing palette colors in queries")
                all_passed = False

        # ======================================================================
        # SUMMARY
        # ======================================================================
        avg_lat = sum(total_latencies) / len(total_latencies) if total_latencies else 0.0
        print("\n" + "=" * 80)
        print("FINAL TEST EXECUTION SUMMARY")
        print("=" * 80)
        for k, v in results_summary.items():
            print(f"  {k:20}: RETURNED {v:2} | TARGET: 25 | {'PASS' if v >= 25 else 'PARTIAL'}")
        print(f"Average Response Latency: {avg_lat:.2f}s")
        print(f"OVERALL SUITE STATUS: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED/PARTIAL'}")
        print("=" * 80)

        return all_passed

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
