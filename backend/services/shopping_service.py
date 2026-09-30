import os
import re
import requests
import urllib.parse
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
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


# ==============================================================================
# PRODUCT VALIDATOR (Strict Gender, Category, Image & Identity Validation)
# ==============================================================================

class ProductValidator:
    """
    Strict validation layer for live shopping products.
    Enforces:
      1. Strict Gender Normalization & Filtering (Zero men's items for female profiles, zero women's items for male profiles)
      2. Category Filtering (Only actual dresses for female dress requests, appropriate menswear for male requests)
      3. Image & Identity Validation (Valid non-placeholder, non-mock, authentic live images)
    """

    GENDER_NORMALIZATION = {
        'female': 'female',
        'women': 'female',
        'woman': 'female',
        'womens': 'female',
        'ladies': 'female',
        'girl': 'female',
        'girls': 'female',
        'male': 'male',
        'men': 'male',
        'man': 'male',
        'mens': 'male',
        'gentlemen': 'male',
        'boy': 'male',
        'boys': 'male',
    }

    # Strict male regex patterns (using word boundaries to prevent matching 'women' as 'men')
    MALE_PATTERNS = [
        r"\bmen's\b", r"\bmens\b", r"\bmen\b", r"\bman\b", r"\bmale\b",
        r"\bgentlemen\b", r"\bboy's\b", r"\bboys\b", r"\bboy\b", r"\bhim\b",
        r"\bmenswear\b",
    ]

    # Strict female regex patterns (using word boundaries)
    FEMALE_PATTERNS = [
        r"\bwomen's\b", r"\bwomens\b", r"\bwomen\b", r"\bwoman\b", r"\bfemale\b",
        r"\bladies\b", r"\blady\b", r"\bgirl's\b", r"\bgirls\b", r"\bgirl\b",
        r"\bmaternity\b", r"\bher\b", r"\bwomenswear\b",
    ]

    # Inherently female garments
    FEMALE_GARMENTS = [
        r"\bdress\b", r"\bdresses\b", r"\bgown\b", r"\bgowns\b", r"\bskirt\b", r"\bskirts\b",
        r"\bkurti\b", r"\bkurtis\b", r"\banarkali\b", r"\blehenga\b", r"\bsaree\b", r"\bsari\b",
        r"\bblouse\b", r"\bbra\b", r"\blingerie\b", r"\bmaxi\b", r"\bmidi\b", r"\bmini dress\b",
        r"\bbodycon\b", r"\bwrap dress\b", r"\bparty dress\b", r"\bsummer dress\b",
    ]

    # Inherently male garments
    MALE_GARMENTS = [
        r"\bkurta pyjama\b", r"\bsherwani\b", r"\bdhoti\b", r"\bboxers\b", r"\bmen's suit\b",
        r"\bpolo t-shirt\b",
    ]

    # Strict required patterns for dresses
    DRESS_REQUIRED_PATTERNS = [
        r'\bmidi dress\b', r'\bmaxi dress\b', r'\bmini dress\b', r'\bbodycon dress\b',
        r'\bwrap dress\b', r'\bparty dress\b', r'\bcasual dress\b', r'\bfloral dress\b',
        r'\bsummer dress\b', r'\bevening dress\b', r'\bcocktail dress\b', r'\ba-line dress\b',
        r'\bfit (and|&) flare dress\b', r'\bshirt dress\b', r'\bslip dress\b', r'\btiered dress\b',
        r'\bskater dress\b', r'\bhalter dress\b', r'\bsheath dress\b', r'\bshift dress\b',
        r'\bprom dress\b', r'\bwedding dress\b', r'\bruffle dress\b', r'\bcut-?out dress\b',
        r'\bdress\b', r'\bdresses\b', r'\bgown\b', r'\bgowns\b', r'\bkurti\b', r'\bkurtis\b',
        r'\banarkali\b', r'\blehenga\b', r'\bsaree\b', r'\bsari\b',
    ]

    # Explicit excluded categories that must NEVER be returned when category is dress
    EXCLUDED_DRESS_PATTERNS = [
        r'\bdress shoes?\b', r'\bdress shirts?\b', r'\bdress socks?\b', r'\bdress material\b',
        r'\bdressing (table|mirror)\b', r'\bfancy dress\b',
        r'\b(shoes?|sneakers?|sandals?|heels?|boots?|flats?|loafers?|pumps?|footwear)\b',
        r'\b(handbags?|bags?|purse|clutch|wallet|tote|backpack)\b',
        r'\b(watches?|smartwatch|earrings?|necklaces?|bracelets?|bangles?|jewelry|jewellery|rings?|anklet|pendant)\b',
        r'\b(sunglasses|glasses|hats?|caps?|scarf|scarves|socks?)\b',
        r'\b(t-shirts?|tshirts?|tee|tees)\b',
        r'\b(trousers?|pants?|jeans?|shorts?|leggings?|trackpants?)\b',
        r'\b(skirts?)\b',
        r'\b(bras?|panties|lingerie|underwear)\b',
        r'\b(furniture|curtains?|bedsheets?|cosmetics?|makeup|perfume|lipstick)\b',
    ]

    # Menswear accepted patterns
    MENSWEAR_ACCEPTED_PATTERNS = [
        r'\bshirt\b', r'\bshirts\b', r'\bt-shirt\b', r'\bt-shirts\b', r'\btshirt\b', r'\btshirts\b',
        r'\bpolo\b', r'\bblazer\b', r'\bblazers\b', r'\bsuit\b', r'\bsuits\b', r'\bjacket\b',
        r'\bjackets\b', r'\btrousers?\b', r'\bchinos?\b', r'\bpants?\b', r'\bkurta\b', r'\bsherwani\b',
        r'\bhoodie\b', r'\bsweatshirt\b',
    ]

    # Menswear exclusions
    MENSWEAR_EXCLUDED_PATTERNS = [
        r'\b(dress|dresses|gown|gowns|skirt|skirts|kurti|kurtis|lehenga|saree|sari|blouse|bra|lingerie|heels?)\b',
        r'\b(shoes?|sneakers?|sandals?|boots?|footwear)\b',
        r'\b(handbags?|bags?|purse|clutch|wallet|backpack)\b',
        r'\b(watches?|smartwatch|earrings?|necklaces?|bracelets?|jewelry)\b',
        r'\b(furniture|cosmetics?|perfume)\b',
    ]

    @classmethod
    def normalize_gender(cls, raw_gender: Optional[str]) -> str:
        """Normalize raw gender input to 'female', 'male', or 'unknown'."""
        if not raw_gender:
            return 'unknown'
        g = str(raw_gender).strip().lower()
        return cls.GENDER_NORMALIZATION.get(g, 'unknown')

    @classmethod
    def validate_gender(
        cls,
        title: str,
        description: str = '',
        category: str = '',
        url: str = '',
        metadata: Optional[dict] = None,
        target_gender: str = 'female'
    ) -> Tuple[bool, str]:
        """
        Multi-signal gender validation using title, description, category, URL, and metadata.
        Returns (is_valid, reason).
        """
        norm_target = cls.normalize_gender(target_gender)
        if norm_target not in ('female', 'male'):
            return True, 'Gender unconstrained'

        # Combine text signals
        meta_str = " ".join(str(v) for v in (metadata or {}).values() if isinstance(v, (str, int, float)))
        combined_text = f"{title} {description} {category} {url} {meta_str}".lower()

        has_male_signal = any(bool(re.search(pat, combined_text)) for pat in cls.MALE_PATTERNS)
        has_female_signal = any(bool(re.search(pat, combined_text)) for pat in cls.FEMALE_PATTERNS)
        has_female_garment = any(bool(re.search(pat, combined_text)) for pat in cls.FEMALE_GARMENTS)
        has_male_garment = any(bool(re.search(pat, combined_text)) for pat in cls.MALE_GARMENTS)

        if norm_target == 'female':
            if has_male_signal or has_male_garment:
                return False, 'Rejected: male indicators found in product for female profile'
            if has_female_signal or has_female_garment:
                return True, 'Valid female product'
            return False, 'Rejected: unknown or unverified gender product for female profile'

        if norm_target == 'male':
            if has_female_signal or has_female_garment:
                return False, 'Rejected: female indicators found in product for male profile'
            if has_male_signal or has_male_garment or any(bool(re.search(p, combined_text)) for p in cls.MENSWEAR_ACCEPTED_PATTERNS):
                return True, 'Valid male product'
            return False, 'Rejected: unknown or unverified gender product for male profile'

        return False, 'Rejected: invalid gender matching'

    @classmethod
    def validate_category(
        cls,
        title: str,
        description: str = '',
        category: str = '',
        target_category: str = 'dress',
        target_gender: str = 'female'
    ) -> Tuple[bool, str]:
        """
        Category validation: enforces actual dresses for dress requests, appropriate menswear for male requests.
        Returns (is_valid, reason).
        """
        norm_gender = cls.normalize_gender(target_gender)
        t = title.lower()

        if norm_gender == 'female' or target_category == 'dress':
            # Check false positives & excluded non-dress products first
            for exp in cls.EXCLUDED_DRESS_PATTERNS:
                # Exception: "shirt dress" is a valid dress style
                if exp == r'\b(shirts?)\b' and 'shirt dress' in t:
                    continue
                if re.search(exp, t):
                    return False, f'Rejected: non-dress product category matched ({exp})'

            # Must match at least one approved dress keyword
            matched_dress = any(bool(re.search(dp, t)) for dp in cls.DRESS_REQUIRED_PATTERNS)
            if matched_dress:
                return True, 'Valid dress category'
            return False, 'Rejected: does not contain an approved dress keyword'

        elif norm_gender == 'male':
            for exp in cls.MENSWEAR_EXCLUDED_PATTERNS:
                if re.search(exp, t):
                    return False, f'Rejected: non-menswear or excluded category matched ({exp})'
            matched_menswear = any(bool(re.search(mp, t)) for mp in cls.MENSWEAR_ACCEPTED_PATTERNS)
            if matched_menswear:
                return True, 'Valid menswear category'
            return False, 'Rejected: does not match approved menswear categories'

        return True, 'Category unconstrained'

    @classmethod
    def validate_image(cls, image_url: Optional[str]) -> Tuple[bool, str]:
        """Validate that the image URL is an authentic, non-placeholder, non-mock image."""
        if not image_url or not isinstance(image_url, str):
            return False, 'Image URL missing'
        url_clean = image_url.strip().lower()
        if not (url_clean.startswith('http://') or url_clean.startswith('https://')):
            return False, 'Invalid image protocol'
        # Reject placeholders, mock domains, Unsplash, generic defaults
        if any(bad in url_clean for bad in ['aurafit.store', 'example.com', 'placeholder', 'unsplash', 'default_avatar', 'no-image']):
            return False, 'Disallowed placeholder or mock image domain'
        return True, 'Valid authentic image'


