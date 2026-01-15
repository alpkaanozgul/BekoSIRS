import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bekosirs_backend.settings')
django.setup()

from products.models import Product

# Test direct ORM filter
ankastre_products = Product.objects.filter(description__icontains='ankastre')
print(f"Products with 'ankastre' in description: {ankastre_products.count()}")

# Print first 5
for p in ankastre_products[:5]:
    print(f"  [{p.id}] {p.name}")

# Test all products count
all_products = Product.objects.count()
print(f"\nTotal products: {all_products}")
