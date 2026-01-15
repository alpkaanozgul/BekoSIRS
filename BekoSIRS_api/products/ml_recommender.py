# products/ml_recommender.py
"""
Hybrid Recommender System with performance optimizations.
Uses singleton pattern and lazy loading for efficient operation.
"""
import pandas as pd
import numpy as np
import threading
import time
from functools import lru_cache
from django.core.cache import cache
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD


class HybridRecommender:
    """
    Singleton recommender with lazy loading and caching.
    
    Performance optimizations:
    - Singleton pattern: Only one instance across the application
    - Lazy loading: Models only trained on first recommendation request
    - Caching: Similarity matrix and user interactions cached
    """
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    # Cache keys
    CACHE_KEY_SIMILARITY = 'ml_similarity_matrix'
    CACHE_KEY_PRODUCTS = 'ml_products_df'
    CACHE_TTL = getattr(settings, 'CACHE_TTL_LONG', 7200)  # 2 hours default
    
    def __new__(cls):
        """Singleton pattern - only create one instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize with lazy loading - don't train models yet."""
        if HybridRecommender._initialized:
            return
            
        self.products_df = None
        self.similarity_matrix = None
        self.user_product_matrix = None
        self.svd_model = None
        self.indices = None
        self._last_trained = None
        
        HybridRecommender._initialized = True

    def _ensure_trained(self):
        """Lazy loading - train models only when needed."""
        # Check if we need to retrain (cache expired or never trained)
        if self.similarity_matrix is not None:
            return
            
        # Try to load from cache first
        cached_similarity = cache.get(self.CACHE_KEY_SIMILARITY)
        cached_products = cache.get(self.CACHE_KEY_PRODUCTS)
        
        if cached_similarity is not None and cached_products is not None:
            self.similarity_matrix = cached_similarity
            self.products_df = cached_products
            if not self.products_df.empty:
                self.indices = pd.Series(
                    self.products_df.index, 
                    index=self.products_df['id']
                ).drop_duplicates()
            return
        
        # Train models if cache miss
        self._load_data()
        self._train_content_model()
        self._train_collaborative_model()
        
        # Cache the results
        if self.similarity_matrix is not None:
            cache.set(self.CACHE_KEY_SIMILARITY, self.similarity_matrix, self.CACHE_TTL)
        if self.products_df is not None:
            cache.set(self.CACHE_KEY_PRODUCTS, self.products_df, self.CACHE_TTL)
        
        self._last_trained = time.time()

    def _load_data(self):
        """Fetches all products from DB into a DataFrame."""
        from .models import Product  # Import here to avoid circular imports
        
        products = Product.objects.all().values(
            'id', 'name', 'description', 'brand', 'category__name', 'price'
        )
        self.products_df = pd.DataFrame(list(products))
        
        if not self.products_df.empty:
            self.indices = pd.Series(
                self.products_df.index, 
                index=self.products_df['id']
            ).drop_duplicates()

    def _train_content_model(self):
        """Builds Content-Based logic using TF-IDF."""
        if self.products_df is None or self.products_df.empty:
            return

        # Combine text fields
        self.products_df['content'] = (
            self.products_df['name'] + " " + 
            self.products_df['description'].fillna('') + " " + 
            self.products_df['brand'].fillna('') + " " + 
            self.products_df['category__name'].fillna('')
        )

        # Create Vectors
        tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        tfidf_matrix = tfidf.fit_transform(self.products_df['content'])

        # Calculate Similarity
        self.similarity_matrix = cosine_similarity(tfidf_matrix)

    def _train_collaborative_model(self):
        """Builds Collaborative Filtering logic using SVD."""
        from .models import ViewHistory, WishlistItem, Review, ProductOwnership
        
        # 1. Fetch all interactions
        views = pd.DataFrame(list(
            ViewHistory.objects.all().values('customer_id', 'product_id', 'view_count')
        ))
        wishlist = pd.DataFrame(list(
            WishlistItem.objects.filter(wishlist__customer__isnull=False)
            .values('wishlist__customer_id', 'product_id')
        ))
        reviews = pd.DataFrame(list(
            Review.objects.all().values('customer_id', 'product_id', 'rating')
        ))
        purchases = pd.DataFrame(list(
            ProductOwnership.objects.all().values('customer_id', 'product_id')
        ))

        # 2. Assign Weights
        interactions = []

        if not views.empty:
            views['score'] = views['view_count'].apply(lambda x: min(x, 5) * 1.0)
            interactions.append(views[['customer_id', 'product_id', 'score']])

        if not wishlist.empty:
            wishlist = wishlist.rename(columns={'wishlist__customer_id': 'customer_id'})
            wishlist['score'] = 3.0
            interactions.append(wishlist)

        if not reviews.empty:
            reviews = reviews.rename(columns={'rating': 'score'})
            interactions.append(reviews)

        if not purchases.empty:
            purchases['score'] = 5.0
            interactions.append(purchases)

        # 3. Create the Matrix
        if not interactions:
            self.user_product_matrix = None
            return

        all_interactions = pd.concat(interactions)
        self.user_product_matrix = all_interactions.groupby(
            ['customer_id', 'product_id']
        )['score'].sum().unstack(fill_value=0)

        # 4. Apply SVD
        if (self.user_product_matrix.shape[0] > 5 and 
            self.user_product_matrix.shape[1] > 5):
            n_components = min(12, min(self.user_product_matrix.shape) - 1)
            self.svd_model = TruncatedSVD(n_components=n_components, random_state=42)
            self.svd_matrix = self.svd_model.fit_transform(self.user_product_matrix)
            self.corr_matrix = np.corrcoef(self.svd_matrix)

    def recommend(self, user, top_n=5, ignore_cache=False, exclude_ids=None):
        """Main function to get hybrid recommendations."""
        self._ensure_trained()
        
        if self.products_df is None or self.products_df.empty:
            return []

        # 1. Content-Based Scores
        content_results = self._recommend_content_based(user, limit=None, ignore_cache=ignore_cache) 
        
        # 2. Collaborative Scores
        collab_results = self._recommend_collaborative(user)
        
        # 3. Hybrid Merge (Weighted)
        final_scores = {}
        reasons = {}

        # Normalize and merge Content scores
        max_content = max(content_results.values()) if content_results else 1.0
        for pid, score in content_results.items():
            final_scores[pid] = (score / max_content) * 0.7
            if score > 0:
                reasons[pid] = "İlgi alanlarınıza göre"
            
        # Normalize and merge Collab scores
        max_collab = max(collab_results.values()) if collab_results else 1.0
        for pid, score in collab_results.items():
            normalized = (score / max_collab) * 0.3
            if pid in final_scores:
                final_scores[pid] += normalized
                # If collab score is high, it might override the reason
                if normalized > final_scores[pid] * 0.4:
                    reasons[pid] = "Benzer kullanıcılar tercih etti"
            else:
                final_scores[pid] = normalized
                reasons[pid] = "Benzer kullanıcılar tercih etti"

        # 4. Search History Boost
        search_boosts = self._get_search_boosts(user)
        for pid, boost in search_boosts.items():
            final_scores[pid] = final_scores.get(pid, 0) + boost
            reasons[pid] = "Aramalarınıza göre"

        # 5. Price Sensitivity Boost
        price_boosts = self._get_price_sensitivity_boosts(user)
        for pid, boost in price_boosts.items():
            if pid in final_scores:
                final_scores[pid] += boost
                # Only change reason if this wasn't a search result
                if reasons.get(pid) != "Aramalarınıza göre" and boost > 0.1:
                    reasons[pid] = "Fiyat tercihlerinize uygun"

        # Sort and Format
        return self._format_final_results(final_scores, reasons, top_n, exclude_ids)

    def _recommend_content_based(self, user, limit=None, ignore_cache=False):
        """Return raw dictionary {product_id: score}."""
        user_interests = self._get_user_interactions_dict(user, ignore_cache)
        if not user_interests:
            return {}

        scores = {}
        # Calculate score for every product based on similarity to liked items
        for product_id, weight in user_interests.items():
            if product_id not in self.indices:
                continue
            idx = self.indices[product_id]
            
            # Get similarity scores for this product against all others
            sim_scores = self.similarity_matrix[idx]
            
            # Add weighted similarity to total score
            for i, score in enumerate(sim_scores):
                if score > 0.1: # Filter low relevance
                    pid = self.products_df.iloc[i]['id']
                    scores[pid] = scores.get(pid, 0) + (score * weight)
                    
        return scores

    def _recommend_collaborative(self, user):
        """Return raw dictionary {product_id: score} using SVD."""
        if self.svd_model is None or self.user_product_matrix is None:
            return {}
            
        user_id = user.id
        if user_id not in self.user_product_matrix.index:
            return {} # Cold start user
            
        # Get user's current vector in interaction matrix
        user_idx = self.user_product_matrix.index.get_loc(user_id)
        user_vector = self.user_product_matrix.iloc[user_idx].values.reshape(1, -1)
        
        # Transform to SVD space
        user_svd = self.svd_model.transform(user_vector)
        
        # Reconstruct (predict) ratings
        predicted_ratings = self.svd_model.inverse_transform(user_svd)[0]
        
        # Map back to product IDs
        scores = {}
        for i, score in enumerate(predicted_ratings):
            pid = self.user_product_matrix.columns[i]
            scores[pid] = score
            
        return scores

    def _format_final_results(self, scores_dict, reasons_dict, top_n, exclude_ids=None):
        from .models import Product
        
        # Exclude IDs
        if exclude_ids:
            for pid in exclude_ids:
                if pid in scores_dict:
                    del scores_dict[pid]
        
        # Sort by score descending
        sorted_items = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        results = []
        for pid, score in sorted_items:
            try:
                obj = Product.objects.get(id=pid)
                results.append({
                    'product': obj, 
                    'product_id': pid,
                    'score': score,
                    'reason': reasons_dict.get(pid, 'Sizin için seçildi')
                })
            except Product.DoesNotExist:
                continue
        return results

    def _get_search_boosts(self, user):
        """Boost products based on search history text matching."""
        from .models import SearchHistory
        
        boosts = {}
        if self.products_df is None or self.products_df.empty:
            return boosts
            
        recent_searches = SearchHistory.objects.filter(customer=user).order_by('-created_at')[:5]
        if not recent_searches:
            return boosts
            
        # Compile search terms
        search_terms = [s.query.lower() for s in recent_searches]
        
        # Simple text matching (could be improved with TF-IDF again but this is faster)
        # Note: products_df already has 'content' column from _train_content_model
        if 'content' not in self.products_df.columns:
             self.products_df['content'] = (
                self.products_df['name'] + " " + 
                self.products_df['description'].fillna('') + " " + 
                self.products_df['brand'].fillna('') + " " + 
                self.products_df['category__name'].fillna('')
            ).str.lower()
            
        for index, row in self.products_df.iterrows():
            pid = row['id']
            content = str(row['content']).lower()
            
            score = 0
            for term in search_terms:
                if term in content:
                    score += 2.0  # Significant boost for search match
            
            if score > 0:
                boosts[pid] = score
                
        return boosts

    def _get_price_sensitivity_boosts(self, user):
        """Boost products that match the user's usual price range."""
        from .models import ProductOwnership, ViewHistory
        
        boosts = {}
        prices = []
        
        # Collect prices from purchases and views
        owned = ProductOwnership.objects.filter(customer=user).values_list('product__price', flat=True)
        viewed = ViewHistory.objects.filter(customer=user).values_list('product__price', flat=True)[:10]
        
        prices.extend([float(p) for p in owned if p])
        prices.extend([float(p) for p in viewed if p])
        
        if not prices:
            return boosts
            
        avg_price = sum(prices) / len(prices)
        price_range_min = avg_price * 0.7
        price_range_max = avg_price * 1.3
        
        # We need product prices. Products_df might not have it loaded by default logic.
        if 'price' in self.products_df.columns:
             for index, row in self.products_df.iterrows():
                try:
                    p_price = float(row['price']) if row['price'] else 0
                    if price_range_min <= p_price <= price_range_max:
                        boosts[row['id']] = 0.5 # Moderate boost
                except:
                    pass
                    
        return boosts

    def _get_user_interactions_dict(self, user, ignore_cache=False):
        """Gather raw interest scores for a single user with caching."""
        from .models import ProductOwnership, Review, WishlistItem, ViewHistory
        
        # Check user-specific cache
        cache_key = f'user_interactions_{user.id}'
        
        if not ignore_cache:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        
        interactions = {}

        # 1. Purchases (Strong Base Interest: 5.0)
        for pid in ProductOwnership.objects.filter(customer=user).values_list('product_id', flat=True):
            interactions[pid] = interactions.get(pid, 0) + 5.0

        # 2. Reviews > 3 (High Satisfaction: 4.0)
        for pid in Review.objects.filter(customer=user, rating__gt=3).values_list('product_id', flat=True):
            interactions[pid] = interactions.get(pid, 0) + 4.0

        # 3. Wishlist (Intent to Buy: 3.0)
        for pid in WishlistItem.objects.filter(wishlist__customer=user).values_list('product_id', flat=True):
            interactions[pid] = interactions.get(pid, 0) + 3.0

        # 4. Recency Boost - Most recent views get highest scores
        recent_views = ViewHistory.objects.filter(customer=user).order_by('-viewed_at')[:10]
        for i, v in enumerate(recent_views):
            recency_bonus = 10 - i
            interactions[v.product_id] = interactions.get(v.product_id, 0) + recency_bonus

        # Cache for 5 minutes
        cache.set(cache_key, interactions, 300)
        
        return interactions

    def _format_results(self, scores, exclude_ids, top_n):
        """Format and return top N product recommendations."""
        from .models import Product
        
        # Zero out already seen products
        for pid in exclude_ids:
            if pid in self.indices:
                scores[self.indices[pid]] = 0

        # Get top indices sorted by score
        top_indices = scores.argsort()[::-1][:top_n]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                prod_id = self.products_df.iloc[idx]['id']
                try:
                    obj = Product.objects.get(id=prod_id)
                    results.append({'product': obj, 'score': scores[idx]})
                except Product.DoesNotExist:
                    continue
        return results

    def invalidate_cache(self):
        """Invalidate all cached data - call when products change."""
        cache.delete(self.CACHE_KEY_SIMILARITY)
        cache.delete(self.CACHE_KEY_PRODUCTS)
        self.similarity_matrix = None
        self.products_df = None
        self._last_trained = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        return cls()


# Alias for backward compatibility
ContentBasedRecommender = HybridRecommender


def get_recommender():
    """Factory function to get the singleton recommender instance."""
    return HybridRecommender.get_instance()