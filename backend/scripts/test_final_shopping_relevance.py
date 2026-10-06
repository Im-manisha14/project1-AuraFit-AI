import os
import sys
import re
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
from flask_jwt_extended import create_access_token

def run_tests():
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("AURAFIT AI — FINAL SHOPPING RELEVANCE, GENDER, CATEGORY & DEDUP SUITE")
        print("=" * 80)

        service = SerpApiShoppingService()

        # Setup test users
        female_user = User.query.filter_by(email="test_relevance_female@aurafit.com").first()
        if not female_user:
            female_user = User(username="test_rel_female", email="test_relevance_female@aurafit.com")
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
        else:
            female_profile.gender = "female"
            female_profile.skin_tone = "medium"
            db.session.commit()

        female_pref = StylePreference.query.filter_by(user_id=female_user.id).first()
        if not female_pref:
            female_pref = StylePreference(
                user_id=female_user.id,
                preferred_styles=["party", "casual"],
                preferred_colors=["olive", "emerald", "burgundy"]
            )
            db.session.add(female_pref)
            db.session.commit()

        male_user = User.query.filter_by(email="test_relevance_male@aurafit.com").first()
        if not male_user:
            male_user = User(username="test_rel_male", email="test_relevance_male@aurafit.com")
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
        else:
            male_profile.gender = "male"
            db.session.commit()

        male_pref = StylePreference.query.filter_by(user_id=male_user.id).first()
        if not male_pref:
            male_pref = StylePreference(
                user_id=male_user.id,
                preferred_styles=["casual", "party"],
                preferred_colors=["navy", "burgundy"]
            )
            db.session.add(male_pref)
            db.session.commit()

        all_tests_passed = True

        # ======================================================================
        # TEST 1: Female + Party + Summer + Dress
        # ======================================================================
        print("\n" + "=" * 60)
        print("TEST 1: Female + Party + Summer + Dress (Strict Dress Only)")
        print("=" * 60)
        recs_t1 = service.fetch_live_recommendations(
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            compatible_colors=["olive", "emerald", "burgundy"],
            target_category="dress",
            limit=25,
            price_range="all"
        )
        print(f"Returned: {len(recs_t1)} products")
        
        t1_invalids = {
            'mens': 0, 'shoes': 0, 'bags': 0, 'jewellery': 0,
            'accessories': 0, 'tops': 0, 'pants': 0, 'skirts': 0,
            'duplicate_products': 0
        }
        seen_t1_cids = set()
        seen_t1_urls = set()
        for p in recs_t1:
            title = p.get('title', '')
            cat = p.get('category', '')
            cid = p.get('canonical_product_id') or p.get('external_id')
            url = p.get('canonical_url') or p.get('product_url')
            
            if cid in seen_t1_cids or url in seen_t1_urls:
                t1_invalids['duplicate_products'] += 1
            if cid: seen_t1_cids.add(cid)
            if url: seen_t1_urls.add(url)
            
            is_compat, _, _ = ProductValidator.is_gender_compatible(p, 'female')
            if not is_compat or p.get('gender') == 'male':
                t1_invalids['mens'] += 1
                
            is_dress, det_cat, _ = ProductValidator.is_actual_dress(p)
            if not is_dress:
                if 'shoe' in det_cat or 'footwear' in det_cat:
                    t1_invalids['shoes'] += 1
                elif 'bag' in det_cat:
                    t1_invalids['bags'] += 1
                elif 'jewel' in det_cat:
                    t1_invalids['jewellery'] += 1
                elif 'accessor' in det_cat:
                    t1_invalids['accessories'] += 1
                elif 'top' in det_cat or 'shirt' in det_cat:
                    t1_invalids['tops'] += 1
                elif 'pant' in det_cat or 'trouser' in det_cat:
                    t1_invalids['pants'] += 1
                elif 'skirt' in det_cat:
                    t1_invalids['skirts'] += 1

        print("Expected invalid counts: 0 across all non-dress categories")
        print(f"Actual invalid counts: {t1_invalids}")
        t1_failed = any(v > 0 for v in t1_invalids.values())
        if t1_failed:
            print("TEST 1 STATUS: FAIL")
            all_tests_passed = False
        else:
            print("TEST 1 STATUS: PASS (0 invalid items, 100% genuine women's dresses)")

        # ======================================================================
        # TEST 2: Male + Party + Summer + Clothing
        # ======================================================================
        print("\n" + "=" * 60)
        print("TEST 2: Male + Party + Summer + Clothing")
        print("=" * 60)
        recs_t2 = service.fetch_live_recommendations(
            profile=male_profile,
            preferences=male_pref,
            occasion="party",
            season="summer",
            compatible_colors=["navy", "burgundy"],
            target_category="clothing",
            limit=25,
            price_range="all"
        )
        print(f"Returned: {len(recs_t2)} products")
        female_dresses_in_male = [
            p for p in recs_t2
            if p.get('gender') == 'female'
            or p.get('category') == 'dress'
            or re.search(r"\b(women|women's|womens|dress|gown|kurti|saree)\b", p.get('title', '').lower())
        ]
        print(f"Female dresses in male results: {len(female_dresses_in_male)}")
        if female_dresses_in_male:
            print("TEST 2 STATUS: FAIL")
            all_tests_passed = False
        else:
            print("TEST 2 STATUS: PASS (0 women's dresses in male recommendations)")

        # ======================================================================
        # TEST 3 & 4: Gender Profile Switching
        # ======================================================================
        print("\n" + "=" * 60)
        print("TEST 3 & 4: Female <-> Male Profile Switching Isolation")
        print("=" * 60)
        recs_f_switch = service.fetch_live_recommendations(
            profile=female_profile, preferences=female_pref, occasion="party", season="summer",
            compatible_colors=["olive"], target_category="dress", limit=20, price_range="all"
        )
        recs_m_switch = service.fetch_live_recommendations(
            profile=male_profile, preferences=male_pref, occasion="party", season="summer",
            compatible_colors=["navy"], target_category="clothing", limit=20, price_range="all"
        )
        recs_f2_switch = service.fetch_live_recommendations(
            profile=female_profile, preferences=female_pref, occasion="casual", season="summer",
            compatible_colors=["emerald"], target_category="dress", limit=20, price_range="all"
        )

        male_in_f1 = [p for p in recs_f_switch if p.get('gender') == 'male']
        female_in_m = [p for p in recs_m_switch if p.get('gender') == 'female' or p.get('category') == 'dress']
        male_in_f2 = [p for p in recs_f2_switch if p.get('gender') == 'male']

        print(f"Switch 1 (Female): {len(recs_f_switch)} items | Male contaminated: {len(male_in_f1)}")
        print(f"Switch 2 (Male):   {len(recs_m_switch)} items | Female contaminated: {len(female_in_m)}")
        print(f"Switch 3 (Female): {len(recs_f2_switch)} items | Male contaminated: {len(male_in_f2)}")
        if male_in_f1 or female_in_m or male_in_f2:
            print("TEST 3 & 4 STATUS: FAIL")
            all_tests_passed = False
        else:
            print("TEST 3 & 4 STATUS: PASS (Zero cross-gender contamination)")

        # ======================================================================
        # TEST 5-9: All 5 Price Ranges
        # ======================================================================
        print("\n" + "=" * 60)
        print("TEST 5-9: All 5 Price Ranges")
        print("=" * 60)
        price_ranges = [
            ("TEST 5: Under ₹500", "under_500", None, 500.0),
            ("TEST 6: ₹500–₹1,000", "500_1000", 500.0, 1000.0),
            ("TEST 7: ₹1,000–₹2,500", "1000_2500", 1000.0, 2500.0),
            ("TEST 8: ₹2,500–₹5,000", "2500_5000", 2500.0, 5000.0),
            ("TEST 9: ₹5,000+", "5000_plus", 5000.0, None),
        ]
        for t_name, p_code, min_p, max_p in price_ranges:
            p_recs = service.fetch_live_recommendations(
                profile=female_profile,
                preferences=female_pref,
                occasion="party",
                season="summer",
                compatible_colors=["olive"],
                target_category="dress",
                limit=25,
                price_range=p_code
            )
            violations = []
            for p in p_recs:
                price = float(p.get('price', 0))
                if min_p is not None and price < min_p:
                    violations.append((p.get('title'), price, f"below {min_p}"))
                if max_p is not None and price > max_p:
                    violations.append((p.get('title'), price, f"above {max_p}"))
            
            print(f"{t_name:25} | Returned: {len(p_recs):2} | Violations: {len(violations)}")
            if violations:
                print(f"   Sample violation: {violations[0]}")
                print(f"   {t_name} STATUS: FAIL")
                all_tests_passed = False
            else:
                print(f"   {t_name} STATUS: PASS (100% price compliant)")

        # ======================================================================
        # TEST 10: Duplicate Product Variants
        # ======================================================================
        print("\n" + "=" * 60)
        print("TEST 10: Duplicate Product Variants")
        print("=" * 60)
        u1 = "https://www.myntra.com/dresses/dress1?utm_source=google&srsltid=123"
        u2 = "https://www.myntra.com/dresses/dress1?size=M&ref=xyz"
        can1 = ProductValidator.canonicalize_url(u1)
        can2 = ProductValidator.canonicalize_url(u2)
        norm_t1 = ProductValidator.normalize_title("Vero Moda Women's Olive Green Ruched Dress - Size M")
        norm_t2 = ProductValidator.normalize_title("Vero Moda Olive Green Ruched Dress Size L")
        print(f"Canonical URL 1: {can1}")
        print(f"Canonical URL 2: {can2}")
        print(f"Normalized Title 1: {norm_t1}")
        print(f"Normalized Title 2: {norm_t2}")
        if can1 == can2 and norm_t1 == norm_t2:
            print("TEST 10 STATUS: PASS (Identifies duplicate product variants and normalizes canonical direct URLs)")
        else:
            print("TEST 10 STATUS: FAIL")
            all_tests_passed = False

        # ======================================================================
        # TEST 11: False Dress Keywords Rejection
        # ======================================================================
        print("\n" + "=" * 60)
        print("TEST 11: False Dress Keywords Rejection")
        print("=" * 60)
        false_dresses = [
            "Women's Dress Shoes in Patent Leather",
            "Men's Formal Dress Shirt",
            "Slim Fit Formal Dress Pants",
            "Women's Block Heel Dress Sandals",
            "Cotton Floral Dress Material 2.5m Fabric"
        ]
        all_false_rejected = True
        for fd in false_dresses:
            is_dress, cat, reason = ProductValidator.is_actual_dress({'title': fd})
            print(f"   '{fd}': is_dress={is_dress} (Detected: {cat}, Reason: {reason})")
            if is_dress:
                all_false_rejected = False
        if all_false_rejected:
            print("TEST 11 STATUS: PASS (100% false dress keywords successfully rejected)")
        else:
            print("TEST 11 STATUS: FAIL")
            all_tests_passed = False

        # ======================================================================
        # TEST 12: Collections Gender / Category / Deduplication Validation
        # ======================================================================
        print("\n" + "=" * 60)
        print("TEST 12: Collections Gender & Category Validation")
        print("=" * 60)
        client = app.test_client()
        token = create_access_token(identity=str(female_user.id))
        headers = {'Authorization': f'Bearer {token}'}
        col_resp = client.get('/api/recommendations/collections?season=summer&limit=8', headers=headers)
        col_data = col_resp.get_json() or {}
        col_passed = True
        for col_name, outfits in col_data.items():
            if not isinstance(outfits, list):
                continue
            dup_imgs = len(outfits) - len(set(o.get('image_url') for o in outfits if o.get('image_url')))
            dup_urls = len(outfits) - len(set(o.get('shopping_url') for o in outfits if o.get('shopping_url')))
            non_dresses = [o.get('name') for o in outfits if o.get('category') != 'dress']
            mens = [o.get('name') for o in outfits if o.get('gender') == 'male']
            if dup_imgs > 0 or dup_urls > 0 or non_dresses or mens:
                col_passed = False
                print(f"   Collection '{col_name}': FAIL (dup_imgs={dup_imgs}, dup_urls={dup_urls}, non_dresses={len(non_dresses)}, mens={len(mens)})")
            else:
                print(f"   Collection '{col_name:12}': PASS ({len(outfits)} items, 0 dupes, 100% female dresses)")
        if col_passed:
            print("TEST 12 STATUS: PASS (All collections pass strict gender/dress/dedup pipeline)")
        else:
            print("TEST 12 STATUS: FAIL")
            all_tests_passed = False

        # ======================================================================
        # TEST 13 & 14: Image & URL Identity Consistency
        # ======================================================================
        print("\n" + "=" * 60)
        print("TEST 13 & 14: Image & URL Identity Consistency")
        print("=" * 60)
        sample = recs_t1[0] if recs_t1 else {}
        card_img = sample.get('image_url')
        card_url = sample.get('product_url')
        canon_url = sample.get('canonical_url')
        db_rec = Outfit.query.filter_by(id=sample.get('id')).first() if sample.get('id') else None
        
        print(f"Card Image URL:   {card_img}")
        print(f"DB Image URL:     {db_rec.image_url if db_rec else 'N/A'}")
        print(f"Card Product URL: {card_url}")
        print(f"DB Product URL:   {db_rec.product_url if db_rec else 'N/A'}")
        
        identity_pass = (
            db_rec is not None
            and card_img == db_rec.image_url
            and (card_url == db_rec.product_url or canon_url == db_rec.product_url)
        )
        if identity_pass:
            print("TEST 13 STATUS: PASS (Card Image == DB Image == Details Page Image)")
            print("TEST 14 STATUS: PASS (Card URL == DB URL == Shop Now URL)")
        else:
            print("TEST 13/14 STATUS: FAIL (Identity mismatch between card and database)")
            all_tests_passed = False

        # ======================================================================
        # FINAL STRUCTURED REPORT
        # ======================================================================
        print("\n" + "=" * 80)
        print("FINAL VERIFICATION SUMMARY (SECTION 46 SPECIFICATION)")
        print("=" * 80)
        print(f"OVERALL STATUS: {'ALL 14 TESTS PASSED' if all_tests_passed else 'SOME TESTS FAILED'}")
        print("=" * 80)

        # Print 5 verified sample products
        print("\nSAMPLE VERIFIED PRODUCTS:")
        for idx, p in enumerate(recs_t1[:5], 1):
            print(f"\nProduct #{idx}:")
            print(f"  Title:                {p.get('title')}")
            print(f"  Gender:               {p.get('gender')}")
            print(f"  Category:             {p.get('category')}")
            print(f"  Retailer:             {p.get('retailer') or p.get('store')}")
            print(f"  Price:                ₹{p.get('price')}")
            print(f"  Canonical Product ID: {p.get('canonical_product_id') or p.get('external_id')}")
            print(f"  Image URL:            {p.get('image_url')}")
            print(f"  Direct Product URL:   {p.get('canonical_url') or p.get('product_url')}")

        return all_tests_passed

if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)
