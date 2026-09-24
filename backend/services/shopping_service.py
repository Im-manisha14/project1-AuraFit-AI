import os
import requests
from datetime import datetime
from extensions import db
from models.outfit import Outfit

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

# Words that MUST appear in the title for women's wear
DRESS_KEYWORDS = ['dress', 'gown', 'maxi', 'midi', 'mini', 'kurti', 'suit', 'anarkali', 'lehenga', 'saree', 'sari', 'salwar']

# Occasion → search-friendly term
OCCASION_SEARCH_MAP = {
    'casual':   'casual',
    'party':    'party',
    'work':     'office',
    'formal':   'formal',
    'date':     'date night',
    'gym':      'athleisure',
    'all':      '',
}

# Occasion → DB occasion value (what to store so the engine can find it)
OCCASION_DB_MAP = {
    'casual':   'casual',
    'party':    'party',
    'work':     'work',
    'formal':   'formal',
    'date':     'date',
    'gym':      'gym',
    'all':      'casual',   # Default to casual when 'all'
    'Shopping': 'casual',   # Normalise legacy 'Shopping' entries
}


class SerpApiShoppingService:
    def __init__(self):
        self.api_key = os.environ.get('SERPAPI_KEY') or os.environ.get('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search"

    def is_configured(self) -> bool:
        configured = bool(self.api_key)
        if not configured:
            print("[ShoppingService] SERPAPI_KEY is not configured")
        return configured

    # ------------------------------------------------------------------
    # Query building
    # ------------------------------------------------------------------

    def _build_search_query(self, profile, preferences, occasion, compatible_colors) -> str:
        """
        Build a specific, human-readable Google Shopping search query.
        e.g. "women burgundy midi dress casual"
        """
        parts = []

        # 1. Gender
        gender = (getattr(profile, 'gender', None) or '').lower()
        if gender == 'female':
            parts.append('women')
        elif gender == 'male':
            parts.append('men')
        else:
            parts.append('women')          # default to women's dresses

        # 2. Color — use skin-tone compatible colors
        if compatible_colors:
            # Pick the first 2 for variety without making the query too long
            parts.extend(compatible_colors[:2])

        # 3. Garment category
        if gender == 'male':
            parts.append('outfit')
        else:
            parts.append('dress')

        # 4. Occasion context
        occasion_term = OCCASION_SEARCH_MAP.get((occasion or '').lower(), '')
        if occasion_term:
            parts.append(occasion_term)

        # 5. Style preference (first one only)
        if preferences and getattr(preferences, 'preferred_styles', None):
            style = preferences.preferred_styles[0]
            if style and style.lower() not in parts:
                parts.append(style)

        return ' '.join(parts)

    def _build_multiple_queries(self, profile, preferences, occasion, compatible_colors) -> list:
        """
        Return a small set of varied queries so we get diverse results.
        """
        gender = (getattr(profile, 'gender', None) or '').lower() or 'female'
        gender_word = 'women' if gender == 'female' else ('men' if gender == 'male' else 'women')
        garment = 'dress' if gender != 'male' else 'outfit'
        occasion_term = OCCASION_SEARCH_MAP.get((occasion or '').lower(), '')

        queries = []

        # Primary: color-based
        for color in (compatible_colors or [])[:3]:
            q_parts = [gender_word, color, garment]
            if occasion_term:
                q_parts.append(occasion_term)
            queries.append(' '.join(q_parts))

        # Fallback: bare
        if not queries:
            q_parts = [gender_word, garment]
            if occasion_term:
                q_parts.append(occasion_term)
            queries.append(' '.join(q_parts))

        return queries[:3]   # At most 3 queries to keep API calls reasonable

    # ------------------------------------------------------------------
    # Main public entry point
    # ------------------------------------------------------------------

    def fetch_recommendations(self, profile, preferences, occasion, compatible_colors) -> list:
        """
        Fetch, validate, and upsert real products from SerpApi Google Shopping.
        Returns a list of Outfit ORM instances (source='serpapi_google_shopping', purchasable=True).
        Returns [] when SerpApi is not configured or the call fails.
        """
        if not self.is_configured():
            return []

        queries = self._build_multiple_queries(profile, preferences, occasion, compatible_colors)
        all_outfits = []
        seen_ids = set()

        for query in queries:
            outfits = self._fetch_for_query(query, occasion, profile)
            for o in outfits:
                if o.external_id not in seen_ids:
                    seen_ids.add(o.external_id)
                    all_outfits.append(o)

        print(f"[ShoppingService] Total valid dress products fetched: {len(all_outfits)}")

        # Log the first 3 valid items for debugging
        for i, o in enumerate(all_outfits[:3], 1):
            print(f"  {i}. {o.name}")
            print(f"     Retailer   : {o.store}")
            print(f"     Price      : {o.currency} {o.price}")
            print(f"     Product ID : {o.external_id}")
            print(f"     Image      : {'valid' if o.image_url else 'MISSING'}")
            print(f"     Merchant URL: {'valid' if o.product_url else 'MISSING'}")

        return all_outfits

    def _fetch_for_query(self, query: str, occasion: str, profile) -> list:
        """
        Make one SerpApi request and return normalised Outfit instances.
        """
        print(f"[ShoppingService] Query: '{query}'")

        params = {
            "engine": "google_shopping",
            "q": query,
            "gl": "in",
            "hl": "en",
            "api_key": self.api_key,
            "num": 20,
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            shopping_results = data.get("shopping_results", [])
            print(f"[ShoppingService] SerpApi success for '{query}' — Results: {len(shopping_results)}")

            valid = []
            for item in shopping_results:
                outfit = self._normalize_and_store_product(item, query, occasion, profile)
                if outfit:
                    valid.append(outfit)

            print(f"[ShoppingService] Valid dress products after filtering: {len(valid)}")
            return valid

        except requests.exceptions.HTTPError as e:
            print(f"[ShoppingService] HTTP error for '{query}': {e.response.status_code} — {e.response.text[:200]}")
            return []
        except Exception as e:
            print(f"[ShoppingService] Error for '{query}': {e}")
            return []

    # ------------------------------------------------------------------
    # Normalisation / validation / upsert
    # ------------------------------------------------------------------

    def _normalize_and_store_product(self, item: dict, query: str, occasion: str, profile) -> 'Outfit':
        """
        Validate one raw SerpApi shopping result.
        If valid, upsert it in the DB and return the Outfit instance.
        Returns None when the product should be rejected.
        """
        title = (item.get("title") or "").strip()
        thumbnail = (item.get("thumbnail") or "").strip()
        price = item.get("extracted_price")

        # SerpApi provides product_link (retailer direct) or link (Google page)
        # Always prefer product_link (direct merchant); fall back to link
        product_link = (
            item.get("product_link") or
            item.get("link") or
            ""
        ).strip()

        # Stable ID
        raw_id = str(item.get("product_id") or item.get("id") or product_link or title)
        provider = "serpapi_google_shopping"
        source_id = f"{provider}_{raw_id}"

        # ── Mandatory fields ──────────────────────────────────────────────
        if not title:
            return None
        if not product_link:
            return None
        if not thumbnail:
            return None
        if price is None:
            return None

        # ── Dress filter ──────────────────────────────────────────────────
        title_lower = title.lower()

        # Must contain at least one dress-category word
        if not any(kw in title_lower for kw in DRESS_KEYWORDS):
            return None

        # Must not contain invalid product category words
        if any(kw in title_lower for kw in INVALID_PRODUCT_KEYWORDS):
            return None

        # Gender guard: reject clear men's items when profile is female
        gender = (getattr(profile, 'gender', None) or '').lower()
        if gender == 'female':
            men_terms = ["men's", "mens ", "man's", "boys'", "boy's", "unisex shirt", "men kurta"]
            if any(t in title_lower for t in men_terms):
                return None

        # ── URL validation ────────────────────────────────────────────────
        bad_domains = ['aurafit.store', 'example.com', 'placeholder', 'localhost', '127.0.0']
        if any(d in product_link.lower() for d in bad_domains):
            return None
        if any(d in thumbnail.lower() for d in ['example.com', 'placeholder', 'aurafit.store']):
            return None

        # Require http/https
        if not (product_link.startswith("http://") or product_link.startswith("https://")):
            return None
        if not (thumbnail.startswith("http://") or thumbnail.startswith("https://")):
            return None

        # ── Stock ─────────────────────────────────────────────────────────
        delivery_raw = str(item.get("delivery") or "").lower()
        availability_raw = str(item.get("availability") or "").lower()
        in_stock = True
        if "out of stock" in delivery_raw or "out of stock" in availability_raw or "unavailable" in delivery_raw:
            in_stock = False

        availability_label = item.get("availability") or ("In Stock" if in_stock else "Unavailable")

        # ── Currency ─────────────────────────────────────────────────────
        currency = item.get("currency") or "INR"

        # ── Occasion mapping ─────────────────────────────────────────────
        # Store the correct occasion so the engine's filter can find it
        db_occasion = OCCASION_DB_MAP.get((occasion or '').lower(), 'casual')

        # ── Upsert in DB ─────────────────────────────────────────────────
        try:
            existing = Outfit.query.filter_by(external_id=source_id).first()
            if existing:
                # Update price-sensitive fields only
                existing.price = price
                existing.currency = currency
                existing.in_stock = in_stock
                existing.image_url = thumbnail
                existing.product_url = product_link
                existing.purchasable = True
                existing.source = provider
                # Keep occasion current
                existing.occasion = db_occasion
                db.session.commit()
                return existing

            profile_gender = (getattr(profile, 'gender', None) or '').lower() or 'unisex'

            new_outfit = Outfit(
                external_id=source_id,
                name=title,
                description=f"Live product from {item.get('source', 'Google Shopping')}",
                category='Dress',
                gender=profile_gender,
                occasion=db_occasion,           # ← CRITICAL: set occasion correctly
                season='all',
                style_type=None,
                colors=None,
                product_url=product_link,
                image_url=thumbnail,
                price=price,
                currency=currency,
                brand=item.get("source") or None,
                store=item.get("source") or "Online Retailer",
                in_stock=in_stock,
                purchasable=True,               # ← Real purchasable product
                source=provider,
            )
            db.session.add(new_outfit)
            db.session.commit()
            return new_outfit

        except Exception as e:
            db.session.rollback()
            print(f"[ShoppingService] DB error saving {source_id}: {e}")
            return None
