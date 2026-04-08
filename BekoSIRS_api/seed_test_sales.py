import os
import sys
import random
from datetime import timedelta
from django.utils import timezone
from django.db import connection

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bekosirs_backend.settings')
sys.path.insert(0, os.path.dirname(__file__))

import django
django.setup()

from products.models import Product, CustomUser, ProductAssignment

def run_seed():
    print("Test satislari olusturuluyor...")
    
    products = list(Product.objects.all())
    if not products:
        print("Hata: Veritabaninda hic urun yok!")
        return
        
    sampled_products = random.sample(products, min(20, len(products)))
    
    customer = CustomUser.objects.filter(groups__name='Müşteri').first() or CustomUser.objects.first()
    admin_user = CustomUser.objects.filter(username='admin').first() or CustomUser.objects.first()

    now = timezone.now()
    four_months_ago = now - timedelta(days=120)
    
    created_count = 0
    sql_inserts = []
    
    for product in sampled_products:
        num_sales = random.randint(15, 50)
        for _ in range(num_sales):
            random_seconds = random.randint(0, int((now - four_months_ago).total_seconds()))
            random_date = four_months_ago + timedelta(seconds=random_seconds)
            qty = random.randint(1, 4)
            
            # Prepare for raw SQL to completely bypass signals and auto_now_add overhead
            # fields: product_id, assigned_to_id(user_id), assigned_by_id, quantity, status, assigned_at, updated_at
            
            date_str = random_date.strftime('%Y-%m-%d %H:%M:%S')
            
            sql_inserts.append(
                f"({product.id}, {customer.id}, {admin_user.id}, {qty}, 'delivered', '{date_str}')"
            )
            created_count += 1
            
    
    # Execute Raw SQL
    print(f"Toplam {created_count} kayit raw SQL ile veritabanina yaziliyor...")
    
    if sql_inserts:
        cursor = connection.cursor()
        
        # SQLite / Postgres bulk insert
        chunk_size = 100
        for i in range(0, len(sql_inserts), chunk_size):
            chunk = sql_inserts[i:i+chunk_size]
            values_str = ",\n".join(chunk)
            
            query = f"""
            INSERT INTO products_productassignment 
            (product_id, customer_id, assigned_by_id, quantity, status, assigned_at)
            VALUES 
            {values_str};
            """
            cursor.execute(query)
            
        cursor.close()
        

    print(f"Bitti! Rastgele {created_count} adet gercekci satis verisi, sinyalleri/loglari dondurmadan sisteme yuklendi.")

if __name__ == '__main__':
    run_seed()
