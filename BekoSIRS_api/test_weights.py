"""
Adaptif Ağırlık Senaryoları Testi
=================================
_get_adaptive_weights metodunun dönüş değerlerini 3 farklı senaryoya göre
değiştirerek 20 rastgele müşteri için öneri listesi üretir ve
get_advanced_metrics ile kalite metriklerini karşılaştırır.

Senaryo A: Baseline (mevcut kodda tanımlı ağırlıklar)
Senaryo B: Agresif NCF — popülerliği sıfırlayarak NCF'yi maksimize eder
Senaryo C: İçerik/Benzerlik Odaklı — content ağırlığını artırır
"""

import os
import sys
import django

# Django ortamını kur
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bekosirs_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.ml_recommender import HybridRecommender

User = get_user_model()

# ═══════════════════════════════════════════════════════════════════════════
# SENARYO TANIMLARI
# ═══════════════════════════════════════════════════════════════════════════
# Her senaryo, _get_adaptive_weights'in interaction_count eşiklerine göre
# döndüreceği (ncf, content, popularity) üçlüsünü tanımlar.
#   Eşikler: 0 | 1-4 | 5-19 | 20+

SCENARIOS = {
    "Senaryo A (Baseline / Mevcut Durum)": {
        0:    (0.0, 0.2, 0.8),
        "lt5":  (0.2, 0.3, 0.5),
        "lt20": (0.4, 0.3, 0.3),
        "gte20":(0.6, 0.3, 0.1),
    },
    "Senaryo B (Agresif NCF)": {
        0:    (0.0, 0.2, 0.8),
        "lt5":  (0.4, 0.4, 0.2),
        "lt20": (0.6, 0.4, 0.0),
        "gte20":(0.8, 0.2, 0.0),
    },
    "Senaryo C (İçerik/Benzerlik Odaklı)": {
        0:    (0.0, 0.3, 0.7),
        "lt5":  (0.1, 0.6, 0.3),
        "lt20": (0.2, 0.7, 0.1),
        "gte20":(0.3, 0.6, 0.1),
    },
}

NUM_USERS = 20
TOP_N = 10


# ═══════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════

def make_adaptive_weights_fn(weight_map):
    """
    Verilen weight_map tablosuna göre _get_adaptive_weights'i taklit eden
    bir fonksiyon döndürür.
    """
    def _patched(self, user_interactions):
        interaction_count = self._count_meaningful_interactions(user_interactions)
        if interaction_count == 0:
            return weight_map[0]
        if interaction_count < 5:
            return weight_map["lt5"]
        if interaction_count < 20:
            return weight_map["lt20"]
        return weight_map["gte20"]
    return _patched


def run_scenario(recommender, scenario_name, weight_map, users):
    """
    Tek bir senaryoyu çalıştırır: ağırlıkları yamalar, her kullanıcı için
    öneri üretir, metrikleri toplar ve ortalamasını döndürür.
    """
    print(f"\n{'='*65}")
    print(f"  {scenario_name}")
    print(f"  Ağırlıklar (20+ | 5-19 | 1-4 | 0):")
    for tier_label, tier_key in [("20+ etkileşim", "gte20"), ("5-19 etkileşim", "lt20"),
                                  ("1-4 etkileşim", "lt5"), ("0 etkileşim", 0)]:
        w = weight_map[tier_key]
        print(f"    {tier_label}: NCF={w[0]}, Content={w[1]}, Popularity={w[2]}")
    print(f"{'='*65}")

    # Monkey-patch _get_adaptive_weights
    original_method = HybridRecommender._get_adaptive_weights
    HybridRecommender._get_adaptive_weights = make_adaptive_weights_fn(weight_map)

    total_avg_score = 0.0
    total_diversity = 0.0
    total_catalog = 0.0
    successful_users = 0

    for i, user in enumerate(users, 1):
        try:
            recs = recommender.recommend(user, top_n=TOP_N, ignore_cache=True)
            if not recs:
                print(f"    [{i}/{len(users)}] Kullanıcı {user.username}: boş liste, atlanıyor.")
                continue
            # recommend() döndürdüğü dict'lerde 'product' bir Django model nesnesi.
            # get_advanced_metrics ise serialized dict bekliyor, bu yüzden dönüştürüyoruz.
            normalized_recs = []
            for rec in recs:
                product_obj = rec.get('product')
                normalized_recs.append({
                    'product_id': rec.get('product_id'),
                    'score': rec.get('score', 0),
                    'product': {
                        'id': product_obj.id if product_obj else None,
                        'price': str(product_obj.price) if product_obj and product_obj.price else None,
                        'category': {
                            'name': product_obj.category.name if product_obj and product_obj.category else None,
                        },
                    },
                })
            metrics = recommender.get_advanced_metrics(normalized_recs)
            total_avg_score += metrics.get("avg_recommendation_score", 0)
            total_diversity += metrics.get("diversity_score", 0)
            total_catalog += metrics.get("catalog_coverage", 0)
            successful_users += 1
        except Exception as e:
            print(f"    [{i}/{len(users)}] Kullanıcı {user.username}: hata — {e}")

    # Orijinal metodu geri yükle
    HybridRecommender._get_adaptive_weights = original_method

    if successful_users == 0:
        print("  ⚠ Hiçbir kullanıcı için öneri üretilemedi!")
        return None

    result = {
        "avg_recommendation_score": round(total_avg_score / successful_users, 4),
        "diversity_score": round(total_diversity / successful_users, 4),
        "catalog_coverage": round(total_catalog / successful_users, 4),
        "successful_users": successful_users,
    }

    print(f"\n  📊 Sonuçlar ({successful_users} kullanıcı ortalaması):")
    print(f"     avg_recommendation_score : {result['avg_recommendation_score']}")
    print(f"     diversity_score          : {result['diversity_score']}")
    print(f"     catalog_coverage         : {result['catalog_coverage']}")

    return result


