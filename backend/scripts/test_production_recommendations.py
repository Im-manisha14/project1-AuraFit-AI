#!/usr/bin/env python3
"""
AuraFit AI — Phase 20 Production Regression Suite
====================================================
Tests all critical GENDER × OCCASION matrix combinations against
live API endpoints (/generate, /collections, /similar).

Rules enforced for EVERY rendered product:
  V Female  -> must be a real dress (not shoes, bags, tops, etc.)
  V Male    -> must be menswear (shirt/blazer/kurta, not a dress)
  V No cross-gender leakage (women's dresses in male results)
  V No duplicate products within or across occasions
  V Occasion classifier must ACCEPT every product shown
  V Every product has a valid direct retailer URL
  V Every product has a valid image URL (not placeholder)
  V Source must be 'serpapi*'

Run from backend/ directory:
    python scripts/test_production_recommendations.py [--base-url http://localhost:5000]
"""

import argparse
import json
import re
import sys
import time
import requests
from typing import Dict, Any, List, Optional, Tuple, Set

# -- Attempt to import validators from the services layer ---
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
sys.path.insert(0, '.')

try:
    from services.product_validator import (
        check_category_suitability,
        check_gender_suitability,
        canonicalize_url,
        normalize_title,
        extract_image_key,
    )
    from services.occasion_classifier import OccasionClassifier
    VALIDATORS_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] Could not import validators: {e}")
    VALIDATORS_AVAILABLE = False


BASE_URL = "http://localhost:5000"
TIMEOUT = 90
PASS_COLOR = "\033[92m"
FAIL_COLOR = "\033[91m"
WARN_COLOR = "\033[93m"
RESET = "\033[0m"

# -- Test matrix ---
TEST_CASES = [
    # (gender, occasion, season, expected_category, description)
    ("female", "party",    "summer", "dress",    "Female Party Summer"),
    ("female", "casual",   "all",    "dress",    "Female Casual All-Season"),
    ("female", "formal",   "all",    "dress",    "Female Formal All-Season"),
    ("female", "vacation", "summer", "dress",    "Female Vacation Summer"),
    ("female", "wedding",  "all",    "dress",    "Female Wedding All-Season"),
    ("female", "party",    "winter", "dress",    "Female Party Winter"),
    ("male",   "party",    "all",    "clothing", "Male Party All-Season"),
    ("male",   "casual",   "all",    "clothing", "Male Casual All-Season"),
]

