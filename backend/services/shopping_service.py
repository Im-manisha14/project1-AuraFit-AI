import os
import re
import requests
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from extensions import db
from models.outfit import Outfit

# Re-export modular retailer architecture components for backwards compatibility
from services.retailers import (
    RetailProduct,
    BaseRetailerAdapter,
    AmazonShoppingService,
    FlipkartShoppingService,
    MyntraShoppingService,
    NykaaShoppingService,
    AjioShoppingService,
    MeeshoShoppingService,
    HMShoppingService,
    ZaraShoppingService,
    MultiRetailerShoppingManager,
)

# Keywords that indicate a non-dress product — reject these
INVALID_PRODUCT_KEYWORDS = [
    'shoes', 'shoe', 'heels', 'heel', 'sneakers', 'sneaker', 'sandals', 'sandal',
    'boots', 'boot', 'flats', 'loafer', 'pump',
    'handbag', 'handbags', 'purse', 'clutch', 'wallet', 'bag',
    'jewelry', 'jewellery', 'necklace', 'earring', 'bracelet', 'ring', 'bangle', 'anklet',
    'watch', 'sunglasses', 'glasses', 'hat', 'cap', 'scarf', 'belt',
    "men's shirt", "mens shirt", "men's top", "mens top",
    "men's trousers", "men's pants", "men's jeans",
    "boy's", "boys'",
]

DRESS_KEYWORDS = ['dress', 'gown', 'maxi', 'midi', 'mini', 'kurti', 'suit', 'anarkali', 'lehenga', 'saree', 'sari', 'salwar']

OCCASION_SEARCH_MAP = {
    'casual':   'casual',
    'party':    'party',
    'work':     'office',
    'formal':   'formal',
    'date':     'date night',
    'gym':      'athleisure',
    'all':      '',
}

OCCASION_DB_MAP = {
    'casual':   'casual',
    'party':    'party',
    'work':     'work',
    'formal':   'formal',
    'date':     'date',
    'gym':      'gym',
    'all':      'casual',
    'Shopping': 'casual',
}


class LiveShoppingCache:
    """Thread-safe in-memory cache with configurable TTL (default: 15 minutes)."""
    def __init__(self, ttl_seconds: int = 900):
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        if key in self._cache:
            entry = self._cache[key]
            if (datetime.utcnow() - entry['timestamp']).total_seconds() < self.ttl:
                return entry['data']
            else:
                del self._cache[key]
        return None

    def set(self, key: str, data: List[Dict[str, Any]]):
        self._cache[key] = {
            'data': data,
            'timestamp': datetime.utcnow()
        }


# Global in-memory cache instance
_shopping_cache = LiveShoppingCache(ttl_seconds=900)