# ==============================================================================
# CACHE
# ==============================================================================

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


# ==============================================================================
# SERPAPI SHOPPING SERVICE
# ==============================================================================

class SerpApiShoppingService:
    """
    SerpApi Google Shopping + Google Immersive Product Stores Shopping Service.
    Acts as the SINGLE SOURCE OF TRUTH for live shopping recommendations.
    """

    def __init__(self):
        self.api_key = os.environ.get('SERPAPI_KEY') or os.environ.get('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search"
        self.retailer_manager = MultiRetailerShoppingManager()
        self.last_fetch_stats: Dict[str, int] = {}

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

    @staticmethod
    def generate_stable_external_id(it: dict, direct_url: str, retailer: str, is_similar: bool = False) -> str:
        """Generate a collision-free, deterministic external ID from SerpApi metadata."""
        raw_id = it.get('product_id') or it.get('id')
        prefix = "serpapi_sim" if is_similar else "serpapi"
        if raw_id:
            return f"{prefix}_{raw_id}"
        seed = f"{retailer}_{direct_url}_{it.get('title', '')}"
        h = hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]
        return f"{prefix}_{h}"

    # ------------------------------------------------------------------
    # Query Building
    # ------------------------------------------------------------------

    def build_shopping_query(
        self,
        profile,
        preferences,
        occasion: str,
        season: str,
        compatible_colors: List[str],
        target_category: str = 'dress'
    ) -> str:
        """
        Builds a gender-specific, high-precision shopping search query.
        Women: 'women dress <color> <occasion> <season>' (e.g. 'women olive green party dress summer')
        Men:   'men <category> <color> <occasion> <season>' (e.g. 'men casual shirt navy party summer')
        """
        norm_gender = ProductValidator.normalize_gender(getattr(profile, 'gender', None) if profile else None)
        if norm_gender not in ('female', 'male'):
            norm_gender = 'female'

        color = compatible_colors[0] if compatible_colors else ''
        occ_term = OCCASION_SEARCH_MAP.get((occasion or '').lower(), (occasion or '').lower())
        if occ_term == 'all':
            occ_term = ''
        season_term = (season or '').lower()
        if season_term in ('all', ''):
            season_term = ''

        if norm_gender == 'female':
            parts = ['women']
            if color:
                parts.append(color)
            if occ_term:
                parts.append(occ_term)
            parts.append('dress')
            if season_term:
                parts.append(season_term)
            return " ".join([p for p in parts if p]).strip()
        else:
            parts = ['men']
            clothing_cat = 'casual shirt'
            if preferences and preferences.preferred_styles:
                style = preferences.preferred_styles[0].lower()
                if style in ('formal', 'suit'):
                    clothing_cat = 'formal suit'
                elif style in ('sporty', 'activewear'):
                    clothing_cat = 'polo t-shirt'
            elif occ_term in ('formal', 'office', 'work'):
                clothing_cat = 'formal shirt'

            parts.append(clothing_cat)
            if color:
                parts.append(color)
            if occ_term:
                parts.append(occ_term)
            if season_term:
                parts.append(season_term)
            return " ".join([p for p in parts if p]).strip()

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
            resp = requests.get(endpoint, params=params, timeout=3)
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
        target_category: str = 'dress',
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Fetches live products from SerpApi Google Shopping + Immersive Stores.
        Enforces strict gender validation, category validation, exact-URL verification,
        and returns immutable standardized dicts backed by database records.
        """
        if not self.is_configured():
            print("[ShoppingService] SERPAPI_KEY is not configured")
            return []

        norm_gender = ProductValidator.normalize_gender(getattr(profile, 'gender', None) if profile else None)
        if norm_gender not in ('female', 'male'):
            norm_gender = 'female'

        # Check Cache
        skin_tone = (getattr(profile, 'skin_tone', None) or '').lower()
        primary_color = compatible_colors[0] if compatible_colors else 'default'
        cache_key = f"{norm_gender}_{skin_tone}_{occasion}_{season}_{primary_color}_{target_category}"
        cached = _shopping_cache.get(cache_key)
        if cached:
            print(f"[ShoppingService] Returning {len(cached)} live products from cache ({cache_key})")
            return cached

        query = self.build_shopping_query(profile, preferences, occasion, season, compatible_colors, target_category)
        print(f"[ShoppingService] Live query: '{query}'")

        params = {
            'engine': 'google_shopping',
            'q': query,
            'gl': 'in',
            'hl': 'en',
            'api_key': self.api_key,
            'num': 25
        }

        try:
            resp = requests.get(self.base_url, params=params, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            shopping_results = data.get('shopping_results', [])
            print(f"[ShoppingService] SerpApi returned {len(shopping_results)} items for '{query}'")
        except Exception as e:
            print(f"[ShoppingService] Failed to query SerpApi: {e}")
            return []

        # Diagnostics counters
        stats = {
            'scanned': len(shopping_results),
            'rejected_gender': 0,
            'rejected_category': 0,
            'rejected_image': 0,
            'rejected_other': 0,
            'valid_candidates': 0,
        }

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
                stats['rejected_other'] += 1
                continue

            # 1. STRICT IMAGE VALIDATION
            img_ok, img_reason = ProductValidator.validate_image(thumbnail)
            if not img_ok:
                stats['rejected_image'] += 1
                continue

            # 2. STRICT GENDER VALIDATION
            gender_ok, g_reason = ProductValidator.validate_gender(
                title=title,
                description=it.get('snippet', '') or it.get('description', ''),
                category=it.get('category', ''),
                url=it.get('link', '') or it.get('product_link', ''),
                metadata=it,
                target_gender=norm_gender
            )
            if not gender_ok:
                stats['rejected_gender'] += 1
                continue

            # 3. STRICT CATEGORY VALIDATION
            cat_ok, c_reason = ProductValidator.validate_category(
                title=title,
                description=it.get('snippet', '') or it.get('description', ''),
                category=it.get('category', ''),
                target_category=target_category,
                target_gender=norm_gender
            )
            if not cat_ok:
                stats['rejected_category'] += 1
                continue

            # Title key for deduplicating identical items across sizes/SKUs
            clean_title_words = [
                w for w in re.sub(r'[^a-zA-Z0-9\s]', '', title.lower()).split()
                if w not in ['women', 'womens', 'ladies', 'dress', 'color', 'size', 'party', 'summer', 'fit', 'flare', 'printed', 'solid', 'men', 'mens']
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
                stats['rejected_other'] += 1
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
                stats['rejected_other'] += 1
                continue

            # Discount calculation
            discount_str = None
            if original_price and original_price > final_price:
                discount_pct = round((1 - (final_price / original_price)) * 100)
                if discount_pct > 0:
                    discount_str = f"{discount_pct}% OFF"

            # Stable collision-free external ID
            ext_id = self.generate_stable_external_id(it, direct_url, retailer_name, is_similar=False)

            # Brand detection
            brand = it.get('brand') or retailer_name

            if title_key:
                seen_title_keys.add(title_key)
            retailer_candidate_counts[retailer_name] = retailer_candidate_counts.get(retailer_name, 0) + 1
            stats['valid_candidates'] += 1

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

        self.last_fetch_stats = stats
        print(f"[ShoppingService] Validation stats: {stats}")

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

            # Collect any additional images belonging to this exact product
            extra_imgs = []
            if isinstance(it.get('thumbnails'), list):
                for t_url in it.get('thumbnails'):
                    if t_url and t_url != thumbnail and ProductValidator.validate_image(t_url)[0]:
                        extra_imgs.append(t_url)

            # Persist to database so OutfitDetail.js loads the EXACT same record by ID
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
                gender=norm_gender,
                category=target_category,
                occasion=OCCASION_DB_MAP.get(occasion.lower(), 'casual'),
                season=season if season != 'all' else 'all',
                colors=compatible_colors[:3] if compatible_colors else ['burgundy', 'pink'],
                additional_images=extra_imgs
            )

            # Derive product dict directly from the persisted record to guarantee 100% identity consistency
            product_dict = outfit_record.to_dict()
            product_dict['title'] = outfit_record.name
            product_dict['availability'] = availability
            product_dict['shopping_links'] = { retailer_name.lower().replace(' ', ''): direct_url }
            live_products.append(product_dict)

        print(f"[ShoppingService] Resolved {len(live_products)} live diverse purchasable products with direct URLs")
        if live_products:
            _shopping_cache.set(cache_key, live_products)

        return live_products

    # ------------------------------------------------------------------
    # Similar Recommendations Query
    # ------------------------------------------------------------------

    def fetch_similar_live_products(
        self,
        main_product: Dict[str, Any],
        profile,
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Generates a live shopping query based on the main recommended item
        (same category, compatible color, occasion) and returns real SerpApi products
        passing the exact same strict gender and category validation.
        """
        if not self.is_configured():
            return []

        norm_gender = ProductValidator.normalize_gender(main_product.get('gender') or getattr(profile, 'gender', None))
        if norm_gender not in ('female', 'male'):
            norm_gender = 'female'

        color = (main_product.get('colors') or ['olive green'])[0]
        occasion = main_product.get('occasion') or 'party'
        target_category = main_product.get('category') or ('dress' if norm_gender == 'female' else 'casual shirt')

        cache_key = f"similar_{norm_gender}_{color}_{occasion}_{target_category}"
        cached = _shopping_cache.get(cache_key)
        if cached:
            return cached

        # Similar query: e.g. "women olive green party dress" or "men navy party shirt"
        if norm_gender == 'female':
            similar_query = f"women {color} {occasion} dress".strip()
        else:
            similar_query = f"men {target_category} {color} {occasion}".strip()

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
            resp = requests.get(self.base_url, params=params, timeout=25)
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

            # 1. STRICT IMAGE VALIDATION
            img_ok, _ = ProductValidator.validate_image(thumbnail)
            if not img_ok:
                continue

            # 2. STRICT GENDER VALIDATION
            gender_ok, _ = ProductValidator.validate_gender(
                title=title,
                description=it.get('snippet', '') or it.get('description', ''),
                category=it.get('category', ''),
                url=it.get('link', '') or it.get('product_link', ''),
                metadata=it,
                target_gender=norm_gender
            )
            if not gender_ok:
                continue

            # 3. STRICT CATEGORY VALIDATION
            cat_ok, _ = ProductValidator.validate_category(
                title=title,
                description=it.get('snippet', '') or it.get('description', ''),
                category=it.get('category', ''),
                target_category=target_category,
                target_gender=norm_gender
            )
            if not cat_ok:
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

            sim_ext_id = self.generate_stable_external_id(it, direct_url, retailer_name, is_similar=True)
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
                gender=norm_gender,
                category=target_category,
                occasion=OCCASION_DB_MAP.get(occasion.lower(), 'casual'),
                season='all',
                colors=[color],
                additional_images=it.get('thumbnails') or []
            )

            sim_dict = outfit_record.to_dict()
            sim_dict['title'] = outfit_record.name
            sim_dict['shopping_links'] = { retailer_name.lower().replace(' ', ''): direct_url }
            similar_items.append(sim_dict)

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
        category: str = 'dress',
        additional_images: Optional[List[str]] = None,
        original_price: Optional[float] = None,
        discount: Optional[str] = None
    ) -> Optional[Outfit]:
        """Upsert a live product into the Outfit table so detail routes can load it with 100% identity."""
        try:
            existing = Outfit.query.filter_by(external_id=external_id).first()
            if existing:
                existing.name = title
                existing.brand = brand
                existing.store = retailer
                existing.image_url = image_url
                existing.additional_images = additional_images or []
                existing.price = price
                existing.original_price = original_price
                existing.discount = discount
                existing.product_url = product_url
                existing.gender = gender
                existing.category = category
                existing.colors = colors
                existing.occasion = occasion
                existing.season = season
                existing.in_stock = True
                existing.purchasable = True
                existing.source = 'serpapi'
                db.session.commit()
                return existing

            new_outfit = Outfit(
                external_id=external_id,
                name=title,
                description=f"Live {retailer} {category} curated for {occasion} wear.",
                category=category,
                gender=gender,
                colors=colors,
                image_url=image_url,
                additional_images=additional_images or [],
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
