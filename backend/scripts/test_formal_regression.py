"""
Regression test suite for AuraFit AI Formal Occasion Filtering and Pipeline Integrity.
Tests all 9 representative cases per Phase 7 requirements:
1. Clearly described casual beach dress (UNSUITABLE -> REJECT)
2. Explicitly described business-formal dress (SUITABLE -> ACCEPT)
3. Generic sheath dress with insufficient supporting information (UNCERTAIN -> REJECT)
4. Party bodycon dress (UNSUITABLE -> REJECT)
5. Wedding guest dress (UNSUITABLE -> REJECT)
6. Traditional ethnic dress (UNSUITABLE -> REJECT)
7. Product with missing description (UNCERTAIN -> REJECT)
8. Duplicate product from two search queries (DEDUPLICATED)
9. Product outside selected price range (REJECTED)
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.occasion_classifier import OccasionClassifier, OccasionDecision
from services.product_validator import validate_live_product
from app import create_app


def run_formal_regression_tests():
    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("AURAFIT AI FORMAL OCCASION REGRESSION TEST SUITE")
        print("=" * 70)

        results = []

        # -------------------------------------------------------------
        # Test 1: Clearly described casual beach dress
        # -------------------------------------------------------------
        t1_product = {
            'title': "Boho Floral Print Summer Beach Sundress",
            'description': "Lightweight breezy casual beach cover-up vacation dress for summer holiday.",
            'category': 'dress',
            'price': 899.0,
            'image_url': 'https://m.media-amazon.com/images/I/71example.jpg',
            'product_url': 'https://www.amazon.in/dp/B0BEACH01',
            'store': 'Amazon',
            'brand': 'BohoStyle'
        }
        dec1 = OccasionClassifier.classify_occasion_decision(t1_product, 'formal')
        v1 = validate_live_product(t1_product, requested_occasion='formal')
        pass1 = (dec1.status == OccasionDecision.UNSUITABLE and not v1['accepted'])
        results.append(('Test 1: Casual beach dress', pass1, f"Decision={dec1.status}, Reason={dec1.reason}"))

        # -------------------------------------------------------------
        # Test 2: Explicitly described business-formal dress
        # -------------------------------------------------------------
        t2_product = {
            'title': "Symbol Premium Women's Black Structured Tailored Formal Sheath Dress",
            'description': "Tailored formal sheath dress with structured notched neckline designed for business formal and corporate occasions.",
            'category': 'dress',
            'price': 2499.0,
            'image_url': 'https://m.media-amazon.com/images/I/61aPtlDki1L._AC_UL600_.jpg',
            'product_url': 'https://www.amazon.in/dp/B0DNM4YTWZ',
            'store': 'Amazon',
            'brand': 'Symbol Premium'
        }
        dec2 = OccasionClassifier.classify_occasion_decision(t2_product, 'formal')
        v2 = validate_live_product(t2_product, requested_occasion='formal')
        pass2 = (dec2.status == OccasionDecision.SUITABLE and v2['accepted'])
        results.append(('Test 2: Explicit business-formal dress', pass2, f"Decision={dec2.status}, Reason={dec2.reason}"))

        # -------------------------------------------------------------
        # Test 3: Generic sheath dress with insufficient supporting info
        # -------------------------------------------------------------
        t3_product = {
            'title': "Solid Sheath Knee-Length Dress for Women",
            'description': "Polyester sheath dress in regular fit with back zipper closure.",
            'category': 'dress',
            'price': 1299.0,
            'image_url': 'https://m.media-amazon.com/images/I/51generic.jpg',
            'product_url': 'https://www.amazon.in/dp/B0SHEATH01',
            'store': 'Amazon',
            'brand': 'GenericBrand'
        }
        dec3 = OccasionClassifier.classify_occasion_decision(t3_product, 'formal')
        v3 = validate_live_product(t3_product, requested_occasion='formal')
        pass3 = (dec3.status == OccasionDecision.UNCERTAIN and not v3['accepted'])
        results.append(('Test 3: Generic sheath without formal context', pass3, f"Decision={dec3.status}, Reason={dec3.reason}"))

        # -------------------------------------------------------------
        # Test 4: Party bodycon dress
        # -------------------------------------------------------------
        t4_product = {
            'title': "Glitter Sequin Ruched Mini Bodycon Party Dress",
            'description': "Sparkly backless bodycon mini dress for nightclub, bachelorette, and evening party.",
            'category': 'dress',
            'price': 1999.0,
            'image_url': 'https://m.media-amazon.com/images/I/71party.jpg',
            'product_url': 'https://www.amazon.in/dp/B0PARTY01',
            'store': 'Amazon',
            'brand': 'ClubGlam'
        }
        dec4 = OccasionClassifier.classify_occasion_decision(t4_product, 'formal')
        v4 = validate_live_product(t4_product, requested_occasion='formal')
        pass4 = (dec4.status == OccasionDecision.UNSUITABLE and not v4['accepted'])
        results.append(('Test 4: Party bodycon dress', pass4, f"Decision={dec4.status}, Reason={dec4.reason}"))

        # -------------------------------------------------------------
        # Test 5: Wedding guest dress
        # -------------------------------------------------------------
        t5_product = {
            'title': "Embellished Chiffon Maxi Gown for Wedding Guest",
            'description': "Pastel pink embroidered gown designed for wedding reception and ceremonies.",
            'category': 'dress',
            'price': 3499.0,
            'image_url': 'https://m.media-amazon.com/images/I/71wedding.jpg',
            'product_url': 'https://www.amazon.in/dp/B0WEDDING01',
            'store': 'Amazon',
            'brand': 'Koskii'
        }
        dec5 = OccasionClassifier.classify_occasion_decision(t5_product, 'formal')
        v5 = validate_live_product(t5_product, requested_occasion='formal')
        pass5 = (dec5.status == OccasionDecision.UNSUITABLE and not v5['accepted'])
        results.append(('Test 5: Wedding guest dress', pass5, f"Decision={dec5.status}, Reason={dec5.reason}"))

        # -------------------------------------------------------------
        # Test 6: Traditional ethnic dress
        # -------------------------------------------------------------
        t6_product = {
            'title': "Zari Work Silk Anarkali Gown with Dupatta",
            'description': "Traditional ethnic Indian anarkali dress with intricate embroidery.",
            'category': 'dress',
            'price': 2999.0,
            'image_url': 'https://m.media-amazon.com/images/I/71ethnic.jpg',
            'product_url': 'https://www.amazon.in/dp/B0ETHNIC01',
            'store': 'Amazon',
            'brand': 'Biba'
        }
        dec6 = OccasionClassifier.classify_occasion_decision(t6_product, 'formal')
        v6 = validate_live_product(t6_product, requested_occasion='formal')
        pass6 = (dec6.status == OccasionDecision.UNSUITABLE and not v6['accepted'])
        results.append(('Test 6: Traditional ethnic dress', pass6, f"Decision={dec6.status}, Reason={dec6.reason}"))

        # -------------------------------------------------------------
        # Test 7: Product with missing description
        # -------------------------------------------------------------
        t7_product = {
            'title': "Women Red Shift Dress",
            'description': "",
            'category': 'dress',
            'price': 1499.0,
            'image_url': 'https://m.media-amazon.com/images/I/51nodesc.jpg',
            'product_url': 'https://www.amazon.in/dp/B0NODESC01',
            'store': 'Amazon',
            'brand': 'ShiftBrand'
        }
        dec7 = OccasionClassifier.classify_occasion_decision(t7_product, 'formal')
        v7 = validate_live_product(t7_product, requested_occasion='formal')
        pass7 = (dec7.status == OccasionDecision.UNCERTAIN and not v7['accepted'])
        results.append(('Test 7: Missing description', pass7, f"Decision={dec7.status}, Reason={dec7.reason}"))

        # -------------------------------------------------------------
        # Test 8: Duplicate product from two search queries
        # -------------------------------------------------------------
        seen_ids = set()
        seen_urls = set()
        seen_imgs = set()
        query1_item = {
            'external_id': 'serpapi_amz_formal_dup_01',
            'title': "Life With Pockets Women's Black Tailored Formal Blazer Sheath Dress",
            'description': "Structured long-sleeve formal blazer sheath dress with lapel collar for business formal occasions.",
            'category': 'dress',
            'price': 3299.0,
            'image_url': 'https://m.media-amazon.com/images/I/61vM-8z8sbL._AC_UL600_.jpg',
            'product_url': 'https://www.amazon.in/dp/B0CMCPJZVT',
            'store': 'Amazon',
            'brand': 'Life With Pockets'
        }
        query2_item = {
            'external_id': 'serpapi_amz_formal_dup_01',
            'title': "Life With Pockets Women's Black Tailored Formal Blazer Sheath Dress - Size M",
            'description': "Structured long-sleeve formal blazer sheath dress with lapel collar for business formal occasions.",
            'category': 'dress',
            'price': 3299.0,
            'image_url': 'https://m.media-amazon.com/images/I/61vM-8z8sbL._AC_UL600_.jpg?width=600',
            'product_url': 'https://www.amazon.in/dp/B0CMCPJZVT?ref=sr_1_1',
            'store': 'Amazon',
            'brand': 'Life With Pockets'
        }
        v8_first = validate_live_product(query1_item, requested_occasion='formal', seen_identity_keys=seen_ids, seen_urls=seen_urls, seen_images=seen_imgs)
        v8_second = validate_live_product(query2_item, requested_occasion='formal', seen_identity_keys=seen_ids, seen_urls=seen_urls, seen_images=seen_imgs)
        pass8 = (v8_first['accepted'] and not v8_second['accepted'] and "duplicate" in v8_second['reason'].lower())
        results.append(('Test 8: Cross-query duplicate product', pass8, f"1st Accepted={v8_first['accepted']}, 2nd Rejected Reason={v8_second['reason']}"))

        # -------------------------------------------------------------
        # Test 9: Product outside selected price range
        # -------------------------------------------------------------
        t9_product = {
            'title': "Symbol Premium Women's Camel Structured Formal Sheath Midi Dress",
            'description': "Structured sleeveless formal sheath midi dress designed for corporate and formal wear.",
            'category': 'dress',
            'price': 15000.0,  # Price is 15,000 INR
            'image_url': 'https://m.media-amazon.com/images/I/61QyERxxPiL._AC_UL600_.jpg',
            'product_url': 'https://www.amazon.in/dp/B0FWBJRJW3',
            'store': 'Amazon',
            'brand': 'Symbol Premium'
        }
        # Request price range: 1000 - 2500 (1000_2500)
        v9 = validate_live_product(
            t9_product,
            requested_occasion='formal',
            price_range='1000_2500',
            price_min=1000.0,
            price_max=2500.0
        )
        pass9 = (not v9['accepted'] and "price" in v9['reason'].lower())
        results.append(('Test 9: Product outside price range', pass9, f"Accepted={v9['accepted']}, Reason={v9['reason']}"))

        # -------------------------------------------------------------
        # Print Summary
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        all_passed = True
        for name, passed, details in results:
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False
            print(f"[{status}] {name}")
            print(f"       {details}")
        print("-" * 70)
        print(f"OVERALL RESULT: {'ALL 9 TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        print("=" * 70)
        return all_passed


if __name__ == '__main__':
    success = run_formal_regression_tests()
    sys.exit(0 if success else 1)
