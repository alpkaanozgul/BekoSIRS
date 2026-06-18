"""
Matrix Factorization (TruncatedSVD, Netflix tarzi CF) birim testleri.

MatrixFactorizationModel; implicit etkilesim matrisini latent faktorlere ayirmali,
faktor boyutlari tutarli olmali, egitimde gorulmemis kullaniciya bos donmeli,
diske kaydedip yukleyince ayni skorlari uretmeli ve veri yetersizse zarif
sekilde False donmeli. Ayrica eski MLPRegressor pickle'inin yol actigi yukleme
kirilganligini gidermek icin save/load duz numpy dizileriyle calismali.
"""

from decimal import Decimal

import numpy as np
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from products.ml_recommender import MatrixFactorizationModel, NCFModel
from products.models import Category, Product, ProductOwnership, ViewHistory

User = get_user_model()


@pytest.fixture
def catalog(db):
    category = Category.objects.create(name='MF Category')
    products = [
        Product.objects.create(
            name=f'MF Product {i}', brand='Beko', category=category,
            price=Decimal('5000.00'), stock=10,
        )
        for i in range(5)
    ]
    return products


def _seed_interactions(products):
    """Bes kullanici, ortusen satin alma/goruntuleme desenleriyle matris kurar."""
    today = timezone.now().date()
    users = [
        User.objects.create_user(username=f'mf-{i}', password='X!', role='customer')
        for i in range(5)
    ]
    # Kullanici i, urun i ve i+1'i alir → user/item faktorlerinde yapi olusur.
    for i, u in enumerate(users):
        ProductOwnership.objects.create(customer=u, product=products[i], purchase_date=today)
        ProductOwnership.objects.create(
            customer=u, product=products[(i + 1) % len(products)], purchase_date=today,
        )
        ViewHistory.objects.create(customer=u, product=products[i], view_count=3)
    return users


@pytest.mark.django_db
def test_train_builds_consistent_factors(catalog):
    """user_factors ve item_factors ayni latent boyutta (k) olmali."""
    users = _seed_interactions(catalog)
    model = MatrixFactorizationModel()
    assert model.train(verbose=False) is True

    k = model.training_metrics['n_components']
    assert model.user_factors.shape[0] == len(users)
    assert model.user_factors.shape[1] == k
    assert model.item_factors.shape[1] == k
    assert model.item_factors.shape[0] == len(model.item_ids)
    assert 0.0 <= model.training_metrics['explained_variance'] <= 1.0 + 1e-9


@pytest.mark.django_db
def test_predict_returns_scores_for_known_user(catalog):
    """Egitimde yer alan kullanici icin pozitif skorlu aday sozlugu donmeli."""
    users = _seed_interactions(catalog)
    model = MatrixFactorizationModel()
    model.train(verbose=False)

    all_ids = [p.id for p in catalog]
    scores = model.predict_for_user(users[0].id, all_ids)
    assert isinstance(scores, dict)
    assert all(v > 0 for v in scores.values())
    # Istenen urun kumesi disina cikmamali.
    assert set(scores.keys()).issubset(set(all_ids))


@pytest.mark.django_db
def test_unknown_user_returns_empty(catalog):
    """Egitimde gorulmemis kullanici (cold-start) bos sozluk almali."""
    _seed_interactions(catalog)
    model = MatrixFactorizationModel()
    model.train(verbose=False)

    stranger = User.objects.create_user(username='stranger', password='X!', role='customer')
    assert model.predict_for_user(stranger.id, [p.id for p in catalog]) == {}


@pytest.mark.django_db
def test_persistence_round_trip(catalog, tmp_path):
    """Kaydet → yukle sonrasi ayni kullanici icin skorlar degismeden gelmeli."""
    users = _seed_interactions(catalog)
    model = MatrixFactorizationModel()
    model.train(verbose=False)
    all_ids = [p.id for p in catalog]
    before = model.predict_for_user(users[0].id, all_ids)

    path = tmp_path / 'mf.pkl'
    model.save(path=str(path))

    reloaded = MatrixFactorizationModel()
    assert reloaded.load(path=str(path)) is True
    after = reloaded.predict_for_user(users[0].id, all_ids)

    assert before.keys() == after.keys()
    for pid in before:
        assert before[pid] == pytest.approx(after[pid], rel=1e-9, abs=1e-9)


@pytest.mark.django_db
def test_train_returns_false_without_data(db):
    """5'ten az etkilesimde egitim zarifce False donmeli."""
    model = MatrixFactorizationModel()
    assert model.train(verbose=False) is False
    assert model.is_trained is False


@pytest.mark.django_db
def test_ncf_alias_points_to_mf():
    """Geriye donuk uyumluluk: NCFModel artik MatrixFactorizationModel olmali."""
    assert NCFModel is MatrixFactorizationModel
