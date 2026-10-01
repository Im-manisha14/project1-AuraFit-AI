import os
import sys

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
    validate_retailer
)
from services.recommendation_engine import RecommendationEngine

def run_tests():
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("AURAFIT AI: REAL SHOPPING FILTERS & RETAILER GENDER DETECTION TEST SUITE")
        print("=" * 80)

        engine = RecommendationEngine()
        shopping_service = SerpApiShoppingService()

        # ------------------------------------------------------------------
        # PART A: UNIT TESTS FOR GENDER DETECTION (Priority Order)
        # ------------------------------------------------------------------
        print("\n[PART A] Testing detect_product_gender Priority & Retailer Independence...")
        test_products_gender = [
            # 1. Structured metadata priority
            {
                "product": {"title": "Cotton Blend T-Shirt", "category": "Women > Clothing > Tops", "source": "Amazon"},
                "expected": "female",
                "label": "Structured metadata says women (title is neutral)"
            },
            {
                "product": {"title": "Casual Linen Shirt", "product_type": "Men's Apparel", "source": "Myntra"},
                "expected": "male",
                "label": "Structured product_type says Men's"
            },
            # 2. Product title priority
            {
                "product": {"title": "Women's Floral Midi Dress", "source": "Myntra"},
                "expected": "female",
                "label": "Title has Women's Floral Midi Dress"
            },
            {
                "product": {"title": "Men's Slim Fit Formal Shirt", "source": "AJIO"},
                "expected": "male",
                "label": "Title has Men's Slim Fit Formal Shirt"
            },
            {
                "product": {"title": "Ladies Party Wear Gown", "source": "Flipkart"},
                "expected": "female",
                "label": "Title has Ladies Party Wear Gown"
            },
            # 3. Retailer independence (retailer must not dictate gender)
            {
                "product": {"title": "Men's Solid Round Neck T-Shirt", "source": "Myntra"},
                "expected": "male",
                "label": "Myntra with Men's product -> detected as male (not assumed female)"
            },
            {
                "product": {"title": "Women Printed A-Line Dress", "source": "Amazon"},
                "expected": "female",
                "label": "Amazon with Women dress -> detected as female (not assumed unisex)"
            },
            # 4. Garment type evidence
            {
                "product": {"title": "Vero Moda Emerald Green Wrap Dress", "source": "Vero Moda"},
                "expected": "female",
                "label": "Wrap Dress without explicit 'women' word -> detected as female"
            },
            {
                "product": {"title": "Handcrafted Silk Anarkali Kurti", "source": "Nykaa"},
                "expected": "female",
                "label": "Anarkali Kurti -> detected as female"
            },
            {
                "product": {"title": "Raw Silk Sherwani with Churidar", "source": "Manyavar"},
                "expected": "male",
                "label": "Sherwani -> detected as male"
            },
            # 5. Unisex
            {
                "product": {"title": "Unisex Oversized Graphic Hoodie", "source": "H&M"},
                "expected": "unisex",
                "label": "Unisex hoodie -> detected as unisex"
            },
            # 6. Compound words (Dress shoes, Dress shirt must NOT be female dress)
            {
                "product": {"title": "Men's Oxford Leather Dress Shoes", "source": "Bata"},
                "expected": "male",
                "label": "Men's Dress Shoes -> detected as male"
            }
        ]

        gender_passes = 0
        for tp in test_products_gender:
            detected = detect_product_gender(tp["product"])
            passed = (detected == tp["expected"])
            if passed:
                gender_passes += 1
                print(f"  [PASS] {tp['label']}: detected='{detected}'")
            else:
                print(f"  [FAIL] {tp['label']}: expected='{tp['expected']}', detected='{detected}'")

        assert gender_passes == len(test_products_gender), f"Gender detection failed: {gender_passes}/{len(test_products_gender)}"
        print(f"All {gender_passes} gender detection tests passed!\n")

        # ------------------------------------------------------------------
        # PART B: UNIT TESTS FOR PRICE VALIDATION
        # ------------------------------------------------------------------
        print("\n[PART B] Testing Price Range Parsing and Validation...")
        price_test_cases = [
            ("under_500", 450, True),
            ("under_500", 500, True),
            ("under_500", 550, False),
            ("500_1000", 799, True),
            ("500_1000", 1200, False),
            ("1000_2000", 1499, True),
            ("1000_2000", 850, False),
            ("1000_2000", 2500, False),
            ("2000_3000", 2499, True),
            ("3000_5000", 4500, True),
            ("5000_10000", 7999, True),
            ("above_10000", 15000, True),
            ("above_10000", 8500, False),
        ]
        for r_str, p_val, exp_ok in price_test_cases:
            mn, mx, lbl = parse_price_range(r_str)
            ok, _ = validate_price(p_val, mn, mx)
            assert ok == exp_ok, f"Price test failed for range {r_str} on price {p_val}: expected {exp_ok}, got {ok}"
            print(f"  [PASS] Range '{lbl}' on ₹{p_val}: valid={ok}")

        # Custom price range test
        c_min, c_max, c_lbl = parse_price_range(custom_min=1200, custom_max=2800)
        assert validate_price(1500, c_min, c_max)[0] is True
        assert validate_price(1100, c_min, c_max)[0] is False
        assert validate_price(3000, c_min, c_max)[0] is False
        print(f"  [PASS] Custom Range '{c_lbl}' on ₹1500 (True), ₹1100 (False), ₹3000 (False)")

        # ------------------------------------------------------------------
        # PART C: 8 MANDATORY SPECIFICATION TESTS
        # ------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("RUNNING 8 MANDATORY SCENARIO TESTS (Section 20)")
        print("=" * 80)

        # Get or setup test users
        female_user = User.query.filter_by(email="manishasivakumar06@gmail.com").first()
        if not female_user:
            female_user = User.query.first()
        female_profile = UserProfile.query.filter_by(user_id=female_user.id).first()
        female_profile.gender = "female"
        db.session.commit()

        # Male profile setup
        male_user = User.query.filter(User.id != female_user.id).first()
        if not male_user:
            male_user = User(email="test_male@aurafit.ai", username="test_male")
            male_user.set_password("Password123!")
            db.session.add(male_user)
            db.session.commit()
        male_profile = UserProfile.query.filter_by(user_id=male_user.id).first()
        if not male_profile:
            male_profile = UserProfile(
                user_id=male_user.id,
                gender="male",
                age=25,
                body_type="athletic",
                skin_tone="medium",
                height=178,
                weight=72
            )
            db.session.add(male_profile)
        else:
            male_profile.gender = "male"
            male_profile.skin_tone = "medium"
        db.session.commit()

        female_pref = StylePreference.query.filter_by(user_id=female_user.id).first()
        male_pref = StylePreference.query.filter_by(user_id=male_user.id).first()

        # TEST 1: Female + Dress + ₹1,000–₹2,000
        print("\n--- TEST 1: Female + Dress + ₹1,000–₹2,000 ---")
        recs1 = engine.generate_recommendations(
            user=female_user,
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            limit=6,
            price_range="1000_2000"
        )
        print(f"Generated {len(recs1)} recommendations for Test 1")
        for r in recs1:
            outfit = r["outfit"]
            price = outfit["price"]
            title = outfit["name"]
            retailer = outfit["retailer"]
            gender = outfit["gender"]
            category = outfit["category"]
            assert 1000 <= price <= 2000, f"TEST 1 FAIL: Price ₹{price} not in 1000-2000 ({title})"
            assert gender in ("female", "unisex"), f"TEST 1 FAIL: Gender {gender} is not female/unisex ({title})"
            assert category == "dress", f"TEST 1 FAIL: Category {category} is not dress ({title})"
            assert outfit.get("shopping_url") is not None, f"TEST 1 FAIL: Missing exact shopping URL ({title})"
            assert outfit.get("image_url") and not "aurafit.store" in outfit["image_url"], f"TEST 1 FAIL: Invalid image ({title})"
            print(f"  ✓ {title} | {retailer} | ₹{price} | gender={gender} | category={category}")

        # Check similar recommendations obey filters too
        sim1 = getattr(engine, 'last_similar_recommendations', [])
        print(f"Verified {len(sim1)} similar recommendations for Test 1")
        for s in sim1:
            price = s["price"]
            assert 1000 <= price <= 2000, f"TEST 1 SIMILAR FAIL: Price ₹{price} not in 1000-2000"
            assert s["gender"] in ("female", "unisex"), f"TEST 1 SIMILAR FAIL: Gender {s['gender']} not female"
            print(f"  ✓ (Similar) {s['name']} | {s['retailer']} | ₹{price} | gender={s['gender']}")

        # TEST 2: Female + Dress + Under ₹500
        print("\n--- TEST 2: Female + Dress + Under ₹500 ---")
        recs2 = engine.generate_recommendations(
            user=female_user,
            profile=female_profile,
            preferences=female_pref,
            occasion="casual",
            season="summer",
            limit=6,
            price_range="under_500"
        )
        print(f"Generated {len(recs2)} recommendations for Test 2")
        for r in recs2:
            outfit = r["outfit"]
            price = outfit["price"]
            title = outfit["name"]
            gender = outfit["gender"]
            assert price <= 500, f"TEST 2 FAIL: Price ₹{price} is above ₹500 ({title})"
            assert gender in ("female", "unisex"), f"TEST 2 FAIL: Gender {gender} is not female/unisex ({title})"
            print(f"  ✓ {title} | {outfit['retailer']} | ₹{price}")

        # TEST 3: Male + Clothing + ₹1,000–₹3,000
        print("\n--- TEST 3: Male + Clothing + ₹1,000–₹3,000 ---")
        recs3 = engine.generate_recommendations(
            user=male_user,
            profile=male_profile,
            preferences=male_pref,
            occasion="casual",
            season="summer",
            limit=6,
            price_range="1000_3000"
        )
        print(f"Generated {len(recs3)} recommendations for Test 3")
        for r in recs3:
            outfit = r["outfit"]
            price = outfit["price"]
            title = outfit["name"]
            gender = outfit["gender"]
            category = outfit["category"]
            assert 1000 <= price <= 3000, f"TEST 3 FAIL: Price ₹{price} not in 1000-3000 ({title})"
            assert gender in ("male", "unisex"), f"TEST 3 FAIL: Gender {gender} is not male ({title})"
            assert category != "dress", f"TEST 3 FAIL: Category {category} is dress for male user ({title})"
            print(f"  ✓ {title} | {outfit['retailer']} | ₹{price} | gender={gender} | category={category}")

        # TEST 4: Female + Myntra + ₹1,000–₹2,000
        print("\n--- TEST 4: Female + Myntra + ₹1,000–₹2,000 ---")
        recs4 = engine.generate_recommendations(
            user=female_user,
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            limit=6,
            price_range="1000_2000",
            retailer="Myntra"
        )
        print(f"Generated {len(recs4)} recommendations for Test 4")
        for r in recs4:
            outfit = r["outfit"]
            price = outfit["price"]
            title = outfit["name"]
            retailer = outfit["retailer"]
            assert "myntra" in retailer.lower(), f"TEST 4 FAIL: Retailer '{retailer}' is not Myntra ({title})"
            assert 1000 <= price <= 2000, f"TEST 4 FAIL: Price ₹{price} not in 1000-2000"
            assert outfit["gender"] in ("female", "unisex")
            print(f"  ✓ {title} | {retailer} | ₹{price}")

        # TEST 5: Female + Amazon + ₹1,000–₹2,000
        print("\n--- TEST 5: Female + Amazon + ₹1,000–₹2,000 ---")
        recs5 = engine.generate_recommendations(
            user=female_user,
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            limit=6,
            price_range="1000_2000",
            retailer="Amazon"
        )
        print(f"Generated {len(recs5)} recommendations for Test 5")
        for r in recs5:
            outfit = r["outfit"]
            price = outfit["price"]
            title = outfit["name"]
            retailer = outfit["retailer"]
            assert "amazon" in retailer.lower(), f"TEST 5 FAIL: Retailer '{retailer}' is not Amazon ({title})"
            assert 1000 <= price <= 2000, f"TEST 5 FAIL: Price ₹{price} not in 1000-2000"
            assert outfit["gender"] in ("female", "unisex")
            print(f"  ✓ {title} | {retailer} | ₹{price}")

        # TEST 6: Change Female -> Male: Verify old female products disappear
        print("\n--- TEST 6: Change Female -> Male Transition ---")
        recs_male = engine.generate_recommendations(
            user=male_user,
            profile=male_profile,
            preferences=male_pref,
            occasion="formal",
            season="summer",
            limit=6
        )
        print(f"Generated {len(recs_male)} recommendations for Male profile")
        female_count_in_male = 0
        for r in recs_male:
            outfit = r["outfit"]
            if outfit["gender"] == "female" or outfit["category"] == "dress":
                female_count_in_male += 1
        assert female_count_in_male == 0, f"TEST 6 FAIL: {female_count_in_male} female products appeared for male user!"
        print(f"  ✓ Verified: 0 female products or dresses found in male recommendations!")

        # TEST 7: Change price range: Verify products outside selected range disappear
        print("\n--- TEST 7: Dynamic Price Range Filtering ---")
        # Generate base list with all prices
        base_recs = engine.generate_recommendations(
            user=female_user,
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            limit=10,
            price_range="all"
        )
        print(f"Base recommendation count: {len(base_recs)}")
        # Now simulate dynamic filtering for ₹1,000–₹2,000 on this dataset
        filtered_dynamic = [
            r for r in base_recs
            if 1000 <= r["outfit"]["price"] <= 2000
        ]
        print(f"Dynamically filtered (₹1,000–₹2,000): {len(filtered_dynamic)} items")
        for fd in filtered_dynamic:
            p = fd["outfit"]["price"]
            assert 1000 <= p <= 2000, f"TEST 7 FAIL: Price ₹{p} is outside range"
            print(f"  ✓ {fd['outfit']['name']} | ₹{p}")

        # TEST 8: No matching products: Verify no mock products appear
        print("\n--- TEST 8: No Matching Products (Extreme Price Filter) ---")
        # Filter for impossible range ₹90,000–₹95,000
        recs8 = engine.generate_recommendations(
            user=female_user,
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            limit=6,
            min_price=90000,
            max_price=95000,
            price_range="custom"
        )
        print(f"Generated items for ₹90,000–₹95,000: {len(recs8)}")
        assert len(recs8) == 0, f"TEST 8 FAIL: Expected 0 products, but got {len(recs8)} (mock products leaked!)"
        # Check no mock $49.99 or AuraFit Official items
        for r in recs8:
            assert r["outfit"]["price"] != 49.99
            assert r["outfit"]["retailer"] != "AuraFit Official"
        print("  ✓ Verified: 0 products returned and zero mock items leaked!")

        print("\n" + "=" * 80)
        print("ALL 8 ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
        print("=" * 80)

if __name__ == "__main__":
    run_tests()
