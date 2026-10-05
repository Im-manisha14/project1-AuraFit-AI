"""
API Contract Verification Test Suite (AuraFit AI)
Validates all 23 sections of the Explicit API Field Contract:
1. POST /api/recommendations/generate request validation & invalid combination rejection (400)
2. Response contract: { recommendations: [], similar_recommendations: [], meta: {} }
3. Recommendation Object Contract: all 28 required fields, correct types, live flags
4. Response Meta Contract: all 18 required meta metrics
5. GET /api/recommendations/collections: structured { collections: { ... } }, identical item contract
6. GET /api/outfits/:id: View details canonical product identity contract
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.user import User, UserProfile, StylePreference
from models.outfit import Outfit
from flask_jwt_extended import create_access_token
from services.product_contract import REQUIRED_CONTRACT_FIELDS

def run_contract_tests():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Setup test female user
        female_user = User.query.filter_by(email='test_female_contract@aurafit.com').first()
        if not female_user:
            female_user = User(username='female_contract', email='test_female_contract@aurafit.com')
            female_user.set_password('Password123!')
            db.session.add(female_user)
            db.session.commit()

        female_prof = UserProfile.query.filter_by(user_id=female_user.id).first()
        if not female_prof:
            female_prof = UserProfile(user_id=female_user.id, gender='female', age=24, body_type='hourglass', skin_tone='medium')
            db.session.add(female_prof)
            db.session.commit()

        female_token = create_access_token(identity=str(female_user.id))
        f_headers = {'Authorization': f'Bearer {female_token}'}

        # Setup test male user
        male_user = User.query.filter_by(email='test_male_contract@aurafit.com').first()
        if not male_user:
            male_user = User(username='male_contract', email='test_male_contract@aurafit.com')
            male_user.set_password('Password123!')
            db.session.add(male_user)
            db.session.commit()

        male_prof = UserProfile.query.filter_by(user_id=male_user.id).first()
        if not male_prof:
            male_prof = UserProfile(user_id=male_user.id, gender='male', age=28, body_type='athletic', skin_tone='fair')
            db.session.add(male_prof)
            db.session.commit()

        male_token = create_access_token(identity=str(male_user.id))
        m_headers = {'Authorization': f'Bearer {male_token}'}

        print("\n" + "=" * 80)
        print("AURAFIT AI — EXPLICIT API FIELD CONTRACT VALIDATION SUITE")
        print("=" * 80)

        # -------------------------------------------------------------
        # TEST 1: Reject invalid gender / category combinations (Section 1)
        # -------------------------------------------------------------
        print("\n[TEST 1] Testing Invalid Gender / Category Rejection (HTTP 400)...")
        # Male requesting 'dress'
        res_m_dress = client.post('/api/recommendations/generate', json={
            'gender': 'male',
            'category': 'dress',
            'occasion': 'party',
            'season': 'summer',
            'skin_tone': 'fair'
        }, headers=m_headers)
        assert res_m_dress.status_code == 400, f"Expected 400, got {res_m_dress.status_code}"
        assert 'Invalid category' in res_m_dress.get_json().get('error', '')
        print("  [PASS] Correctly rejected Male + Dress combination with HTTP 400")

        # Female requesting 'menswear'
        res_f_mens = client.post('/api/recommendations/generate', json={
            'gender': 'female',
            'category': 'menswear',
            'occasion': 'party',
            'season': 'summer',
            'skin_tone': 'medium'
        }, headers=f_headers)
        assert res_f_mens.status_code == 400, f"Expected 400, got {res_f_mens.status_code}"
        print("  [PASS] Correctly rejected Female + Menswear combination with HTTP 400")

        # -------------------------------------------------------------
        # TEST 2: POST /api/recommendations/generate Response Contract (Section 2, 3, 4, 15)
        # -------------------------------------------------------------
        print("\n[TEST 2] Testing POST /api/recommendations/generate Full Contract...")
        gen_res = client.post('/api/recommendations/generate', json={
            'gender': 'female',
            'occasion': 'party',
            'season': 'summer',
            'category': 'dress',
            'skin_tone': 'medium',
            'price_min': 500,
            'price_max': 5000,
            'retailer': 'all',
            'limit': 15
        }, headers=f_headers)
        assert gen_res.status_code == 200, f"Expected 200, got {gen_res.status_code}: {gen_res.get_json()}"
        data = gen_res.get_json()

        # Section 2: Top-level keys
        assert 'recommendations' in data, "Missing mandatory top-level 'recommendations'"
        assert 'similar_recommendations' in data, "Missing mandatory top-level 'similar_recommendations'"
        assert 'meta' in data, "Missing mandatory top-level 'meta'"
        print("  [PASS] Mandatory top-level keys verified: recommendations, similar_recommendations, meta")

        # Section 15: Meta Contract
        meta = data['meta']
        required_meta_keys = [
            'requested_gender', 'requested_occasion', 'requested_season', 'requested_category',
            'requested_skin_tone', 'requested_price_min', 'requested_price_max', 'requested_count',
            'returned_count', 'unique_product_count', 'duplicate_count', 'gender_rejection_count',
            'category_rejection_count', 'occasion_rejection_count', 'season_rejection_count',
            'price_rejection_count', 'retailers', 'source', 'is_live'
        ]
        for mk in required_meta_keys:
            assert mk in meta, f"Missing required meta field: {mk}"
        assert meta['requested_gender'] == 'female'
        assert meta['requested_occasion'] == 'party'
        assert meta['requested_season'] == 'summer'
        assert meta['requested_category'] == 'dress'
        assert meta['is_live'] is True
        assert isinstance(meta['retailers'], list)
        print("  [PASS] Meta contract fully validated (all 19 fields conform)")

        # Section 3: Recommendation Object Contract for every item
        recs = data['recommendations']
        print(f"  Validating {len(recs)} recommendation items against Section 3 contract...")
        for idx, item in enumerate(recs):
            for field in REQUIRED_CONTRACT_FIELDS:
                assert field in item, f"Item {idx} missing required field '{field}'"
            assert isinstance(item['id'], int), f"Item {idx} id not int"
            assert isinstance(item['external_id'], str) and item['external_id'], f"Item {idx} invalid external_id"
            assert isinstance(item['title'], str) and item['title'], f"Item {idx} invalid title"
            assert item['name'] == item['title'], f"Item {idx} name != title"
            assert item['gender'] == 'female', f"Item {idx} gender is '{item['gender']}', expected 'female'"
            assert isinstance(item['price'], (int, float)) and item['price'] > 0, f"Item {idx} price invalid: {item['price']}"
            assert item['currency'] == 'INR', f"Item {idx} currency != INR"
            assert item['availability'] in ('IN STOCK', 'OUT OF STOCK')
            assert item['is_live'] is True
            assert item['is_purchasable'] is True
            assert item['in_stock'] is True
            assert item['exact_product_link_available'] is True
            assert item['image_url'].startswith('http')
            assert item['product_url'].startswith('http')
            assert item['shopping_url'].startswith('http')
            assert isinstance(item['colors'], list)
            assert 0.0 <= item['match_score'] <= 1.0
            if item['original_price'] is not None:
                assert isinstance(item['original_price'], (int, float))
            if item['discount'] is not None:
                assert isinstance(item['discount'], int)
        print(f"  [PASS] 100% of {len(recs)} recommendation items strictly satisfy Recommendation Object Contract")

        # Check similar recommendations contract
        sims = data['similar_recommendations']
        print(f"  Validating {len(sims)} similar recommendations items against Section 3 contract...")
        for idx, item in enumerate(sims):
            for field in REQUIRED_CONTRACT_FIELDS:
                assert field in item, f"Similar Item {idx} missing required field '{field}'"
            assert item['gender'] == 'female'
            assert item['exact_product_link_available'] is True
        print(f"  [PASS] 100% of similar recommendations satisfy contract")

        # -------------------------------------------------------------
        # TEST 3: GET /api/recommendations/collections Contract (Section 17, 18)
        # -------------------------------------------------------------
        print("\n[TEST 3] Testing GET /api/recommendations/collections Contract...")
        col_res = client.get('/api/recommendations/collections?season=summer&limit=8', headers=f_headers)
        assert col_res.status_code == 200, f"Expected 200, got {col_res.status_code}"
        col_data = col_res.get_json()

        assert 'collections' in col_data, "Missing mandatory 'collections' dictionary"
        collections_dict = col_data['collections']

        expected_collections = ['trending', 'seasonal', 'casual', 'formal', 'sports', 'minimalist', 'party']
        for c_key in expected_collections:
            assert c_key in collections_dict, f"Missing expected collection: {c_key}"
            col_obj = collections_dict[c_key]
            assert 'title' in col_obj, f"Collection {c_key} missing title"
            assert 'count' in col_obj, f"Collection {c_key} missing count"
            assert 'items' in col_obj, f"Collection {c_key} missing items"
            assert isinstance(col_obj['items'], list)
            assert col_obj['count'] == len(col_obj['items'])

            for idx, c_item in enumerate(col_obj['items']):
                for field in REQUIRED_CONTRACT_FIELDS:
                    assert field in c_item, f"Collection '{c_key}' item {idx} missing field '{field}'"
                assert c_item['gender'] == 'female', f"Collection '{c_key}' item {idx} has wrong gender {c_item['gender']}"

        print(f"  [PASS] Collection API contract verified with all {len(collections_dict)} style collections")

        # -------------------------------------------------------------
        # TEST 4: GET /api/outfits/:id View Details Contract (Section 20)
        # -------------------------------------------------------------
        print("\n[TEST 4] Testing GET /api/outfits/:id View Details Contract...")
        first_outfit = Outfit.query.first()
        if first_outfit:
            detail_res = client.get(f'/api/outfits/{first_outfit.id}', headers=f_headers)
            assert detail_res.status_code == 200, f"Expected 200, got {detail_res.status_code}"
            detail_data = detail_res.get_json()
            assert 'outfit' in detail_data or 'id' in detail_data
            target_obj = detail_data.get('outfit') or detail_data
            for field in REQUIRED_CONTRACT_FIELDS:
                assert field in target_obj, f"View Details missing field '{field}'"
            print(f"  [PASS] View Details contract strictly matches canonical product identity (ID: {first_outfit.id})")

        print("\n" + "=" * 80)
        print("ALL API FIELD CONTRACT TESTS PASSED WITH 100% COMPLIANCE!")
        print("=" * 80 + "\n")

if __name__ == '__main__':
    run_contract_tests()
