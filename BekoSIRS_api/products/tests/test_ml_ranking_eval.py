"""
Siralama degerlendirmesi (leave-one-out Recall@K / NDCG@K / MAP@K) testleri.

evaluate_ranking; R² yerine oneri sistemlerinde anlamli olan sirali metrikleri
uretmeli, metrikler [0, 1] araliginda olmali ve uygun (>=2 etkilesimli) kullanici
yoksa zarifce bos (None) donmeli.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from products.ml_recommender import (
    HybridRecommender,
    MatrixFactorizationModel,
    ItemItemCFModel,
    ContentBasedModel,
)
from products.models import Category, Product, ProductOwnership, ViewHistory

User = get_user_model()


def _build_trained_recommender():
    """Singleton yan etkileri olmadan alt modelleri gercek veride egitilmis recommender."""
    recommender = object.__new__(HybridRecommender)
    recommender._last_runtime_weights = {}
    recommender.ncf = MatrixFactorizationModel()
    recommender.itemitem = ItemItemCFModel()
    recommender.content = ContentBasedModel()
    recommender.ncf.train(verbose=False)
    recommender.itemitem.train(verbose=False)
    recommender.content.train(verbose=False)
    return recommender


@pytest.fixture
def catalog(db):
    """Ayirt edici metinli urunler — content kulesinin TF-IDF'i terim bulabilsin."""
    category = Category.objects.create(name='Eval Category')
    names = [
        ('Buzdolabi NoFrost', 'genis hacimli soğutucu dondurucu'),
        ('Camasir Makinesi', 'yuksek devirli sessiz yikama'),
        ('Bulasik Makinesi', 'enerji tasarruflu kurutma programi'),
        ('Ankastre Firin', 'turbo fanli pisirme termostat'),
        ('Split Klima', 'inverter sogutma isitma sessiz'),
        ('Robot Supurge', 'akilli haritalama guclu emis'),
    ]
    return [
        Product.objects.create(
            name=name, description=desc, brand='Beko', category=category,
            price=Decimal('5000.00'), stock=10,
        )
        for name, desc in names
    ]


@pytest.mark.django_db
def test_evaluate_ranking_returns_bounded_metrics(catalog):
    """Yeterli etkilesim oldugunda metrikler [0, 1] araliginda ve tutarli olmali."""
    today = timezone.now().date()
    # Bes kullanici, her biri ardisik iki urune sahip → holdout uretilebilir.
    for i in range(5):
        u = User.objects.create_user(username=f'eval-{i}', password='X!', role='customer')
        ProductOwnership.objects.create(customer=u, product=catalog[i % 6], purchase_date=today)
        ProductOwnership.objects.create(customer=u, product=catalog[(i + 1) % 6], purchase_date=today)
        ViewHistory.objects.create(customer=u, product=catalog[(i + 2) % 6], view_count=2)

    recommender = _build_trained_recommender()
    metrics = recommender.evaluate_ranking(k=10)

    assert metrics['eval_users'] >= 1
    assert metrics['eval_k'] == 10
    for key in ('recall_at_k', 'ndcg_at_k', 'map_at_k'):
        assert 0.0 <= metrics[key] <= 1.0


@pytest.mark.django_db
def test_evaluate_ranking_empty_when_no_eligible_users(catalog):
    """>=2 etkilesimli kullanici yoksa metrikler None ve eval_users 0 olmali."""
    today = timezone.now().date()
    # Tek etkilesimli kullanici → holdout uretilemez.
    u = User.objects.create_user(username='solo', password='X!', role='customer')
    ProductOwnership.objects.create(customer=u, product=catalog[0], purchase_date=today)

    recommender = _build_trained_recommender()
    metrics = recommender.evaluate_ranking(k=10)

    assert metrics['eval_users'] == 0
    assert metrics['recall_at_k'] is None
    assert metrics['ndcg_at_k'] is None
    assert metrics['map_at_k'] is None
