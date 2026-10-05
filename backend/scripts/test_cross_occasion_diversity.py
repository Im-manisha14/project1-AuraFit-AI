import json
import sys
import os

sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from extensions import db
from models.user import User, UserProfile
from flask_jwt_extended import create_access_token

app = create_app()
client = app.test_client()

with app.app_context():
    female_user = User.query.filter_by(email='test_female_contract@aurafit.com').first()
    if not female_user:
        female_user = User(username='female_contract', email='test_female_contract@aurafit.com')
        female_user.set_password('Password123!')
        db.session.add(female_user)
        db.session.commit()

    female_token = create_access_token(identity=str(female_user.id))
    headers = {'Authorization': f'Bearer {female_token}'}

    occasions_to_test = ["party", "casual", "formal", "date", "vacation", "wedding"]
    results_by_occasion = {}

    print("=" * 80)
    print("TESTING CROSS-OCCASION PRODUCT DIVERSITY & STRICT ISOLATION")
    print("=" * 80)

    for occ in occasions_to_test:
        payload = {
            "gender": "female",
            "category": "dress",
            "occasion": occ,
            "season": "summer",
            "skin_tone": "medium",
            "price_min": 500,
            "price_max": 5000,
            "limit": 10
        }
        res = client.post("/api/recommendations/generate", json=payload, headers=headers)
        assert res.status_code == 200, f"Failed for occasion {occ}: {res.status_code}"
        data = res.get_json()
        recs = data.get("recommendations", [])
        titles = [r["title"] for r in recs]
        ids = [r.get("external_id") or r.get("id") for r in recs]
        results_by_occasion[occ] = {
            "titles": titles,
            "ids": ids,
            "count": len(recs)
        }
        print(f"\nOccasion: [{occ.upper()}] -> Returned {len(recs)} products:")
        for i, t in enumerate(titles[:3], 1):
            print(f"  {i}. {t}")

    print("\n" + "=" * 80)
    print("CHECKING FOR CROSS-OCCASION DUPLICATES")
    print("=" * 80)

    overlap_found = False
    for i in range(len(occasions_to_test)):
        for j in range(i + 1, len(occasions_to_test)):
            occ1 = occasions_to_test[i]
            occ2 = occasions_to_test[j]
            ids1 = set(results_by_occasion[occ1]["ids"])
            ids2 = set(results_by_occasion[occ2]["ids"])
            common = ids1.intersection(ids2)
            if common:
                print(f"  [FAIL] Overlap between {occ1.upper()} and {occ2.upper()}: {len(common)} items")
                overlap_found = True
            else:
                print(f"  [PASS] Zero overlap between {occ1.upper()} and {occ2.upper()}")

    if not overlap_found:
        print("\n[SUCCESS] PERFECT OCCASION ISOLATION: No dresses repeated across occasions!")
    else:
        print("\n[WARNING] Some overlap detected.")