# ═══════════════════════════════════════════════════════════════════════════
# ANA ÇALIŞTIRMA
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  ADAPTIF AĞIRLIK SENARYO TESTİ")
    print("  3 senaryo × 20 kullanıcı × 10 öneri")
    print("=" * 65)

    # 1. Rastgele 20 aktif müşteri seç
    active_users = list(User.objects.filter(role='customer').order_by('?')[:NUM_USERS])
    if not active_users:
        print("HATA: Veritabanında müşteri bulunamadı.")
        sys.exit(1)

    if len(active_users) < NUM_USERS:
        print(f"  ⚠ Sadece {len(active_users)} müşteri bulundu, bunlarla devam ediliyor.")

    print(f"  Seçilen kullanıcılar: {[u.username for u in active_users]}")

    # 2. Recommender'ı başlat (modeller bir kez eğitilir, sadece ağırlıklar değişir)
    recommender = HybridRecommender()
    if not recommender._loaded:
        print("\n  Model henüz eğitilmemiş, eğitim başlatılıyor...")
        recommender.train(epochs=50, verbose=True)

    # 3. Her senaryoyu çalıştır
    all_results = {}
    for scenario_name, weight_map in SCENARIOS.items():
        result = run_scenario(recommender, scenario_name, weight_map, active_users)
        if result:
            all_results[scenario_name] = result

    # ═══════════════════════════════════════════════════════════════════════
    # SONUÇ TABLOSU
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n\n{'='*80}")
    print("  KARŞILAŞTIRMA TABLOSU")
    print(f"{'='*80}")
    header = f"{'Senaryo':<45} {'avg_score':>10} {'diversity':>10} {'coverage':>10}"
    print(header)
    print("-" * 80)
    for name, r in all_results.items():
        short_name = name[:44]
        print(f"{short_name:<45} {r['avg_recommendation_score']:>10.4f} {r['diversity_score']:>10.4f} {r['catalog_coverage']:>10.4f}")
    print("-" * 80)

    # ═══════════════════════════════════════════════════════════════════════
    # EN İYİ SENARYO
    # ═══════════════════════════════════════════════════════════════════════
    if all_results:
        # Bileşik skor: avg_score(%40) + diversity(%30) + coverage(%30)
        def composite_score(r):
            return (r['avg_recommendation_score'] * 0.4 +
                    r['diversity_score'] * 0.3 +
                    r['catalog_coverage'] * 0.3)

        best_name = max(all_results, key=lambda n: composite_score(all_results[n]))
        best = all_results[best_name]

        print(f"\n{'='*65}")
        print(f"  🏆 EN İYİ SENARYO 🏆")
        print(f"{'='*65}")
        print(f"  İsim              : {best_name}")
        print(f"  avg_rec_score     : {best['avg_recommendation_score']}")
        print(f"  diversity_score   : {best['diversity_score']}")
        print(f"  catalog_coverage  : {best['catalog_coverage']}")
        print(f"  Bileşik Skor      : {composite_score(best):.4f}")
        print(f"  (Bileşik = avg_score×0.4 + diversity×0.3 + coverage×0.3)")
        print(f"{'='*65}")
    else:
        print("\n  ⚠ Hiçbir senaryodan sonuç alınamadı.")
