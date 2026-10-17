import requests
import json

def test_formal_api():
    s = requests.Session()
    # Try login
    r = s.post('http://localhost:5000/api/auth/login', json={'email': 'test_female_contract@aurafit.com', 'password': 'Password123!'})
    if r.status_code != 200:
        print("Login failed:", r.status_code, r.text)
        return
    token = r.json().get('access_token')
    print("Logged in successfully.")
    
    # Request formal recommendations
    payload = {
        'occasion': 'formal',
        'gender': 'female',
        'category': 'dress',
        'limit': 25
    }
    resp = s.post(
        'http://localhost:5000/api/recommendations/generate',
        json=payload,
        headers={'Authorization': f'Bearer {token}'}
    )
    print("Generate status:", resp.status_code)
    data = resp.json()
    recs = data.get('recommendations', [])
    similar = data.get('similar_recommendations', [])
    print(f"Total recommendations returned: {len(recs)}")
    print(f"Total similar recommendations returned: {len(similar)}")
    
    for idx, item in enumerate(recs, 1):
        outfit = item.get('outfit') or item
        print(f"\n--- Product {idx} ---")
        print(f"ID: {outfit.get('id')}")
        print(f"Title: {outfit.get('title') or outfit.get('name')}")
        print(f"Retailer: {outfit.get('retailer') or outfit.get('store')}")
        print(f"Price: INR {outfit.get('price')}")
        print(f"Occasion in Outfit: {outfit.get('occasion')} | Primary: {outfit.get('primary_occasion')}")
        print(f"Match Score: {item.get('overall_score') or outfit.get('match_score')}")
        print(f"URL: {outfit.get('product_url')}")
        print(f"Image: {outfit.get('image_url')}")

if __name__ == '__main__':
    test_formal_api()