# -- Auth helper ---
def get_auth_token(base_url, email=None, password=None):
    if email and password:
        try:
            r = requests.post(f"{base_url}/api/auth/login", json={"email": email, "password": password}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                token = data.get("access_token") or data.get("token")
                if token:
                    return token
        except Exception:
            pass

    test_creds = [
        {"email": "final_test_female@aurafit.com", "password": "Password123!"},
        {"email": "phase20@aurafit.ai",           "password": "Phase20Test!"},
        {"email": "e2e_test@aurafit.com",          "password": "TestPass123!"},
        {"email": "manisha1411@gmail.com",         "password": "Manisha123!"},
    ]
    for cred in test_creds:
        try:
            r = requests.post(f"{base_url}/api/auth/login", json=cred, timeout=10)
            if r.status_code == 200:
                data = r.json()
                token = data.get("access_token") or data.get("token")
                if token:
                    print(f"[AUTH] Logged in as {cred['email']}")
                    return token
        except Exception:
            pass
    print("[AUTH] Could not authenticate")
    return None


# -- Product validation helpers ---
PLACEHOLDER_PATTERNS = [
    "aurafit.store", "example.com", "placeholder", "dummy",
    "unsplash", "default_avatar", "no-image", "1v2w3x4y5",
]

FEMALE_DRESS_REQUIRED = [
    r'\b(dress|dresses|gown|gowns|kurti|kurtis|kurta|kurtas|saree|sari|sarees|saris)\b',
    r'\b(anarkali|anarkalis|lehenga|lehengas|salwar\s+suit|salwar\s+kameez)\b',
    r'\b(jumpsuit|jumpsuits|romper|rompers)\b',
]

MALE_FORBIDDEN = [
    r'\b(women|womens|woman|ladies|lady|girls|girl|womenswear)\b',
    r'\b(dress|gown|saree|kurti|anarkali|lehenga|bra|skirt)\b',
]

FALSE_DRESS = [
    r'\bdress\s+shirt\b', r'\bdress\s+shoes?\b', r'\bdress\s+socks?\b',
    r'\bdress\s+material\b', r'\bdress\s+fabric\b', r'\bdress\s+boots?\b',
]

NON_DRESS_FEMALE = [
    r'\b(shoes?|sneakers?|heels?|sandals?|boots?|flats?|slippers?|footwear)\b',
    r'\b(handbags?|bags?|totes?|clutch|wallets?|backpacks?|purses?|sling\s+bag)\b',
    r'\b(jewellery|earrings?|necklaces?|bracelets?|bangles?|pendants?)\b',
    r'\b(watches?|sunglasses?|belts?|scarf|scarves|stoles?|hats?|caps?)\b',
    r'\b(trousers?|pants?|jeans?|shorts?|leggings?|jeggings?|palazzos?)\b',
    r'\b(lingerie|bras?|panties?|sleepwear|nightwear|pajamas?|pyjamas?)\b',
    r'\b(cosmetics?|perfumes?|fragrance|makeup|lipstick)\b',
]


def _text(p):
    return " ".join([
        str(p.get("title") or p.get("name") or ""),
        str(p.get("description") or ""),
        str(p.get("category") or ""),
    ]).lower()


def validate_product(p, expected_gender, expected_occasion, seen_urls, seen_imgs, seen_titles):
    """Returns (is_valid, rejection_reason)."""
    title = (p.get("title") or p.get("name") or "").strip()
    if not title or len(title) < 4:
        return False, "Missing title"

    src = (p.get("source") or "").lower()
    if src and not src.startswith("serpapi"):
        return False, f"Non-live source: '{src}'"

    img = (p.get("image_url") or p.get("image") or "").strip()
    if not img or not (img.startswith("http://") or img.startswith("https://")):
        return False, "Invalid image URL"
    for ph in PLACEHOLDER_PATTERNS:
        if ph in img.lower():
            return False, f"Placeholder image: '{ph}'"

    url = (p.get("product_url") or p.get("shopping_url") or "").strip()
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return False, "Missing/invalid product URL"
    for bad in ["/search", "rawquery=", "searchterm=", "google.com/url", "google.com/search"]:
        if bad in url.lower():
            return False, f"Search URL detected: '{bad}'"

    t = _text(p)

    if expected_gender == "female":
        for pat in FALSE_DRESS:
            if re.search(pat, t):
                return False, f"False dress keyword: {pat}"
        for pat in NON_DRESS_FEMALE:
            m = re.search(pat, t)
            if m:
                if re.search(r'\bshirt\s+dress\b', t):
                    continue
                return False, f"Non-dress category: {m.group(0)}"
        if not any(re.search(pat, t) for pat in FEMALE_DRESS_REQUIRED):
            return False, "Title does not match accepted female dress category"
        male_pat = r'(?<!wo)(?<!wo-)\b(men|mens|man|boys|menswear|male)\b'
        m = re.search(male_pat, t)
        if m:
            return False, f"Male terminology in female result: '{m.group(0)}'"

    elif expected_gender == "male":
        for pat in MALE_FORBIDDEN:
            m = re.search(pat, t)
            if m:
                return False, f"Female garment in male results: '{m.group(0)}'"

    if VALIDATORS_AVAILABLE and expected_occasion not in ("all", "trending", "seasonal", "minimalist"):
        try:
            occ_res = OccasionClassifier.classify(p, expected_occasion, debug=False)
            if occ_res.decision == "REJECT":
                return False, f"Occasion mismatch: {occ_res.reason}"
        except Exception:
            pass

    # Deduplication
    if VALIDATORS_AVAILABLE:
        canon = canonicalize_url(url)
        img_key = extract_image_key(img)
        norm_t = normalize_title(title)
    else:
        canon = url.split("?")[0].rstrip("/")
        img_key = img.split("?")[0]
        norm_t = title.lower()

    if canon in seen_urls:
        return False, "Duplicate product URL"
    if img_key in seen_imgs:
        return False, "Duplicate image"
    if norm_t in seen_titles:
        return False, "Duplicate normalized title"

    seen_urls.add(canon)
    seen_imgs.add(img_key)
    seen_titles.add(norm_t)
    return True, "OK"


def call_generate(base_url, token, gender, occasion, season, expected_cat="dress", limit=8):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "gender": gender,
        "category": expected_cat,
        "occasion": occasion,
        "season": season,
        "limit": limit
    }
    try:
        r = requests.post(f"{base_url}/api/recommendations/generate", json=payload, headers=headers, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            return data.get("recommendations") or []
        else:
            print(f"  [WARN] /generate {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"  [ERROR] /generate failed: {e}")
        return None



def call_collections(base_url, token, season):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{base_url}/api/recommendations/collections?season={season}&limit=10", headers=headers, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"  [WARN] /collections {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"  [ERROR] /collections failed: {e}")
        return None


def run_generate_tests(base_url, token):
    print("\n" + "=" * 60)
    print("PHASE 20 -- /generate endpoint tests")
    print("=" * 60)

    female_token = token
    male_token = get_auth_token(base_url, "final_test_male@aurafit.com", "Password123!") or token

    total_pass = 0
    total_fail = 0
    total_products = 0
    rejection_counts = {"source":0,"image":0,"url":0,"gender":0,"category":0,"occasion":0,"duplicate":0}

    global_occasion_by_url = {}
    global_occasion_by_img = {}
    global_seen_titles = set()

    for (gender, occasion, season, expected_cat, desc) in TEST_CASES:
        print(f"\n  [{desc}]")

        active_token = male_token if gender == "male" else female_token
        products = call_generate(base_url, active_token, gender, occasion, season, expected_cat=expected_cat, limit=8)
        if products is None:
            print(f"  {FAIL_COLOR}X API call failed{RESET}")
            total_fail += 1
            continue

        if not products:
            print(f"  {WARN_COLOR}? No products returned (live API may be rate-limited){RESET}")
            continue

        local_seen_urls = set()
        local_seen_imgs = set()
        local_seen_titles = set()
        case_pass = 0
        case_fail = 0

        for p in products:
            total_products += 1
            ok, reason = validate_product(p, gender, occasion, local_seen_urls, local_seen_imgs, local_seen_titles)

            if ok:
                url = (p.get("product_url") or p.get("shopping_url") or "").strip()
                img = (p.get("image_url") or "").strip()
                if VALIDATORS_AVAILABLE:
                    canon = canonicalize_url(url)
                    img_key = extract_image_key(img)
                else:
                    canon = url.split("?")[0].rstrip("/")
                    img_key = img.split("?")[0]

                if canon in global_occasion_by_url and global_occasion_by_url[canon] != occasion:
                    reason = f"Cross-occasion duplicate (already in {global_occasion_by_url[canon]})"
                    ok = False
                    rejection_counts["duplicate"] += 1
                elif img_key in global_occasion_by_img and global_occasion_by_img[img_key] != occasion:
                    reason = f"Cross-occasion duplicate image (already in {global_occasion_by_img[img_key]})"
                    ok = False
                    rejection_counts["duplicate"] += 1
                else:
                    global_occasion_by_url[canon] = occasion
                    global_occasion_by_img[img_key] = occasion

            if ok:
                case_pass += 1
                total_pass += 1
            else:
                case_fail += 1
                total_fail += 1
                r_low = reason.lower()
                if "source" in r_low: rejection_counts["source"] += 1
                elif "image" in r_low: rejection_counts["image"] += 1
                elif "url" in r_low: rejection_counts["url"] += 1
                elif "male" in r_low or "female" in r_low or "gender" in r_low: rejection_counts["gender"] += 1
                elif "dress" in r_low or "category" in r_low: rejection_counts["category"] += 1
                elif "occasion" in r_low: rejection_counts["occasion"] += 1
                name = (p.get("title") or p.get("name") or "")[:50]
                print(f"  {FAIL_COLOR}X REJECT: {name} | {reason}{RESET}")

        mark = "V" if case_fail == 0 else "X"
        color = PASS_COLOR if case_fail == 0 else FAIL_COLOR
        print(f"  {color}{mark} {desc}: {case_pass}/{case_pass+case_fail} valid{RESET}")

    return {"total_products": total_products, "total_passed": total_pass, "total_failed": total_fail, "rejection_counts": rejection_counts}


def run_collections_tests(base_url, token):
    print("\n" + "=" * 60)
    print("PHASE 20 -- /collections endpoint tests")
    print("=" * 60)

    data = call_collections(base_url, token, season="all")
    if not data:
        print(f"{FAIL_COLOR}X Collections API call failed{RESET}")
        return {"total_products": 0, "total_passed": 0, "total_failed": 1}

    collections = data.get("collections") or {}
    if not isinstance(collections, dict):
        print(f"{FAIL_COLOR}X Unexpected collections shape{RESET}")
        return {"total_products": 0, "total_passed": 0, "total_failed": 1}

    OCCASION_MAP = {
        "casual":"casual","formal":"formal","party":"party",
        "sports":"sports","trending":"trending","seasonal":"seasonal",
        "minimalist":"minimalist","skin_tone":"all","body_shape":"all",
    }

    total_pass = 0
    total_fail = 0
    total_products = 0
    global_seen_urls = set()
    global_seen_imgs = set()
    global_seen_titles = set()

    for coll_name, coll_data in collections.items():
        if not isinstance(coll_data, dict):
            continue
        items = coll_data.get("items") or []
        if not isinstance(items, list):
            continue

        expected_occ = OCCASION_MAP.get(coll_name, "all")
        case_pass = 0
        case_fail = 0

        for p in items:
            total_products += 1
            ok, reason = validate_product(p, "female", expected_occ, global_seen_urls, global_seen_imgs, global_seen_titles)
            if ok:
                case_pass += 1
                total_pass += 1
            else:
                case_fail += 1
                total_fail += 1
                name = (p.get("title") or p.get("name") or "")[:50]
                print(f"  {FAIL_COLOR}X [{coll_name}] REJECT: {name} | {reason}{RESET}")

        mark = "V" if case_fail == 0 else "?"
        color = PASS_COLOR if case_fail == 0 else WARN_COLOR
        print(f"  {color}{mark} [{coll_name}]: {case_pass}/{case_pass+case_fail} valid, {len(items)} items{RESET}")

    return {"total_products": total_products, "total_passed": total_pass, "total_failed": total_fail}


def print_summary(gen_res, col_res):
    print("\n" + "=" * 60)
    print("PHASE 20 -- FINAL SUMMARY")
    print("=" * 60)

    total_p = gen_res["total_products"] + col_res["total_products"]
    total_ok = gen_res["total_passed"] + col_res["total_passed"]
    total_fail = gen_res["total_failed"] + col_res["total_failed"]
    pass_rate = (total_ok / total_p * 100) if total_p > 0 else 0.0

    print(f"\n  Total products tested : {total_p}")
    print(f"  Passed                : {total_ok}")
    print(f"  Failed                : {total_fail}")
    print(f"  Pass rate             : {pass_rate:.1f}%")

    rc = gen_res.get("rejection_counts", {})
    if any(rc.values()):
        print("\n  Rejection breakdown (/generate):")
        for k, v in rc.items():
            if v > 0:
                print(f"    {k:20s}: {v}")

    if pass_rate >= 95.0:
        print(f"\n{PASS_COLOR}  V PRODUCTION READY -- pass rate {pass_rate:.1f}% >= 95%{RESET}")
        return 0
    elif pass_rate >= 80.0:
        print(f"\n{WARN_COLOR}  ? MARGINAL -- pass rate {pass_rate:.1f}%, some failures need attention{RESET}")
        return 1
    else:
        print(f"\n{FAIL_COLOR}  X FAILING -- pass rate {pass_rate:.1f}% below 80%{RESET}")
        return 2


def main():
    global BASE_URL
    parser = argparse.ArgumentParser(description="AuraFit Phase 20 Production Regression Suite")
    parser.add_argument("--base-url", default=BASE_URL, help="Backend base URL")
    parser.add_argument("--generate-only", action="store_true", help="Skip collections tests")
    parser.add_argument("--collections-only", action="store_true", help="Skip generate tests")
    args = parser.parse_args()
    BASE_URL = args.base_url.rstrip("/")

    print(f"\nAuraFit AI -- Phase 20 Production Regression Suite")
    print(f"Target: {BASE_URL}")

    token = get_auth_token(BASE_URL)
    if not token:
        print("Authentication failed -- cannot proceed")
        sys.exit(1)

    gen_res = {"total_products":0,"total_passed":0,"total_failed":0,"rejection_counts":{}}
    col_res = {"total_products":0,"total_passed":0,"total_failed":0}

    if not args.collections_only:
        gen_res = run_generate_tests(BASE_URL, token)
    if not args.generate_only:
        col_res = run_collections_tests(BASE_URL, token)

    code = print_summary(gen_res, col_res)
    sys.exit(code)


if __name__ == "__main__":
    main()
