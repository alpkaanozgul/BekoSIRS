import requests
r = requests.get('http://localhost:8000/api/v1/products/', params={'search': 'ankastre'})
print(f"Count: {r.json()['count']}")
print(f"First 3 products:")
for p in r.json()['results'][:3]:
    print(f"  - {p['name']}")
