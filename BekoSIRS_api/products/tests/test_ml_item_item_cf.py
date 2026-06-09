"""
Item-Item Collaborative Filtering (Amazon tarzi) birim testleri.

ItemItemCFModel; kullanici sepetlerinden urun-urun kosinus benzerligi kurmali,
benzerlik matrisi simetrik ve [0, 1] araliginda olmali, bilinen sepetlerde
beklenen komsuyu uretmeli ve diske kaydedip geri yukleyince ayni skorlari vermeli.
"""

from decimal import Decimal

import numpy as np
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from products.ml_recommender import ItemItemCFModel
from products.models import Category, Product, ProductOwnership

User = get_user_model()


@pytest.fixture
def category(db):
    return Category.objects.create(name='Item-CF Category')


@pytest.fixture
def products(db, category):
    """Dort urun: A-B birlikte alinir, C-D nadiren."""
    make = lambda name, price: Product.objects.create(
        name=name, brand='Beko', category=category,
        price=Decimal(price), stock=10,
    )
    return (
        make('Product A', '10000.00'),
        make('Product B', '8000.00'),
        make('Product C', '6000.00'),
        make('Product D', '4000.00'),
    )


def _buy(user, product):
    ProductOwnership.objects.create(
        customer=user, product=product, purchase_date=timezone.now().date(),
    )


@pytest.mark.django_db
def test_train_builds_symmetric_normalized_matrix(products):
    """Benzerlik matrisi simetrik ve kosinus oldugu icin [0, 1] araliginda olmali."""
    a, b, c, d = products
    # Uc kullanici A+B alir → A ile B guclu komsu; bir kullanici C+D alir.
    for i in range(3):
        u = User.objects.create_user(username=f'ab-{i}', password='X!', role='customer')
        _buy(u, a)
        _buy(u, b)
    u_cd = User.objects.create_user(username='cd', password='X!', role='customer')
    _buy(u_cd, c)
    _buy(u_cd, d)

    model = ItemItemCFModel()
    assert model.train(verbose=False) is True

    sim = model.sim_matrix
    # Simetri
    assert np.allclose(sim, sim.T)
    # Kosinus benzerligi negatif olmayan agirliklarda [0, 1]
    assert sim.min() >= -1e-9
    assert sim.max() <= 1.0 + 1e-9
    # Kosegen sifirlanmis olmali (urun kendi komsusu degil)
    assert np.allclose(np.diag(sim), 0.0)


@pytest.mark.django_db
def test_cooccurring_returns_expected_neighbor(products):
    """A+B birlikte alindiginda A'nin en guclu komsusu B olmali."""
    a, b, c, d = products
    for i in range(3):
        u = User.objects.create_user(username=f'ab-{i}', password='X!', role='customer')
        _buy(u, a)
        _buy(u, b)
    # C'yi alan tek kullanici A da alir ama daha zayif sinyal.
    u_ac = User.objects.create_user(username='ac', password='X!', role='customer')
    _buy(u_ac, a)
    _buy(u_ac, c)

    model = ItemItemCFModel()
    model.train(verbose=False)

    neighbors = model.get_cooccurring(a.id, top_n=3)
    assert neighbors, 'komsu listesi bos olmamali'
    # En guclu komsu B (3 ortak alici) olmali.
    assert neighbors[0][0] == b.id
    # Anchor kendi listesinde olmamali.
    assert a.id not in [pid for pid, _ in neighbors]


@pytest.mark.django_db
def test_cooccurring_excludes_given_ids(products):
    """exclude_ids ile verilen urunler komsu listesinde gozukmemeli."""
    a, b, c, _d = products
    u = User.objects.create_user(username='abc', password='X!', role='customer')
    _buy(u, a)
    _buy(u, b)
    _buy(u, c)

    model = ItemItemCFModel()
    model.train(verbose=False)

    neighbors = model.get_cooccurring(a.id, top_n=5, exclude_ids={b.id})
    pids = [pid for pid, _ in neighbors]
    assert b.id not in pids
    assert c.id in pids


@pytest.mark.django_db
def test_user_itemcf_scores_accumulate(products):
    """Kullanici birden cok tohum urune sahipse skorlar toplanmali."""
    a, b, c, d = products
    # A-B ve A-C birliktelik sinyali kur.
    for i in range(2):
        u = User.objects.create_user(username=f'ab-{i}', password='X!', role='customer')
        _buy(u, a)
        _buy(u, b)
    u_ac = User.objects.create_user(username='ac', password='X!', role='customer')
    _buy(u_ac, a)
    _buy(u_ac, c)

    model = ItemItemCFModel()
    model.train(verbose=False)

    # Kullanici A'ya bakmis; aday skorlarinda B ve C pozitif olmali, A exclude.
    scores = model.get_user_itemcf_scores({a.id: 5.0}, exclude_ids={a.id})
    assert a.id not in scores
    assert scores.get(b.id, 0) > 0
    assert scores.get(c.id, 0) > 0


@pytest.mark.django_db
def test_persistence_round_trip(products, tmp_path):
    """Kaydet → yukle sonrasi benzerlik matrisi ayni kalmali (surum-bagimsiz pickle)."""
    a, b, _c, _d = products
    u = User.objects.create_user(username='rt', password='X!', role='customer')
    _buy(u, a)
    _buy(u, b)

    model = ItemItemCFModel()
    model.train(verbose=False)
    path = tmp_path / 'itemitem.pkl'
    # _save_model_to_db DB'ye yazmaya calisip sessizce gecer; round-trip diske dayali.
    model.save(path=str(path))

    reloaded = ItemItemCFModel()
    assert reloaded.load(path=str(path)) is True
    assert np.allclose(reloaded.sim_matrix, model.sim_matrix)
    assert reloaded.item_ids == model.item_ids


@pytest.mark.django_db
def test_train_returns_false_without_data(db):
    """Hic etkilesim yoksa egitim zarifce False donmeli."""
    model = ItemItemCFModel()
    assert model.train(verbose=False) is False
    assert model.is_trained is False
