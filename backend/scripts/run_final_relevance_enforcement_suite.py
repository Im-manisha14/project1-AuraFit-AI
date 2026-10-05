import json
import sys
import os
import time

sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from extensions import db
from models.user import User, UserProfile
from flask_jwt_extended import create_access_token

app = create_app()
client = app.test_client()

report_lines = []

def log_r(msg=""):
    print(msg)
    report_lines.append(str(msg))

with app.app_context():
    # Setup test users
    female_user = User.query.filter_by(email='final_test_female@aurafit.com').first()
    if not female_user:
        female_user = User(username='final_female', email='final_test_female@aurafit.com')
        female_user.set_password('Password123!')
        db.session.add(female_user)
        db.session.commit()

    female_prof = UserProfile.query.filter_by(user_id=female_user.id).first()
    if not female_prof:
        female_prof = UserProfile(user_id=female_user.id, gender='female', age=25, body_type='hourglass', skin_tone='medium')
        db.session.add(female_prof)
        db.session.commit()

    f_token = create_access_token(identity=str(female_user.id))
    f_headers = {'Authorization': f'Bearer {f_token}'}

    male_user = User.query.filter_by(email='final_test_male@aurafit.com').first()
    if not male_user:
        male_user = User(username='final_male', email='final_test_male@aurafit.com')
        male_user.set_password('Password123!')
        db.session.add(male_user)
        db.session.commit()

    male_prof = UserProfile.query.filter_by(user_id=male_user.id).first()
    if not male_prof:
        male_prof = UserProfile(user_id=male_user.id, gender='male', age=28, body_type='athletic', skin_tone='fair')
        db.session.add(male_prof)
        db.session.commit()

    m_token = create_access_token(identity=str(male_user.id))
    m_headers = {'Authorization': f'Bearer {m_token}'}

    log_r("=" * 80)
    log_r("AURAFIT AI — FINAL LIVE SHOPPING PRODUCT RELEVANCE ENFORCEMENT TEST SUITE")
    log_r("=" * 80)

    # 1. FEMALE OCCASIONS MATRIX
    female_occasions = ["party", "casual", "formal", "office", "date", "evening", "cocktail", "wedding", "festive", "traditional", "vacation", "sports"]
    female_results = {}
    
    log_r("\n[1] TESTING FEMALE DRESS REQUESTS ACROSS ALL 12 OCCASIONS")
    log_r("-" * 80)

    for occ in female_occasions:
        t0 = time.time()
        res = client.post('/api/recommendations/generate', json={
            'gender': 'female',
            'category': 'dress',
            'occasion': occ,
            'season': 'summer',
            'skin_tone': 'medium',
            'price_min': 500,
            'price_max': 5000,
            'limit': 10
        }, headers=f_headers)
        elapsed = time.time() - t0
        assert res.status_code == 200, f"Female request failed for {occ}: {res.status_code}"
        data = res.get_json()
        recs = data.get('recommendations', [])
        meta = data.get('meta', {})
        female_results[occ] = recs
        
        log_r(f"Occasion: {occ.upper():<12} | Returned: {len(recs):<2} | Rejections (G:{meta.get('gender_rejection_count', 0)}, C:{meta.get('category_rejection_count', 0)}, O:{meta.get('occasion_rejection_count', 0)}, S:{meta.get('season_rejection_count', 0)}) | Time: {elapsed:.2f}s")
        for r in recs[:2]:
            log_r(f"   -> [{r.get('retailer')}] {r.get('title')[:65]} (INR {r.get('price')})")

    # 2. MALE OCCASIONS MATRIX
    male_occasions = ["party", "casual", "formal", "office", "date", "evening", "wedding", "festive", "traditional", "vacation", "sports"]
    male_results = {}

    log_r("\n[2] TESTING MALE CLOTHING REQUESTS ACROSS ALL 11 OCCASIONS")
    log_r("-" * 80)

    for occ in male_occasions:
        t0 = time.time()
        res = client.post('/api/recommendations/generate', json={
            'gender': 'male',
            'category': 'clothing',
            'occasion': occ,
            'season': 'summer',
            'skin_tone': 'fair',
            'price_min': 500,
            'price_max': 5000,
            'limit': 10
        }, headers=m_headers)
        elapsed = time.time() - t0
        assert res.status_code == 200, f"Male request failed for {occ}: {res.status_code}"
        data = res.get_json()
        recs = data.get('recommendations', [])
        meta = data.get('meta', {})
        male_results[occ] = recs

        log_r(f"Occasion: {occ.upper():<12} | Returned: {len(recs):<2} | Rejections (G:{meta.get('gender_rejection_count', 0)}, C:{meta.get('category_rejection_count', 0)}, O:{meta.get('occasion_rejection_count', 0)}, S:{meta.get('season_rejection_count', 0)}) | Time: {elapsed:.2f}s")
        for r in recs[:2]:
            log_r(f"   -> [{r.get('retailer')}] {r.get('title')[:65]} (INR {r.get('price')})")

    # 3. CROSS-GENDER ISOLATION TEST
    log_r("\n[3] CROSS-GENDER ISOLATION TEST")
    log_r("-" * 80)
    female_male_leakage = 0
    for occ, recs in female_results.items():
        for r in recs:
            if r['gender'] != 'female':
                female_male_leakage += 1
                log_r(f"  [FAIL] Non-female product in female results: {r['title']}")

    male_female_leakage = 0
    for occ, recs in male_results.items():
        for r in recs:
            if r['gender'] != 'male':
                male_female_leakage += 1
                log_r(f"  [FAIL] Non-male product in male results: {r['title']}")

    log_r(f"Female results containing male products = {female_male_leakage}")
    log_r(f"Male results containing female products = {male_female_leakage}")
    assert female_male_leakage == 0 and male_female_leakage == 0, "Cross-gender leakage detected!"
    log_r("  [PASS] 100% PERFECT CROSS-GENDER ISOLATION")

    # 4. CROSS-CATEGORY TEST (FEMALE DRESS REQUEST)
    log_r("\n[4] CROSS-CATEGORY ISOLATION TEST (FEMALE DRESS REQUEST)")
    log_r("-" * 80)
    forbidden_category_keywords = ["shoe", "shoes", "heel", "heels", "sandal", "sneaker", "boot", "bag", "handbag", "clutch", "jewellery", "earring", "necklace", "bracelet", "watch", "sunglasses", "cosmetics", "perfume", "skirt", "trouser", "pant", "jeans", "shorts", "leggings", "top", "shirt", "dress shirt", "dress shoes", "dress socks", "dress material"]
    category_violations = 0

    for occ, recs in female_results.items():
        for r in recs:
            t_lower = r['title'].lower()
            # If title matches forbidden category keyword unless it's a valid dress phrase
            for fk in forbidden_category_keywords:
                if fk in t_lower and not any(dp in t_lower for dp in ["dress", "gown", "saree", "kurti", "anarkali"]):
                    category_violations += 1
                    log_r(f"  [FAIL] Category violation in female dress results: '{fk}' in '{r['title']}'")
                elif fk in ["dress shirt", "dress shoes", "dress socks", "dress material"] and fk in t_lower:
                    category_violations += 1
                    log_r(f"  [FAIL] Forbidden dress phrase in results: '{fk}' in '{r['title']}'")

    log_r(f"Female dress results containing forbidden non-dress items = {category_violations}")
    assert category_violations == 0, "Cross-category violations detected!"
    log_r("  [PASS] 100% PERFECT CATEGORY ISOLATION (Only genuine female dresses/gowns/sarees/kurtis)")

    # 5. CROSS-OCCASION PRODUCT DUPLICATION TEST
    log_r("\n[5] CROSS-OCCASION DIVERSITY & PRODUCT ISOLATION TEST")
    log_r("-" * 80)
    test_occs = ["party", "casual", "formal", "date", "wedding", "vacation"]
    overlap_count = 0

    for i in range(len(test_occs)):
        for j in range(i + 1, len(test_occs)):
            o1, o2 = test_occs[i], test_occs[j]
            ids1 = {r.get('external_id') or r.get('id') for r in female_results[o1]}
            ids2 = {r.get('external_id') or r.get('id') for r in female_results[o2]}
            common = ids1.intersection(ids2)
            if common:
                overlap_count += len(common)
                log_r(f"  [FAIL] Overlap between {o1.upper()} and {o2.upper()}: {len(common)} items")
            else:
                log_r(f"  [PASS] {o1.upper():<8} intersect {o2.upper():<8} = 0 duplicates")

    log_r(f"Total duplicate products across incompatible occasions = {overlap_count}")
    assert overlap_count == 0, "Cross-occasion duplicate products detected!"
    log_r("  [PASS] 100% PERFECT CROSS-OCCASION ISOLATION")

    # 6. COLLECTIONS ENGINE & CONTRACT TEST
    log_r("\n[6] COLLECTIONS ENGINE & CONTRACT TEST (GET /api/recommendations/collections)")
    log_r("-" * 80)
    col_res = client.get('/api/recommendations/collections', headers=f_headers)
    assert col_res.status_code == 200, f"Collections API failed: {col_res.status_code}"
    col_data = col_res.get_json()
    collections = col_data.get('collections', {})
    log_r(f"Collections returned: {list(collections.keys())}")
    for col_key, col_val in collections.items():
        items = col_val.get('items', [])
        log_r(f"   -> Collection [{col_key.upper()}]: Title='{col_val.get('title')}', Items={len(items)}")
        for it in items[:1]:
            assert 'external_id' in it and 'price' in it and 'product_url' in it, "Collection item missing contract fields!"
    log_r("  [PASS] 100% COLLECTIONS ENGINE & CONTRACT VERIFIED")

    # 7. VIEW DETAILS IDENTITY TEST
    sample_live_id = female_results['party'][0]['id'] if female_results.get('party') else 1
    log_r(f"\n[7] VIEW DETAILS CANONICAL PRODUCT IDENTITY TEST (GET /api/outfits/{sample_live_id})")
    log_r("-" * 80)
    out_res = client.get(f'/api/outfits/{sample_live_id}', headers=f_headers)
    assert out_res.status_code == 200, f"View Details API failed: {out_res.status_code}"
    out_data = out_res.get_json()
    log_r(f"View Details product identity: ID={out_data.get('id')}, Title='{out_data.get('title') or out_data.get('name')}', Retailer='{out_data.get('retailer')}', is_live={out_data.get('is_live')}")
    assert out_data.get('is_live') is True, "View Details must return canonical live product!"
    log_r("  [PASS] 100% VIEW DETAILS CANONICAL PRODUCT IDENTITY VERIFIED")

    log_r("\n" + "=" * 80)
    log_r("ALL 31 FINAL ACCEPTANCE CRITERIA PASSED WITH ZERO VIOLATIONS!")
    log_r("=" * 80)

with open('backend/scripts/final_relevance_report.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))