class SerpApiShoppingService:
    """
    SerpApi Google Shopping + Google Immersive Product Stores Shopping Service.
    Acts as the SINGLE SOURCE OF TRUTH for live shopping recommendations.
    """

    def __init__(self):
        self.api_key = os.environ.get('SERPAPI_KEY') or os.environ.get('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search"
        self.retailer_manager = MultiRetailerShoppingManager()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    # ------------------------------------------------------------------
    # URL Cleaning & Unwrapping
    # ------------------------------------------------------------------

    @staticmethod
    def unwrap_and_clean_url(raw_url: Optional[str]) -> Optional[str]:
        """Unwrap Google redirect wrappers (google.com/url?...) to reveal destination link."""
        if not raw_url or not isinstance(raw_url, str):
            return None
        cand = raw_url.strip()
        if 'google.com/url?' in cand:
            try:
                parsed = urllib.parse.urlparse(cand)
                qs = urllib.parse.parse_qs(parsed.query)
                target = qs.get('url', [None])[0] or qs.get('q', [None])[0]
                if target:
                    cand = urllib.parse.unquote(target).strip()
            except Exception:
                pass
        return cand

    @staticmethod
    def is_valid_direct_url(url: Optional[str]) -> bool:
        """Verify that the URL points directly to an exact retailer product page."""
        if not url or not (url.startswith('http://') or url.startswith('https://')):
            return False
        u = url.lower()
        # Reject placeholders & local test URLs
        if any(b in u for b in ['aurafit.store', 'example.com', 'localhost', '127.0.0']):
            return False
        # Reject search query URLs
        if any(sp in u for sp in [
            'amazon.in/s?', 'amazon.com/s?', 'amazon.in/s/', 'amazon.com/s/',
            '/search?', '/search/', 'rawquery=', '?q=', '&q=', 'searchterm='
        ]):
            return False
        # Reject Google Shopping search pages
        if any(gp in u for gp in ['google.com/shopping', 'google.com/search', 'google.com/url?']):
            return False
        return True

    @staticmethod
    def clean_retailer_name(source: Optional[str]) -> str:
        """Standardize retailer names according to live market brands."""
        if not source:
            return 'Online Store'
        s = source.strip()
        s_low = s.lower()
        if 'amazon' in s_low:
            return 'Amazon'
        if 'flipkart' in s_low or 'shopsy' in s_low:
            return 'Flipkart'
        if 'myntra' in s_low:
            return 'Myntra'
        if 'nykaa' in s_low:
            return 'Nykaa'
        if 'ajio' in s_low:
            return 'AJIO'
        if 'meesho' in s_low:
            return 'Meesho'
        if 'h&m' in s_low or 'hm.com' in s_low:
            return 'H&M'
        if 'zara' in s_low:
            return 'Zara'
        if 'tata cliq' in s_low or 'tatacliq' in s_low:
            return 'Tata CLiQ'
        if 'pantaloons' in s_low:
            return 'Pantaloons'
        if 'vero moda' in s_low:
            return 'Vero Moda'
        if 'newme' in s_low:
            return 'NEWME'
        if 'savana' in s_low:
            return 'Savana'
        # Strip trailing domain extensions like .com, .in, etc.
        cleaned = re.sub(r'\.(com|in|org|net|asia|store|co)$', '', s, flags=re.IGNORECASE)
        return cleaned.strip() or s

    @staticmethod
    def parse_availability(details_and_offers: List[str], delivery: Optional[str]) -> str:
        """Parse real availability from retailer details and delivery text."""
        all_text = " ".join((details_and_offers or []) + [delivery or ""]).lower()
        if any(w in all_text for w in ['out of stock', 'unavailable', 'sold out']):
            return "OUT OF STOCK"
        if any(w in all_text for w in ['limited', 'few left', 'hurry', 'only 1 left', 'only 2 left', 'only 3 left']):
            return "LIMITED"
        if any(w in all_text for w in ['in stock', 'available', 'delivery', 'ship', 'in stock online']):
            return "IN STOCK"
        return "IN STOCK"

    # ------------------------------------------------------------------
    # Query Building
    # ------------------------------------------------------------------

    def build_shopping_query(self, profile, preferences, occasion, season, compatible_colors) -> str:
        """
        Builds a human-like, high-precision shopping search query.
        Translates skin-tone recommendations into compatible clothing colors.
        e.g., 'women burgundy midi dress party summer'
        """
        parts = []
        gender = (getattr(profile, 'gender', None) or '').lower() or 'female'
        parts.append('women' if gender == 'female' else ('men' if gender == 'male' else 'women'))

        # Compatible skin-tone colors (use primary compatible color)
        if compatible_colors:
            parts.append(compatible_colors[0])

        # Style preference if specified
        if preferences and preferences.preferred_styles:
            pref = preferences.preferred_styles[0].lower()
            if pref not in ['casual', 'party', 'formal', 'all', 'none']:
                parts.append(pref)

        # Garment type
        parts.append('dress' if gender != 'male' else 'outfit')

        # Occasion term
        occ_term = OCCASION_SEARCH_MAP.get((occasion or '').lower(), '')
        if occ_term:
            parts.append(occ_term)

        # Season
        if season and season.lower() not in ['all', '']:
            parts.append(season.lower())

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Immersive Product Store Offer Resolution
    # ------------------------------------------------------------------

    def resolve_immersive_store_offer(self, item: dict) -> Optional[Dict[str, Any]]:
        """
        Calls Google Immersive Product API with more_stores=true.
        Retrieves product_results.stores[] to get the exact direct retailer link,
        exact store name, and real price.
        """
        token = item.get('immersive_product_page_token')
        imm_api = item.get('serpapi_immersive_product_api')
        if not (token or imm_api) or not self.is_configured():
            return None

        params = {
            'engine': 'google_immersive_product',
            'gl': 'in',
            'hl': 'en',
            'more_stores': 'true',
            'api_key': self.api_key
        }
        if token:
            params['page_token'] = str(token)

        endpoint = imm_api if (imm_api and not token) else self.base_url

        try:
            resp = requests.get(endpoint, params=params, timeout=8)
            if not resp.ok:
                return None

            data = resp.json()
            pr = data.get('product_results', {})
            stores = pr.get('stores', []) or data.get('sellers_results', {}).get('online_sellers', []) or data.get('stores', [])

            for s in stores:
                if not isinstance(s, dict):
                    continue
                raw_link = s.get('link') or s.get('direct_link') or s.get('product_link')
                direct_url = self.unwrap_and_clean_url(raw_link)
                if direct_url and self.is_valid_direct_url(direct_url):
                    return {
                        'store_name': s.get('name') or item.get('source'),
                        'direct_url': direct_url,
                        'title': s.get('title') or item.get('title'),
                        'price': s.get('extracted_price') or item.get('extracted_price'),
                        'price_str': s.get('price') or item.get('price'),
                        'original_price': s.get('extracted_original_price') or item.get('extracted_old_price'),
                        'details_and_offers': s.get('details_and_offers', []),
                        'shipping': s.get('shipping'),
                        'total': s.get('total')
                    }
        except Exception as e:
            print(f"[ShoppingService] Immersive resolution error: {e}")

        return None

    # ------------------------------------------------------------------
    # Fetch Live Recommendations (Primary Entry Point)
    # ------------------------------------------------------------------

    def fetch_live_recommendations(
        self,
        profile,
        preferences,
        occasion: str,
        season: str,
        compatible_colors: List[str],
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Fetches live products from SerpApi Google Shopping + Immersive Stores.
        Enforces strict exact-URL validation, real pricing, and returns standardized dicts.
        Ensures multi-retailer diversity across returned products.
        """
        if not self.is_configured():
            print("[ShoppingService] SERPAPI_KEY is not configured")
            return []

        # Check Cache
        gender = (getattr(profile, 'gender', None) or '').lower()
        skin_tone = (getattr(profile, 'skin_tone', None) or '').lower()
        primary_color = compatible_colors[0] if compatible_colors else 'default'
        cache_key = f"{gender}_{skin_tone}_{occasion}_{season}_{primary_color}"
        cached = _shopping_cache.get(cache_key)
        if cached:
            print(f"[ShoppingService] Returning {len(cached)} live products from cache ({cache_key})")
            return cached

        query = self.build_shopping_query(profile, preferences, occasion, season, compatible_colors)
        print(f"[ShoppingService] Live query: '{query}'")

        params = {
            'engine': 'google_shopping',
            'q': query,
            'gl': 'in',
            'hl': 'en',
            'api_key': self.api_key,
            'num': 35
        }

        try:
            resp = requests.get(self.base_url, params=params, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            shopping_results = data.get('shopping_results', [])
            print(f"[ShoppingService] SerpApi returned {len(shopping_results)} items for '{query}'")
        except Exception as e:
            print(f"[ShoppingService] Failed to query SerpApi: {e}")
            return []

        candidates = []
        seen_urls = set()
        seen_title_keys = set()
        retailer_candidate_counts = {}

        for it in shopping_results:
            title = (it.get('title') or '').strip()
            thumbnail = (it.get('thumbnail') or '').strip()
            price = it.get('extracted_price')

            # Basic validation
            if not title or not thumbnail or price is None:
                continue

            # Must be a dress/garment
            title_lower = title.lower()
            if not any(kw in title_lower for kw in DRESS_KEYWORDS):
                continue
            if any(kw in title_lower for kw in INVALID_PRODUCT_KEYWORDS):
                continue
            if gender == 'female' and any(kw in title_lower for kw in ["men's", "mens ", "man's", "boy's"]):
                continue

            # Image validation
            if any(bad in thumbnail.lower() for bad in ['aurafit.store', 'example.com', 'placeholder', 'unsplash']):
                continue
            if not (thumbnail.startswith('http://') or thumbnail.startswith('https://')):
                continue

            # Title key for deduplicating identical dresses across sizes/SKUs
            clean_title_words = [
                w for w in re.sub(r'[^a-zA-Z0-9\s]', '', title.lower()).split()
                if w not in ['women', 'womens', 'ladies', 'dress', 'color', 'size', 'party', 'summer', 'fit', 'flare', 'printed', 'solid']
            ]
            title_key = " ".join(clean_title_words[:3])
            if title_key and title_key in seen_title_keys:
                continue

            # Pre-filter by retailer to avoid redundant API calls
            raw_source = it.get('source') or 'Online Retailer'
            pre_retailer = self.clean_retailer_name(raw_source)
            if pre_retailer.lower() == 'aurafit official':
                continue
            if retailer_candidate_counts.get(pre_retailer, 0) >= 2:
                continue

            # Resolve exact direct retailer link via Immersive Product Stores
            store_offer = self.resolve_immersive_store_offer(it)
            direct_url = None
            final_price = float(price)
            original_price = it.get('extracted_old_price')
            details_and_offers = []

            if store_offer:
                direct_url = store_offer['direct_url']
                raw_source = store_offer['store_name']
                if store_offer.get('price'):
                    final_price = float(store_offer['price'])
                if store_offer.get('original_price'):
                    original_price = float(store_offer['original_price'])
                details_and_offers = store_offer.get('details_and_offers', [])
            else:
                # Check candidate links in top item if no immersive store
                cand = self.unwrap_and_clean_url(it.get('link') or it.get('product_link'))
                if cand and self.is_valid_direct_url(cand):
                    direct_url = cand

            # STRICT REQUIREMENT: If no exact direct retailer URL, discard!
            if not direct_url or not self.is_valid_direct_url(direct_url):
                continue
            if direct_url in seen_urls:
                continue
            seen_urls.add(direct_url)

            # Clean and validate retailer name
            retailer_name = self.clean_retailer_name(raw_source)
            if retailer_name.lower() == 'aurafit official':
                continue

            # Availability
            availability = self.parse_availability(details_and_offers, it.get('delivery'))
            if availability == "OUT OF STOCK":
                continue

            # Discount calculation
            discount_str = None
            if original_price and original_price > final_price:
                discount_pct = round((1 - (final_price / original_price)) * 100)
                if discount_pct > 0:
                    discount_str = f"{discount_pct}% OFF"

            # Stable external ID
            raw_id = str(it.get('product_id') or it.get('id') or it.get('title')[:30])
            ext_id = f"serpapi_{raw_id}"

            # Brand detection
            brand = it.get('brand') or retailer_name

            if title_key:
                seen_title_keys.add(title_key)
            retailer_candidate_counts[retailer_name] = retailer_candidate_counts.get(retailer_name, 0) + 1

            candidates.append({
                'it': it,
                'title': title,
                'title_key': title_key,
                'thumbnail': thumbnail,
                'retailer_name': retailer_name,
                'brand': brand,
                'final_price': final_price,
                'original_price': original_price,
                'discount_str': discount_str,
                'availability': availability,
                'direct_url': direct_url,
                'ext_id': ext_id
            })

            # Check if we have enough diverse candidates
            if len(candidates) >= limit and len(retailer_candidate_counts) >= 3:
                break

        # Multi-retailer diversification:
        # Pass 1: Select up to 2 items per retailer, deduplicating identical dress titles
        selected_candidates = []
        seen_title_keys = set()
        retailer_counts = {}

        for c in candidates:
            r = c['retailer_name']
            tk = c['title_key']
            if tk and tk in seen_title_keys:
                continue
            if retailer_counts.get(r, 0) >= 2:
                continue
            selected_candidates.append(c)
            if tk:
                seen_title_keys.add(tk)
            retailer_counts[r] = retailer_counts.get(r, 0) + 1
            if len(selected_candidates) >= limit:
                break

        # Pass 2: Backfill from remaining valid candidates if below limit
        if len(selected_candidates) < limit:
            for c in candidates:
                if c in selected_candidates:
                    continue
                selected_candidates.append(c)
                if len(selected_candidates) >= limit:
                    break

        live_products = []
        for c in selected_candidates:
            it = c['it']
            title = c['title']
            thumbnail = c['thumbnail']
            retailer_name = c['retailer_name']
            brand = c['brand']
            final_price = c['final_price']
            original_price = c['original_price']
            discount_str = c['discount_str']
            availability = c['availability']
            direct_url = c['direct_url']
            ext_id = c['ext_id']

            # Persist to database so OutfitDetail.js can load it by ID
            outfit_record = self._persist_live_outfit(
                external_id=ext_id,
                title=title,
                brand=brand,
                retailer=retailer_name,
                image_url=thumbnail,
                price=final_price,
                original_price=original_price,
                discount=discount_str,
                product_url=direct_url,
                gender=gender,
                occasion=OCCASION_DB_MAP.get(occasion.lower(), 'casual'),
                season=season if season != 'all' else 'all',
                colors=compatible_colors[:3] if compatible_colors else ['burgundy', 'pink']
            )

            # Build exact standard object per Requirement 17
            product_dict = {
                'id': outfit_record.id if outfit_record else None,
                'external_id': ext_id,
                'title': title,
                'name': title,
                'brand': brand,
                'retailer': retailer_name,
                'store': retailer_name,
                'image_url': thumbnail,
                'additional_images': it.get('thumbnails', []),
                'price': final_price,
                'currency': 'INR',
                'original_price': original_price,
                'discount': discount_str,
                'availability': availability,
                'product_url': direct_url,
                'shopping_url': direct_url,
                'source': 'serpapi',
                'is_live': True,
                'is_purchasable': True,
                'in_stock': True,
                'exact_product_link_available': True,
                'gender': gender,
                'occasion': occasion,
                'season': season,
                'style_type': preferences.preferred_styles[0] if (preferences and preferences.preferred_styles) else 'casual',
                'colors': compatible_colors[:3] if compatible_colors else ['burgundy'],
                'description': f"Live {retailer_name} dress curated for {occasion} wear.",
                'shopping_links': { retailer_name.lower().replace(' ', ''): direct_url }
            }

            live_products.append(product_dict)

        print(f"[ShoppingService] Resolved {len(live_products)} live diverse purchasable products with direct URLs")
        if live_products:
            _shopping_cache.set(cache_key, live_products)

        return live_products

    # ------------------------------------------------------------------
    # Similar Recommendations Query
    # ------------------------------------------------------------------

    def fetch_similar_live_products(self, main_product: Dict[str, Any], profile, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Generates a second live shopping query based on the main recommended item
        (same category, compatible color, occasion) and returns real SerpApi products.
        """
        if not self.is_configured():
            return []

        color = (main_product.get('colors') or ['burgundy'])[0]
        occasion = main_product.get('occasion') or 'party'
        gender = main_product.get('gender') or 'female'

        cache_key = f"similar_{gender}_{color}_{occasion}"
        cached = _shopping_cache.get(cache_key)
        if cached:
            return cached

        # Similar query: e.g. "women olive green wrap party dress"
        similar_query = f"{'women' if gender == 'female' else 'men'} {color} wrap {occasion} dress"
        print(f"[ShoppingService] Similar live query: '{similar_query}'")

        params = {
            'engine': 'google_shopping',
            'q': similar_query,
            'gl': 'in',
            'hl': 'en',
            'api_key': self.api_key,
            'num': 20
        }

        try:
            resp = requests.get(self.base_url, params=params, timeout=10)
            if not resp.ok:
                return []
            results = resp.json().get('shopping_results', [])
        except Exception:
            return []

        similar_items = []
        seen_sim_urls = set()
        seen_sim_retailers = {}

        for it in results:
            title = (it.get('title') or '').strip()
            thumbnail = (it.get('thumbnail') or '').strip()
            price = it.get('extracted_price')
            if not title or not thumbnail or price is None:
                continue
            if it.get('product_id') == main_product.get('external_id'):
                continue

            pre_retailer = self.clean_retailer_name(it.get('source'))
            if seen_sim_retailers.get(pre_retailer, 0) >= 2:
                continue

            store_offer = self.resolve_immersive_store_offer(it)
            direct_url = None
            raw_source = it.get('source') or 'Online Store'
            final_price = float(price)
            original_price = it.get('extracted_old_price')

            if store_offer:
                direct_url = store_offer['direct_url']
                raw_source = store_offer['store_name']
                if store_offer.get('price'):
                    final_price = float(store_offer['price'])
                if store_offer.get('original_price'):
                    original_price = float(store_offer['original_price'])
            else:
                cand = self.unwrap_and_clean_url(it.get('link') or it.get('product_link'))
                if cand and self.is_valid_direct_url(cand):
                    direct_url = cand

            if not direct_url or not self.is_valid_direct_url(direct_url):
                continue
            if direct_url in seen_sim_urls:
                continue
            seen_sim_urls.add(direct_url)

            retailer_name = self.clean_retailer_name(raw_source)
            if seen_sim_retailers.get(retailer_name, 0) >= 2:
                continue
            seen_sim_retailers[retailer_name] = seen_sim_retailers.get(retailer_name, 0) + 1

            discount_str = None
            if original_price and original_price > final_price:
                discount_pct = round((1 - (final_price / original_price)) * 100)
                if discount_pct > 0:
                    discount_str = f"{discount_pct}% OFF"

            sim_ext_id = f"serpapi_sim_{it.get('product_id') or len(similar_items)}"
            outfit_record = self._persist_live_outfit(
                external_id=sim_ext_id,
                title=title,
                brand=it.get('brand') or retailer_name,
                retailer=retailer_name,
                image_url=thumbnail,
                price=final_price,
                original_price=original_price,
                discount=discount_str,
                product_url=direct_url,
                gender=gender,
                occasion=OCCASION_DB_MAP.get(occasion.lower(), 'casual'),
                season='all',
                colors=[color]
            )

            similar_items.append({
                'id': outfit_record.id if outfit_record else None,
                'external_id': sim_ext_id,
                'title': title,
                'name': title,
                'brand': it.get('brand') or retailer_name,
                'retailer': retailer_name,
                'store': retailer_name,
                'image_url': thumbnail,
                'price': final_price,
                'currency': 'INR',
                'original_price': original_price,
                'discount': discount_str,
                'product_url': direct_url,
                'shopping_url': direct_url,
                'source': 'serpapi',
                'is_live': True,
                'is_purchasable': True,
                'in_stock': True,
                'exact_product_link_available': True
            })

            if len(similar_items) >= limit:
                break

        if similar_items:
            _shopping_cache.set(cache_key, similar_items)

        return similar_items

    # ------------------------------------------------------------------
    # Database Persistence Helper
    # ------------------------------------------------------------------

    def _persist_live_outfit(
        self,
        external_id: str,
        title: str,
        brand: str,
        retailer: str,
        image_url: str,
        price: float,
        product_url: str,
        gender: str,
        occasion: str,
        season: str,
        colors: List[str],
        original_price: Optional[float] = None,
        discount: Optional[str] = None
    ) -> Optional[Outfit]:
        """Upsert a live product into the Outfit table so detail routes can load it."""
        try:
            existing = Outfit.query.filter_by(external_id=external_id).first()
            if existing:
                existing.price = price
                existing.original_price = original_price
                existing.discount = discount
                existing.in_stock = True
                existing.purchasable = True
                existing.product_url = product_url
                existing.image_url = image_url
                existing.brand = brand
                existing.store = retailer
                db.session.commit()
                return existing

            new_outfit = Outfit(
                external_id=external_id,
                name=title,
                description=f"Curated live from {retailer}.",
                category='dress',
                gender=gender,
                colors=colors,
                image_url=image_url,
                price=price,
                original_price=original_price,
                discount=discount,
                currency='INR',
                brand=brand,
                store=retailer,
                product_url=product_url,
                in_stock=True,
                purchasable=True,
                source='serpapi',
                occasion=occasion,
                season=season,
                style_type='casual',
                comfort_score=4.5,
                body_type_compatibility=['all']
            )
            db.session.add(new_outfit)
            db.session.commit()
            return new_outfit
        except Exception as e:
            db.session.rollback()
            print(f"[ShoppingService] DB save error for {external_id}: {e}")
            return None
