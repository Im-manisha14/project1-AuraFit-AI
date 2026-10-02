import requests

base_url = 'http://localhost:5000/api'

# 1. Login
resp = requests.post(f"{base_url}/auth/login", json={
    'email': 'test_engine_female@aurafit.com',
    'password': 'Password123!'
})
token = resp.json().get('token') or resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# 2. Test Collections Endpoint
print("=" * 60)
print("TESTING /api/recommendations/collections")
print("=" * 60)
col_resp = requests.get(f"{base_url}/recommendations/collections?season=summer&limit=8", headers=headers)
print(f"Collections HTTP Status: {col_resp.status_code}")
collections = col_resp.json()

for col_name, outfits in collections.items():
    print(f"\nCollection: {col_name:15} | Count: {len(outfits)}")
    seen_imgs = set()
    dup_imgs = []
    broken_links = []
    mock_items = []
    
    for o in outfits:
        img = (o.get('image_url') or '').strip()
        if img in seen_imgs:
            dup_imgs.append(img[:40])
        seen_imgs.add(img)
        
        if not o.get('exact_product_link_available') or not o.get('shopping_url'):
            broken_links.append(o.get('name'))
        if o.get('source') == 'mock':
            mock_items.append(o.get('name'))
            
    print(f"   Duplicate Images: {len(dup_imgs)} {'[FAIL]' if dup_imgs else '[PASS]'}")
    print(f"   Broken/Missing Links: {len(broken_links)} {'[FAIL]' if broken_links else '[PASS]'}")
    print(f"   Mock Products: {len(mock_items)} {'[FAIL]' if mock_items else '[PASS]'}")
    if outfits:
        sample = outfits[0]
        print(f"   Sample: {sample.get('name')[:35]} | Store: {sample.get('store')} | URL: {sample.get('shopping_url')[:35]}...")

# 3. Test Generate Endpoint Deduplication
print("\n" + "=" * 60)
print("TESTING /api/recommendations/generate DEDUPLICATION")
print("=" * 60)

gen_resp = requests.post(f"{base_url}/recommendations/generate", json={
    'occasion': 'party',
    'season': 'summer',
    'price_range': 'all',
    'results': 25
}, headers=headers)
print(f"Generate HTTP Status: {gen_resp.status_code}")
gen_data = gen_resp.json()
recs = gen_data.get('recommendations', [])
sims = gen_data.get('similar_recommendations', [])

print(f"Recommendations count: {len(recs)} | Similar count: {len(sims)}")

rec_imgs = [r['outfit']['image_url'] for r in recs if r.get('outfit', {}).get('image_url')]
rec_urls = [r['outfit']['product_url'] for r in recs if r.get('outfit', {}).get('product_url')]

print(f"Total image URLs: {len(rec_imgs)} | Unique image URLs: {len(set(rec_imgs))}")
print(f"Total product URLs: {len(rec_urls)} | Unique product URLs: {len(set(rec_urls))}")
print(f"Image Duplicate Check: {'PASS' if len(rec_imgs) == len(set(rec_imgs)) else 'FAIL'}")
print(f"Product URL Duplicate Check: {'PASS' if len(rec_urls) == len(set(rec_urls)) else 'FAIL'}")

# Cross-check similar items do not duplicate main recommendations
sim_imgs = [s['image_url'] for s in sims if s.get('image_url')]
overlap = set(rec_imgs).intersection(set(sim_imgs))
print(f"Similar vs Main Image Overlap: {len(overlap)} {'[FAIL]' if overlap else '[PASS]'}")
