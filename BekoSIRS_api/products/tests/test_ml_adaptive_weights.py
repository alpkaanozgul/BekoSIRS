"""
Oneri motorundaki adaptif hibrit agirlik davranisini dogrulayan testler.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from products.ml_recommender import HybridRecommender
from products.models import Category, Product, Recommendation

User = get_user_model()


def _build_recommender_for_unit_test():
    """Singleton yukleme yan etkileri olmadan hafif bir recommender ornegi kurar."""
    recommender = object.__new__(HybridRecommender)
    recommender._last_runtime_weights = {}
    return recommender


def test_cold_start_user_gets_high_popularity_weight():
    """0 etkilesimli kullanicida CF kuleleri sifir, populerlik baskin olmali."""
    recommender = _build_recommender_for_unit_test()
    mf, item_item, content, popularity = recommender._get_adaptive_weights({})

    # Soguk baslangicta MF (latent vektor yok) ve item-item (sepet yok) calisamaz.
    assert mf == pytest.approx(0.0)
    assert item_item == pytest.approx(0.0)
    assert content == pytest.approx(0.25)
    assert popularity >= 0.7
    # Agirliklar toplami 1.0 olmali.
    assert mf + item_item + content + popularity == pytest.approx(1.0)


def test_active_user_gets_high_cf_weight():
    """Yuksek etkilesimli kullanicida CF kuleleri (MF + item-item) baskin olmali."""
    recommender = _build_recommender_for_unit_test()
    interactions = {product_id: 1.0 for product_id in range(1, 26)}
    mf, item_item, content, popularity = recommender._get_adaptive_weights(interactions)

    assert mf >= 0.3
    assert item_item >= 0.3
    assert popularity <= 0.05
    assert mf + item_item + content + popularity == pytest.approx(1.0)


@pytest.mark.django_db
def test_recommendation_list_returns_weights_used_for_cold_start():
    """API, frontend skor dokumu icin kullanilan agirliklari dondurmeli."""
    category = Category.objects.create(name='Adaptive Weight Category')
    product = Product.objects.create(
        name='Önerilen Ürün',
        brand='Beko',
        category=category,
        price=Decimal('9999.99'),
        stock=10,
    )
    user = User.objects.create_user(
        username='adaptive-user',
        password='Adaptive123!',
        role='customer',
    )
    Recommendation.objects.create(
        customer=user,
        product=product,
        score=0.91,
        reason='Test önerisi',
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get('/api/v1/recommendations/')

    # Bu alanlar API'nin adaptif agirliklari dogru yansittigini gosterir; soguk
    # baslangicta MF + item-item sifir, populerlik ise en yuksek olmalidir.
    assert response.status_code == 200
    weights_used = response.data['ml_metrics']['weights_used']
    assert weights_used['mf'] == pytest.approx(0.0)
    assert weights_used['item_item'] == pytest.approx(0.0)
    assert weights_used['content'] == pytest.approx(0.25)
    assert weights_used['popularity'] == pytest.approx(0.75)
    assert weights_used['user_tier'] == 'cold_start'
    # Geriye donuk uyumluluk anahtari 'ncf' = MF agirligi olarak hala mevcut olmali.
    assert weights_used['ncf'] == pytest.approx(0.0)
