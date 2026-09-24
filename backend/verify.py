import requests

try:
    # Need to login first to get a token!
    res = requests.post('http://127.0.0.1:5000/api/auth/login', json={'email': 'test@example.com', 'password': 'password'})
    token = res.json().get('token')
    
    headers = {'Authorization': f'Bearer {token}'}
    res = requests.post('http://127.0.0.1:5000/api/recommendations/generate', headers=headers, json={'occasion': 'casual', 'season': 'all'})
    
    data = res.json()
    print(f"Generated {len(data)} recommendations.")
    for i, rec in enumerate(data):
        print(f"{i+1}. {rec['outfit']['name']} | URL: {rec['outfit']['product_url']}")
except Exception as e:
    print(e)
