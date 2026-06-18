"""Create load test users for Locust performance testing."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bekosirs_backend.settings')

import django
django.setup()

from products.models import CustomUser

# Create admin user for load testing
admin, created = CustomUser.objects.get_or_create(username='loadtest_admin')
if created or not admin.check_password('LoadAdmin123!'):
    admin.set_password('LoadAdmin123!')
    admin.is_staff = True
    admin.is_superuser = True
    admin.role = 'admin'
    admin.email = 'loadtest_admin@test.com'
    admin.first_name = 'Load'
    admin.last_name = 'Admin'
    admin.save()
    print(f"Admin created: loadtest_admin / LoadAdmin123!")
else:
    print(f"Admin already exists: loadtest_admin")

# Create customer user for load testing
customer, created = CustomUser.objects.get_or_create(username='loadtest_customer')
if created or not customer.check_password('LoadCustomer123!'):
    customer.set_password('LoadCustomer123!')
    customer.role = 'customer'
    customer.email = 'loadtest_customer@test.com'
    customer.first_name = 'Load'
    customer.last_name = 'Customer'
    customer.save()
    print(f"Customer created: loadtest_customer / LoadCustomer123!")
else:
    print(f"Customer already exists: loadtest_customer")

# Verify login works
import urllib.request, json, urllib.error

def post(url, data):
    req = urllib.request.Request(
        'http://localhost:8000' + url,
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'}
    )
    try:
        r = urllib.request.urlopen(req, timeout=5)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

# Test admin login (web)
s, d = post('/api/v1/token/', {'username': 'loadtest_admin', 'password': 'LoadAdmin123!', 'login_type': 'web'})
print(f"Admin login test: {s} - token={'access' in d}")

# Test customer login (mobile)
s, d = post('/api/v1/token/', {'username': 'loadtest_customer', 'password': 'LoadCustomer123!', 'login_type': 'mobile'})
print(f"Customer login test: {s} - token={'access' in d}")
if 'access' in d:
    print(f"Customer token: {d['access'][:30]}...")
