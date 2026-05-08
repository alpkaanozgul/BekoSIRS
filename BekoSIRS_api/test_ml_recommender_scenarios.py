import os
import sys
import django
import pandas as pd

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bekosirs_backend.settings')
django.setup()

from products.ml_recommender import NCFModel
from products.models import ViewHistory, WishlistItem, Review, ProductOwnership

def custom_build_interaction_matrix(self, purchase_weight, wishlist_weight, view_weight):
    interactions = []

    # Views (mapped to "Click" in user request)
    views = ViewHistory.objects.all().values('customer_id', 'product_id', 'view_count')
    for v in views:
        interactions.append({
            'user_id': v['customer_id'],
            'product_id': v['product_id'],
            'score': min(v['view_count'], 5) * view_weight,
            'source': 'view'
        })

    # Wishlist
    wishlist_items = WishlistItem.objects.filter(
        wishlist__customer__isnull=False
    ).values('wishlist__customer_id', 'product_id')
    for w in wishlist_items:
        interactions.append({
            'user_id': w['wishlist__customer_id'],
            'product_id': w['product_id'],
            'score': wishlist_weight,
            'source': 'wishlist'
        })

    # Reviews (keep existing behavior for review)
    reviews = Review.objects.all().values('customer_id', 'product_id', 'rating')
    for r in reviews:
        interactions.append({
            'user_id': r['customer_id'],
            'product_id': r['product_id'],
            'score': float(r['rating']),
            'source': 'review'
        })

    # Purchases
    purchases = ProductOwnership.objects.all().values('customer_id', 'product_id')
    for p in purchases:
        interactions.append({
            'user_id': p['customer_id'],
            'product_id': p['product_id'],
            'score': purchase_weight,
            'source': 'purchase'
        })

    if not interactions:
        return None

    df = pd.DataFrame(interactions)
    df = df.groupby(['user_id', 'product_id'])['score'].sum().reset_index()
    return df

def run_scenario(name, purchase_w, wishlist_w, view_w):
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"Weights -> Purchase: {purchase_w}, Wishlist: {wishlist_w}, Click/View: {view_w}")
    print(f"{'='*60}")
    
    # Monkey patch the method
    original_method = NCFModel._build_interaction_matrix
    
    def bound_custom_method(self):
        return custom_build_interaction_matrix(self, purchase_w, wishlist_w, view_w)
        
    NCFModel._build_interaction_matrix = bound_custom_method
    
    model = NCFModel()
    success = model.train(epochs=50, verbose=False)
    
    if success:
        metrics = model.training_metrics
        print(f"Sonuçlar:")
        print(f"  Train R2     : {metrics.get('train_r2')}")
        print(f"  Test R2      : {metrics.get('test_r2')}")
        print(f"  Hit Rate @10 : {metrics.get('hit_rate_at_10')}")
    else:
        print("Model eğitimi başarısız oldu (yeterli veri olmayabilir).")
        metrics = None
        
    # Restore original method
    NCFModel._build_interaction_matrix = original_method
    return metrics

if __name__ == '__main__':
    scenarios = [
        ("Senaryo 1 (Mevcut Durum)", 5.0, 3.0, 2.0),
        ("Senaryo 2 (Yüksek Satın Alma, Düşük Görüntüleme)", 7.0, 2.0, 1.0),
        ("Senaryo 3 (Görüntüleme Ön Planda)", 4.0, 2.0, 3.0),
        ("Senaryo 4 (İstek Listesi Ağırlıklı)", 5.0, 4.0, 1.5),
        ("Senaryo 5 (Dengeli Hibrit)", 6.0, 2.5, 1.5),
        ("Senaryo 6 (İnceleme Odaklı)", 5.0, 1.0, 2.5),
        ("Senaryo 7 (Güçlü Satın Alma, Zayıf İstek Listesi)", 8.0, 1.0, 1.5),
        ("Senaryo 8 (Güçlü İstek Listesi, Zayıf Görüntüleme)", 5.0, 3.5, 0.5),
        ("Senaryo 9 (Azınlık Görüntüleme Etkisi)", 6.0, 2.0, 0.5),
        ("Senaryo 10 (Klasik E-Ticaret Dengesi)", 5.0, 2.0, 1.0)
    ]
    
    print("Test başlatılıyor. 10 farklı senaryo denenecek. Lütfen bekleyin...")
    
    results = []
    for name, p_w, w_w, v_w in scenarios:
        metrics = run_scenario(name, p_w, w_w, v_w)
        if metrics:
            results.append({
                'name': name,
                'weights': f"Purchase={p_w}, Wishlist={w_w}, View={v_w}",
                'test_r2': metrics.get('test_r2', -999),
                'train_r2': metrics.get('train_r2', -999),
                'hit_rate': metrics.get('hit_rate_at_10', 0)
            })
            
    print(f"\n{'='*60}\nTest tamamlandı.")
    
    if results:
        best_scenario = max(results, key=lambda x: x['test_r2'])
        print(f"\n🏆 KAZANAN SENARYO 🏆")
        print(f"İsim: {best_scenario['name']}")
        print(f"Ağırlıklar: {best_scenario['weights']}")
        print(f"Test R²: {best_scenario['test_r2']}")
        print(f"Train R²: {best_scenario['train_r2']}")
        print(f"Hit Rate @10: {best_scenario['hit_rate']}")
        print(f"{'='*60}")
