import requests

# Test without search - baseline
r1 = requests.get('http://localhost:8000/api/v1/products/')
print(f"Without search: {r1.json()['count']} products")

# Test with search
r2 = requests.get('http://localhost:8000/api/v1/products/', params={'search': 'ankastre'})
print(f"With search=ankastre: {r2.json()['count']} products")

# Print request URL to verify param is passed
print(f"Request URL: {r2.request.url}")

# Check if DRF is using filter_backends
# Try ordering filter to see if any filter works
r3 = requests.get('http://localhost:8000/api/v1/products/', params={'ordering': '-price'})
print(f"\nWith ordering=-price: {r3.json()['count']} products")
if r3.json()['results']:
    first_price = r3.json()['results'][0]['price']
    print(f"First product price: {first_price}")

# Test category filter
r4 = requests.get('http://localhost:8000/api/v1/products/', params={'category': 1})
print(f"\nWith category=1: {r4.json()['count']} products")
