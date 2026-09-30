import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from extensions import db
from models.user import User, UserProfile, StylePreference
from models.outfit import Outfit
from services.shopping_service import SerpApiShoppingService, ProductValidator
from services.recommendation_engine import RecommendationEngine

def run_tests():
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("AURAFIT AI: RECOMMENDATION RELEVANCE & INTEGRITY VERIFICATION SUITE")
        print("=" * 80)

        # ----------------------------------------------------------------------
        # UNIT VALIDATION ON SAMPLE / EDGE-CASE DATA
        # ----------------------------------------------------------------------
        sample_dataset = [
            # Valid Women's Dresses
            {"title": "Women Navy Blue Floral Midi Dress", "thumbnail": "https://img.shop.com/dress1.jpg", "target": "female", "expected_gender": True, "expected_cat": True},
            {"title": "Burgundy Velvet Bodycon Party Dress", "thumbnail": "https://img.shop.com/dress2.jpg", "target": "female", "expected_gender": True, "expected_cat": True},
            {"title": "Zara Women Olive Green Wrap Maxi Dress", "thumbnail": "https://img.shop.com/dress3.jpg", "target": "female", "expected_gender": True, "expected_cat": True},
            {"title": "H&M Women Cotton Shirt Dress with Belt", "thumbnail": "https://img.shop.com/dress4.jpg", "target": "female", "expected_gender": True, "expected_cat": True},
            {"title": "Vero Moda Women A-Line Cocktail Dress", "thumbnail": "https://img.shop.com/dress5.jpg", "target": "female", "expected_gender": True, "expected_cat": True},
            
            # Non-Dress / Accessories / Shoes (Should be rejected for dress requests)
            {"title": "Nike Women Air Max Running Shoes", "thumbnail": "https://img.shop.com/shoes1.jpg", "target": "female", "expected_gender": True, "expected_cat": False},
            {"title": "Michael Kors Leather Handbag for Women", "thumbnail": "https://img.shop.com/bag1.jpg", "target": "female", "expected_gender": True, "expected_cat": False},
            {"title": "Titan Raga Analog Watch for Women", "thumbnail": "https://img.shop.com/watch1.jpg", "target": "female", "expected_gender": True, "expected_cat": False},
            {"title": "Gold Plated Dangler Earrings", "thumbnail": "https://img.shop.com/earring1.jpg", "target": "female", "expected_gender": True, "expected_cat": False},
            {"title": "Levis Women High-Rise Flared Jeans", "thumbnail": "https://img.shop.com/jeans1.jpg", "target": "female", "expected_gender": True, "expected_cat": False},
            {"title": "Women Cotton Graphic T-Shirt", "thumbnail": "https://img.shop.com/tee1.jpg", "target": "female", "expected_gender": True, "expected_cat": False},
            {"title": "Pleated Midi Skirt for Women", "thumbnail": "https://img.shop.com/skirt1.jpg", "target": "female", "expected_gender": True, "expected_cat": False},
            {"title": "Oxford Leather Dress Shoes", "thumbnail": "https://img.shop.com/dress_shoes.jpg", "target": "female", "expected_gender": False, "expected_cat": False},
            {"title": "Men Formal Cotton Dress Shirt", "thumbnail": "https://img.shop.com/dress_shirt.jpg", "target": "female", "expected_gender": False, "expected_cat": False},
            {"title": "Unstitched Cotton Dress Material", "thumbnail": "https://img.shop.com/dress_mat.jpg", "target": "female", "expected_gender": True, "expected_cat": False},

            # Men's Items (Should be rejected for female, accepted for male)
            {"title": "Men's Navy Blue Slim Fit Casual Shirt", "thumbnail": "https://img.shop.com/mshirt1.jpg", "target": "male", "expected_gender": True, "expected_cat": True},
            {"title": "Allen Solly Men Solid Cotton Polo T-Shirt", "thumbnail": "https://img.shop.com/mshirt2.jpg", "target": "male", "expected_gender": True, "expected_cat": True},
            {"title": "Raymond Men Formal Two-Piece Suit", "thumbnail": "https://img.shop.com/msuit1.jpg", "target": "male", "expected_gender": True, "expected_cat": True},
            {"title": "Men Chino Trousers Slim Fit", "thumbnail": "https://img.shop.com/mpants1.jpg", "target": "male", "expected_gender": True, "expected_cat": True},
            {"title": "Men Linen Casual Blazer", "thumbnail": "https://img.shop.com/mblazer1.jpg", "target": "male", "expected_gender": True, "expected_cat": True},
            {"title": "Women Party Wear Gown", "thumbnail": "https://img.shop.com/gown1.jpg", "target": "male", "expected_gender": False, "expected_cat": False},

            # Invalid Image / Placeholder Cases
            {"title": "Women Floral Dress", "thumbnail": "https://aurafit.store/mock.png", "target": "female", "expected_gender": True, "expected_cat": True, "expected_img": False},
            {"title": "Women Summer Dress", "thumbnail": "https://images.unsplash.com/photo-1234", "target": "female", "expected_gender": True, "expected_cat": True, "expected_img": False},
            {"title": "Women Cocktail Dress", "thumbnail": "invalid_url_string", "target": "female", "expected_gender": True, "expected_cat": True, "expected_img": False},
        ]

        total_scanned = len(sample_dataset)
        rejected_by_gender = 0
        rejected_by_category = 0
        rejected_by_image = 0
        valid_women_dresses = 0
        valid_men_products = 0

        for item in sample_dataset:
            target_g = item["target"]
            # 1. Image Check
            img_ok, _ = ProductValidator.validate_image(item["thumbnail"])
            if not img_ok:
                rejected_by_image += 1
                continue

            # 2. Gender Check
            g_ok, _ = ProductValidator.validate_gender(item["title"], target_gender=target_g)
            if not g_ok:
                rejected_by_gender += 1
                continue

            # 3. Category Check
            c_ok, _ = ProductValidator.validate_category(
                item["title"],
                target_category="dress" if target_g == "female" else "clothing",
                target_gender=target_g
            )
            if not c_ok:
                rejected_by_category += 1
                continue

            if target_g == "female":
                valid_women_dresses += 1
            else:
                valid_men_products += 1

        print("\n--- SAMPLE DATASET VALIDATION METRICS ---")
        print(f"Total Products Evaluated:        {total_scanned}")
        print(f"Rejected by Gender:              {rejected_by_gender}")
        print(f"Rejected by Category:            {rejected_by_category}")
        print(f"Rejected by Image/Identity:      {rejected_by_image}")
        print(f"Valid Women's Dresses Approved:  {valid_women_dresses}")
        print(f"Valid Men's Products Approved:   {valid_men_products}")

        # ----------------------------------------------------------------------
        # TEST A — LIVE WOMEN RECOMMENDATIONS
        # ----------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST A: WOMEN RECOMMENDATION PIPELINE")
        print("Profile: Female | Occasion: Party | Season: Summer | Category: Dress")
        print("=" * 80)

        engine = RecommendationEngine()
        female_user = User(email="test_female@aurafit.ai", username="test_female")
        female_profile = UserProfile(
            gender="female",
            skin_tone="medium",
            body_type="hourglass"
        )
        female_pref = StylePreference(
            preferred_styles=["party", "elegant"],
            preferred_colors=["olive green", "burgundy"]
        )

        female_recs = engine.generate_recommendations(
            user=female_user,
            profile=female_profile,
            preferences=female_pref,
            occasion="party",
            season="summer",
            limit=6
        )

        print(f"\n[Test A] Returned {len(female_recs)} recommendations.")
        assert len(female_recs) > 0, "TEST A FAILED: No recommendations returned"

        test_a_zero_men = True
        test_a_zero_shoes_or_accessories = True
        test_a_all_dresses = True

        for i, r in enumerate(female_recs, 1):
            outfit = r["outfit"]
            title = outfit.get("title") or outfit.get("name")
            retailer = outfit.get("retailer") or outfit.get("store")
            price = outfit.get("price")
            img = outfit.get("image_url")
            url = outfit.get("shopping_url") or outfit.get("product_url")
            print(f"  {i}. [{retailer}] {title} | INR {price} | URL: {url[:60]}...")

            # Strict Gender Check: ZERO men's items
            g_ok, g_reason = ProductValidator.validate_gender(title, target_gender="female")
            if not g_ok:
                test_a_zero_men = False
                print(f"     [FAIL] FAILED GENDER: {g_reason}")

            # Category Check: MUST be an actual dress
            c_ok, c_reason = ProductValidator.validate_category(title, target_category="dress", target_gender="female")
            if not c_ok:
                test_a_all_dresses = False
                test_a_zero_shoes_or_accessories = False
                print(f"     [FAIL] FAILED CATEGORY: {c_reason}")

        assert test_a_zero_men, "TEST A FAILED: Men's items leaked into female recommendations"
        assert test_a_all_dresses, "TEST A FAILED: Non-dress items returned for female dress request"
        print("[PASS] TEST A PASSED: 100% of returned items are female dresses with ZERO men's or non-dress items.")

        # ----------------------------------------------------------------------
        # TEST B — LIVE MEN RECOMMENDATIONS
        # ----------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST B: MEN RECOMMENDATION PIPELINE")
        print("Profile: Male | Occasion: Party | Season: Summer | Category: Clothing")
        print("=" * 80)

        male_user = User(email="test_male@aurafit.ai", username="test_male")
        male_profile = UserProfile(
            gender="male",
            skin_tone="fair",
            body_type="athletic"
        )
        male_pref = StylePreference(
            preferred_styles=["casual", "smart-casual"],
            preferred_colors=["navy", "royal blue"]
        )

        male_recs = engine.generate_recommendations(
            user=male_user,
            profile=male_profile,
            preferences=male_pref,
            occasion="party",
            season="summer",
            limit=6
        )

        print(f"\n[Test B] Returned {len(male_recs)} recommendations.")
        assert len(male_recs) > 0, "TEST B FAILED: No recommendations returned"

        test_b_zero_women = True
        test_b_all_menswear = True

        for i, r in enumerate(male_recs, 1):
            outfit = r["outfit"]
            title = outfit.get("title") or outfit.get("name")
            retailer = outfit.get("retailer") or outfit.get("store")
            price = outfit.get("price")
            img = outfit.get("image_url")
            url = outfit.get("shopping_url") or outfit.get("product_url")
            print(f"  {i}. [{retailer}] {title} | INR {price} | URL: {url[:60]}...")

            # Strict Gender Check: ZERO women's items
            g_ok, g_reason = ProductValidator.validate_gender(title, target_gender="male")
            if not g_ok:
                test_b_zero_women = False
                print(f"     [FAIL] FAILED GENDER: {g_reason}")

            # Category Check: MUST be valid menswear
            c_ok, c_reason = ProductValidator.validate_category(title, target_category="clothing", target_gender="male")
            if not c_ok:
                test_b_all_menswear = False
                print(f"     [FAIL] FAILED CATEGORY: {c_reason}")

        assert test_b_zero_women, "TEST B FAILED: Women's dresses leaked into male recommendations"
        assert test_b_all_menswear, "TEST B FAILED: Invalid category in male recommendations"
        print("[PASS] TEST B PASSED: 100% of returned items are menswear with ZERO women's dresses.")

        # ----------------------------------------------------------------------
        # TEST C — IMAGE & PRODUCT IDENTITY CONSISTENCY
        # ----------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST C: IMAGE & PRODUCT IDENTITY CONSISTENCY")
        print("Card image == Persisted image_url == Details image == Exact product URL")
        print("=" * 80)

        image_consistency_passed = True
        url_consistency_passed = True

        for r in female_recs:
            card_outfit = r["outfit"]
            db_outfit = db.session.get(Outfit, card_outfit["id"])
            assert db_outfit is not None, f"Persisted DB record missing for ID {card_outfit['id']}"

            details_dict = db_outfit.to_dict()

            # Verify image consistency
            if card_outfit["image_url"] != details_dict["image_url"]:
                image_consistency_passed = False
                print(f"[FAIL] Image mismatch for {card_outfit['id']}: Card '{card_outfit['image_url']}' != Details '{details_dict['image_url']}'")

            # Verify product URL consistency
            card_url = card_outfit.get("shopping_url") or card_outfit.get("product_url")
            details_url = details_dict.get("shopping_url") or details_dict.get("product_url")
            if card_url != details_url:
                url_consistency_passed = False
                print(f"[FAIL] URL mismatch for {card_outfit['id']}: Card '{card_url}' != Details '{details_url}'")

            # Verify exact product URL is valid direct retailer link
            if not Outfit.is_exact_product_url(details_url):
                url_consistency_passed = False
                print(f"[FAIL] Direct URL invalid for {card_outfit['id']}: {details_url}")

        assert image_consistency_passed, "TEST C FAILED: Image identity mismatch between card and details"
        assert url_consistency_passed, "TEST C FAILED: URL consistency mismatch"
        print("[PASS] TEST C PASSED: 100% exact match between Card, Details Page, and Direct Retailer URLs.")

        # ----------------------------------------------------------------------
        # TEST D — SIMILAR RECOMMENDATIONS VALIDATION
        # ----------------------------------------------------------------------
        # TEST D — SIMILAR RECOMMENDATIONS VALIDATION
        # ----------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST D: SIMILAR RECOMMENDATIONS VALIDATION")
        print("Every similar recommendation must pass the same gender and category filters.")
        print("=" * 80)

        # Generate similar recommendations for female top recommendation
        shopping_service = SerpApiShoppingService()
        female_similar = shopping_service.fetch_similar_live_products(
            female_recs[0]['outfit'], female_profile, limit=4
        )
        print(f"[Test D] Total female similar recommendations: {len(female_similar)}")
        assert len(female_similar) > 0, "TEST D FAILED: No female similar recommendations generated"

        similar_valid = True
        for i, sim in enumerate(female_similar, 1):
            title = sim.get("title") or sim.get("name")
            retailer = sim.get("retailer") or sim.get("store")
            img = sim.get("image_url")
            url = sim.get("shopping_url") or sim.get("product_url")
            print(f"  Female Sim {i}. [{retailer}] {title} | INR {sim.get('price')} | URL: {url[:60]}...")

            g_ok, _ = ProductValidator.validate_gender(title, target_gender="female")
            c_ok, _ = ProductValidator.validate_category(title, target_category="dress", target_gender="female")
            img_ok, _ = ProductValidator.validate_image(img)
            url_ok = Outfit.is_exact_product_url(url)

            if not (g_ok and c_ok and img_ok and url_ok):
                similar_valid = False
                print(f"     [FAIL] Similar item failed checks: gender={g_ok}, cat={c_ok}, img={img_ok}, url={url_ok}")

        # Also verify male similar recommendations from male top rec
        male_similar = getattr(engine, 'last_similar_recommendations', [])
        print(f"[Test D] Total male similar recommendations: {len(male_similar)}")
        for i, sim in enumerate(male_similar, 1):
            title = sim.get("title") or sim.get("name")
            retailer = sim.get("retailer") or sim.get("store")
            img = sim.get("image_url")
            url = sim.get("shopping_url") or sim.get("product_url")
            print(f"  Male Sim {i}. [{retailer}] {title} | INR {sim.get('price')} | URL: {url[:60]}...")

            g_ok, _ = ProductValidator.validate_gender(title, target_gender="male")
            c_ok, _ = ProductValidator.validate_category(title, target_category="clothing", target_gender="male")
            img_ok, _ = ProductValidator.validate_image(img)
            url_ok = Outfit.is_exact_product_url(url)

            if not (g_ok and c_ok and img_ok and url_ok):
                similar_valid = False
                print(f"     [FAIL] Male similar item failed checks: gender={g_ok}, cat={c_ok}, img={img_ok}, url={url_ok}")

        assert similar_valid, "TEST D FAILED: Similar recommendation failed validation"
        print("[PASS] TEST D PASSED: 100% of similar recommendations pass gender and category validation.")

        # ----------------------------------------------------------------------
        # TEST E — RETAILER & AVAILABILITY INTEGRITY
        # ----------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST E: RETAILER & PRICING INTEGRITY")
        print("Real retailer, real price, real image, real availability, direct product URL")
        print("=" * 80)

        retailers_seen = set()
        for r in female_recs:
            o = r["outfit"]
            assert o.get("retailer") and o.get("retailer").lower() != "aurafit official", "Retailer must be real external retailer"
            assert o.get("price") and float(o.get("price")) > 0, "Price must be real positive value"
            assert o.get("image_url") and not any(m in o.get("image_url") for m in ["aurafit.store", "placeholder", "unsplash"]), "Image must be real authentic product image"
            assert o.get("availability") in ("IN STOCK", "LIMITED"), "Availability must be in stock or limited"
            assert Outfit.is_exact_product_url(o.get("product_url")), "Product URL must be exact direct retailer URL"
            retailers_seen.add(o.get("retailer"))

        print(f"Retailers present in results: {retailers_seen}")
        print("[PASS] TEST E PASSED: All items have authentic retailer, price, image, availability, and direct URL.")

        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

if __name__ == '__main__':
    run_tests()
