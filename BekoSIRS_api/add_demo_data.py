import os
import django
from django.utils import timezone
from datetime import timedelta
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bekosirs_backend.settings")
django.setup()

from products.models import Product, ProductAssignment, CustomUser

def create_demo_data():
    ProductAssignment.objects.all().delete()
    products = list(Product.objects.all())
    
    # We need user for assignments
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        user = CustomUser.objects.first()

    now = timezone.now()
    
    # Distribute products
    critical_prods = products[0:4]
    warning_prods = products[4:9]
    opportunity_prods = products[9:15]
    dead_stock_prods = products[15:19]
    healthy_prods = products[19:]
    
    assignments_to_create = []

    def add_sales(prod, count, days_ago_start=1, days_ago_end=28):
        for _ in range(count):
            days_ago = random.randint(days_ago_start, days_ago_end)
            assignments_to_create.append(ProductAssignment(
                product=prod,
                customer=user,
                quantity=1,
                status='DELIVERED',
                assigned_by=user,
                assigned_at=now - timedelta(days=days_ago)
            ))

    print("Setting up Critical products...")
    for p in critical_prods:
        p.stock = 8
        p.save()
        add_sales(p, 45) # velocity 1.5 -> stockout in 5.3 days

    print("Setting up Warning products...")
    for p in warning_prods:
        p.stock = 40
        p.save()
        add_sales(p, 60) # velocity 2.0 -> stockout in 20 days

    print("Setting up Opportunity products...")
    for p in opportunity_prods:
        p.stock = 150
        p.save()
        add_sales(p, 3) # velocity 0.1 -> opportunity

    print("Setting up Dead Stock products...")
    for p in dead_stock_prods:
        p.stock = 35
        p.save()
        # 0 sales

    print("Setting up Healthy products...")
    for p in healthy_prods:
        p.stock = 300
        p.save()
        add_sales(p, 30) # velocity 1.0 -> stockout in 300 days

    print("Adding 15-month history for forecast...")
    for p in critical_prods[:3] + warning_prods[:3]:
        # Generate upward trend
        base_sales = 5
        for month_offset in range(1, 16):
            # 15 months ago -> month_offset=15, sales ~ base_sales
            monthly_sales = base_sales + (16 - month_offset) * 3 + random.randint(-2, 2)
            if monthly_sales < 1: monthly_sales = 1
            
            # create sales for that month
            target_date = now - timedelta(days=month_offset * 30 + 15)
            assignments_to_create.append(ProductAssignment(
                product=p,
                customer=user,
                quantity=monthly_sales,
                status='DELIVERED',
                assigned_by=user,
                assigned_at=target_date
            ))

    print(f"Creating {len(assignments_to_create)} ProductAssignments...")
    field = ProductAssignment._meta.get_field('assigned_at')
    old_auto_now_add = field.auto_now_add
    field.auto_now_add = False

    try:
        ProductAssignment.objects.bulk_create(assignments_to_create, batch_size=1000)
    finally:
        field.auto_now_add = old_auto_now_add

    print("Demo data setup complete!")

if __name__ == '__main__':
    create_demo_data()
