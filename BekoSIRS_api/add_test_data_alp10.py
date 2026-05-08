import os
import sys
import django
import random
from collections import Counter
import concurrent.futures

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bekosirs_backend.settings')
django.setup()

from products.models import Product, ViewHistory, Wishlist, WishlistItem, Review, ProductOwnership
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def clear_old_data(user):
    print(f"[{user.username}] Eski etkileşim verileri temizleniyor...")
    ViewHistory.objects.filter(customer=user).delete()
    Wishlist.objects.filter(customer=user).delete() # Cascades to WishlistItem
    Review.objects.filter(customer=user).delete()
    ProductOwnership.objects.filter(customer=user).delete()
    print("Temizlik tamamlandı.")

def add_purchases(user, products_to_buy):
    print("Satın almalar ekleniyor...")
    objs = [
        ProductOwnership(customer=user, product=p, purchase_date=timezone.now().date())
        for p in products_to_buy
    ]
    ProductOwnership.objects.bulk_create(objs, ignore_conflicts=True)
    print(f"✅ {len(objs)} adet satın alma eklendi.")

def add_reviews(user, products_to_review):
    print("Yorumlar ekleniyor...")
    objs = []
    for p in products_to_review:
        # İnsan davranışı: Bazılarına 5, bazılarına 4 vb.
        rating = random.choices([5, 4, 3, 2, 1], weights=[50, 30, 10, 5, 5])[0]
        objs.append(
            Review(customer=user, product=p, rating=rating, comment=f'Gerçekçi otomatik yorum ({rating} yıldız)', is_approved=True)
        )
    Review.objects.bulk_create(objs, ignore_conflicts=True)
    print(f"✅ {len(objs)} adet yorum eklendi.")

def add_wishlist(user, products_to_wishlist):
    print("İstek listesi ekleniyor...")
    wishlist, _ = Wishlist.objects.get_or_create(customer=user)
    objs = [
        WishlistItem(wishlist=wishlist, product=p)
        for p in products_to_wishlist
    ]
    WishlistItem.objects.bulk_create(objs, ignore_conflicts=True)
    print(f"✅ {len(objs)} adet istek listesi elemanı eklendi.")

def add_views(user, products_for_views):
    print("Görüntülemeler ekleniyor...")
    # İnsanlar bazı ürünlere 1-2 kere, bazılarına 10 kere tıklar
    objs = []
    for p in products_for_views:
        # Rastgele 1 ile 15 arası tıklama
        view_count = random.randint(1, 15)
        objs.append(ViewHistory(customer=user, product=p, view_count=view_count))
        
    ViewHistory.objects.bulk_create(objs, ignore_conflicts=True)
    print(f"✅ {len(objs)} farklı ürüne ait toplam yüzlerce görüntüleme eklendi.")

def main():
    try:
        user = User.objects.get(username='alp10')
    except User.DoesNotExist:
        try:
            user = User.objects.get(email='alp10@example.com')
        except User.DoesNotExist:
            print("Kullanıcı 'alp10' bulunamadı. Oluşturuluyor...")
            user = User.objects.create_user(username='alp10', password='password123', email='alp10@example.com', role='customer')
            
    print(f"Kullanıcı: {user.username} (ID: {user.id})")
    
    # 1. Clear old data
    clear_old_data(user)
    
    products = list(Product.objects.all())
    if len(products) < 150:
        print("Yeterli ürün yok, lütfen veritabanına ürün ekleyin.")
        return
        
    # İnsan benzeri senaryo (Human-like behavior)
    # Toplam ~1000 etkileşim. 
    # Gerçek insan davranışı: İnceler -> İstek listesine atar -> Satın alır -> Yorumlar
    
    # İlgilenilen 150 ürün seç
    interested_products = random.sample(products, 150)
    
    # 150 ürüne tıklar (Views)
    products_for_views = interested_products
    
    # Bunların 100 tanesini istek listesine ekler (Wishlist)
    products_to_wishlist = random.sample(interested_products, 100)
    
    # İstek listesinden 80 tanesini, dışarıdan da 20 tane ani kararla satın alır (Purchases)
    products_to_buy = random.sample(products_to_wishlist, 80) + random.sample(list(set(products) - set(products_to_wishlist)), 20)
    
    # Satın aldıklarından 70 tanesine yorum yapar (Reviews)
    products_to_review = random.sample(products_to_buy, 70)
    
    # ThreadPoolExecutor ile eşzamanlı (concurrent) çalışma ile hızı arttırma
    print("\nVeritabanına concurrent (eşzamanlı) olarak ekleniyor...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        # Not: SQLite ve bazı pooler'lar concurrent insert'te kilitlenebilir, bulk_create zaten inanılmaz hızlıdır
        # ama isteğe binaen concurrent threadler ile atıyoruz.
        futures.append(executor.submit(add_views, user, products_for_views))
        futures.append(executor.submit(add_wishlist, user, products_to_wishlist))
        futures.append(executor.submit(add_purchases, user, products_to_buy))
        futures.append(executor.submit(add_reviews, user, products_to_review))
        
        concurrent.futures.wait(futures)
        
    print(f"\n🚀 İşlem Çok Hızlı Bir Şekilde Tamamlandı!")
    print(f"Toplam Simüle Edilen Etkileşim ~1000+")

if __name__ == '__main__':
    main()
