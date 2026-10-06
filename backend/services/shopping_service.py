import os
import re
import requests
import urllib.parse
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from extensions import db
from services.occasion_classifier import (
    OccasionClassifier,
    SeasonClassifier,
    get_occasion_search_queries,
    normalize_occasion as classify_normalize_occasion,
    get_occasion_db_value,
)
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
    Strict validation layer for live shopping products per AuraFit specification.
    Enforces:
      1. Strict Gender Normalization & Hard Opposite-Gender Rejection
      2. Kids / Non-Adult Hard Exclusion (zero kids products for adult profiles)
      3. Strict Category Filtering (Only actual dresses for female dress requests, menswear for male requests)
      4. False "Dress" keyword rejection (dress shoes, dress shirts, dress pants, dress material, etc.)
      5. Hard Category Exclusions (shoes, bags, jewellery, accessories, bottoms, standalone tops, sleepwear/homewear, towels/robes)
      6. Canonical Product Identity & Multi-Level Deduplication
      7. Image & URL Validation
      8. Current Selling Price Range Filtering
    """

    GENDER_NORMALIZATION = {
        'female': 'female',
        'women': 'female',
        'woman': 'female',
        'womens': 'female',
        'ladies': 'female',
        'lady': 'female',
        'male': 'male',
        'men': 'male',
        'man': 'male',
        'mens': 'male',
        'gentlemen': 'male',
        'gentleman': 'male',
    }

    # Strict male regex patterns (using word boundaries to prevent matching 'women' as 'men')
    MALE_PATTERNS = [
        r"\bmen's\b", r"\bmens\b", r"\bmen\b", r"\bman\b", r"\bmale\b",
        r"\bgentlemen\b", r"\bgentleman\b", r"\bhim\b",
        r"\bmenswear\b", r"\bmenwear\b",
    ]

    # Strict female regex patterns (using word boundaries)
    FEMALE_PATTERNS = [
        r"\bwomen's\b", r"\bwomens\b", r"\bwomen\b", r"\bwoman\b", r"\bfemale\b",
        r"\bladies\b", r"\blady\b", r"\bwomenswear\b", r"\bwomenwear\b", r"\bladieswear\b",
        r"\bmaternity\b", r"\bher\b",
    ]

    # Kids patterns: MUST be rejected for adult profiles (Section 6)
    KIDS_PATTERNS = [
        r"\bkids?\b", r"\bchildren\b", r"\bchild\b", r"\bbaby\b", r"\bbabies\b",
        r"\btoddlers?\b", r"\bjuniors?\b", r"\bteens?\b", r"\bteenagers?\b",
        r"\bboys?\b", r"\bboy's\b", r"\bgirls?\b", r"\bgirl's\b",
        r"\binfants?\b"
    ]

    # Inherently female garments
    FEMALE_GARMENTS = [
        r"\bdress\b", r"\bdresses\b", r"\bgown\b", r"\bgowns\b",
        r"\bkurti\b", r"\bkurtis\b", r"\banarkali\b", r"\blehenga\b", r"\bsaree\b", r"\bsari\b",
        r"\bskirt\b", r"\bskirts\b", r"\bblouse\b", r"\bbra\b", r"\blingerie\b",
        r"\bmaxi\b", r"\bmidi\b", r"\bmini dress\b", r"\bbodycon\b", r"\bwrap dress\b",
        r"\bparty dress\b", r"\bsummer dress\b", r"\bsundress\b", r"\bsundresses\b",
    ]

    # Inherently male garments
    MALE_GARMENTS = [
        r"\bkurta(?:\s+pyjama|\s+pajama)?\b", r"\bsherwani\b", r"\bdhoti\b", r"\bboxers\b",
        r"\b(?:men's\s+)?suit\b", r"\bpolo\s+t-?shirt\b", r"\bpolo\b", r"\btuxedo\b",
        r"\bnehru\s+jacket\b", r"\bbandhgala\b", r"\bchinos?\b", r"\bmen's\s+shirt\b",
        r"\bwaistcoat\b",
    ]

    # Strict required patterns for dresses (Section 7)
    DRESS_REQUIRED_PATTERNS = [
        r'\bmidi dress(?:es)?\b', r'\bmaxi dress(?:es)?\b', r'\bmini dress(?:es)?\b',
        r'\bparty dress(?:es)?\b', r'\bsummer dress(?:es)?\b', r'\bwinter dress(?:es)?\b',
        r'\bevening dress(?:es)?\b', r'\bcocktail dress(?:es)?\b', r'\bbodycon dress(?:es)?\b',
        r'\bwrap dress(?:es)?\b', r'\ba-line dress(?:es)?\b', r'\bfit (?:and|&) flare dress(?:es)?\b',
        r'\bshirt dress(?:es)?\b', r'\bt-shirt dress(?:es)?\b', r'\btshirt dress(?:es)?\b',
        r'\btee dress(?:es)?\b', r'\bslip dress(?:es)?\b', r'\bskater dress(?:es)?\b',
        r'\bgown(?:s)?\b', r'\bmaxi gown(?:s)?\b', r'\bball gown(?:s)?\b', r'\bevening gown(?:s)?\b',
        r'\bfloral dress(?:es)?\b', r'\bprinted dress(?:es)?\b', r'\bformal dress(?:es)?\b',
        r'\bcasual dress(?:es)?\b', r'\bdenim dress(?:es)?\b', r'\bknit dress(?:es)?\b',
        r'\bsatin dress(?:es)?\b', r'\bsequin dress(?:es)?\b', r'\bruched dress(?:es)?\b',
        r'\bhalter dress(?:es)?\b', r'\boff shoulder dress(?:es)?\b', r'\bone shoulder dress(?:es)?\b',
        r'\bsheath dress(?:es)?\b', r'\bshift dress(?:es)?\b', r'\bprom dress(?:es)?\b',
        r'\bwedding dress(?:es)?\b', r'\bruffle dress(?:es)?\b', r'\bcut-?out dress(?:es)?\b',
        r'\btiered dress(?:es)?\b', r'\bpleated dress(?:es)?\b', r'\bsmocked dress(?:es)?\b',
        r'\bstrapless dress(?:es)?\b', r'\bbackless dress(?:es)?\b', r'\bflared dress(?:es)?\b',
        r'\bpeplum dress(?:es)?\b', r'\bbabydoll dress(?:es)?\b', r'\bkaftan dress(?:es)?\b',
        r'\bcaftan dress(?:es)?\b', r'\bsweater dress(?:es)?\b', r'\bblazer dress(?:es)?\b',
        r'\banarkali(?:\s+(?:suit|dress|gown))?\b', r'\bkurti(?:\s+dress)?\b', r'\bkurtis\b',
        r'\bsaree(?:s)?\b', r'\bsari(?:s)?\b', r'\bsundress(?:es)?\b', r'\bdress(?:es)?\b',
    ]

    # False dress matches that must be REJECTED (Section 8)
    FALSE_DRESS_PATTERNS = [
        r'\bdress\s+(?:shoes?|socks?|shirts?|trousers?|pants?|boots?|sandals?|material|fabric|accessories|belts?|bags?|cases?)\b',
        r'\b(?:shoes?|socks?|shirts?|trousers?|pants?|boots?|sandals?|material|fabric|accessories|belts?|bags?)\s+for\s+(?:party\s+)?dress(?:es)?\b',
        r'\b(?:unstitched|semi[- ]stitched)\s+(?:dress|suit|fabric|material|piece)\b',
        r'\b(?:dress\s+material|unstitched\s+fabric)\b',
        r'\bdressing\s+(?:table|mirror|room)\b',
        r'\bfancy\s+dress(?:\s+costume)?\b',
    ]

    # Category Exclusions for dresses (Section 9 & 10)
    EXCLUDED_DRESS_PATTERNS = [
        # Shoes / Footwear
        (r'\b(shoes?|sneakers?|sandals?|heels?|pumps?|slippers?|loafers?|boots?|footwear|wedges?|flats?|mules?|stilettos?|slides?|chappals?|flip[- ]flops?|clogs?|espadrilles?|oxfords?|derbys?|booties?)\b', 'footwear'),
        # Bags
        (r'\b(handbags?|bags?|purse|clutch|wallets?|totes?|backpacks?|sling\s*bags?|potli|crossbody|shoulder\s*bags?|satchels?|duffles?|suitcases?)\b', 'bag'),
        # Jewellery
        (r'\b(earrings?|necklaces?|bracelets?|bangles?|rings?|anklets?|jewellery|jewelry|pendants?|chains?|chokers?|mangalsutras?|jhumkas?|nose\s*pins?)\b', 'jewellery'),
        # Accessories
        (r'\b(watches?|smartwatch|sunglasses?|eyewear|glasses|belts?|scarfs?|scarves|hair\s*accessories|hair\s*accessory|hairbands?|headbands?|scrunchies?|hats?|caps?|socks?|stockings?|stoles?)\b', 'accessory'),
        # Bottoms (shorts as garment, not short as adjective)
        (r'\b(trousers?|pants?|jeans?|denim\s+pants|shorts|leggings?|joggers?|culottes?|palazzos?|track\s*pants?|tights?|capris?)\b', 'bottoms'),
        # Standalone Tops (subject to dress exception e.g. shirt dress)
        (r'\b(t-shirts?|tshirts?|tees?|shirts?|blouses?|crop\s*tops?|tops?|camisoles?|tank\s*tops?|corsets?|hoodies?|sweatshirts?|sweaters?|cardigans?|shrugs?|jackets?|blazers?|coats?)\b', 'tops'),
        # Sleepwear / Homewear / Undergarments / Towels / Robes
        (r'\b(nightwear|night\s*suit|pyjamas?|pajamas?|sleepwear|robes?|bathrobes?|dressing\s*gown|lounge\s*set|loungewear|house\s*dress|towels?|bath\s*towels?|shower\s*robes?|bedsheets?|curtains?|quilts?|duvets?|pillows?|nightys?|nighties?|nightdress(?:es)?|lingerie|bras?|panties?|panty|underwear|shapewear)\b', 'sleepwear_or_homewear'),
        # Cosmetics / Beauty / Personal care
        (r'\b(cosmetics?|makeup|perfumes?|lipsticks?|lotions?|creams?|serums?|foundations?|eyeliners?|shampoos?|conditioners?|soaps?|skincare|haircare)\b', 'beauty'),
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

    # Unisex patterns
    UNISEX_PATTERNS = [
        r"\bunisex\b", r"\ball-gender\b", r"\bgender-neutral\b",
    ]

    @classmethod
    def normalize_gender(cls, raw_gender: Optional[str]) -> str:
        """Normalize raw gender input to 'female', 'male', or 'unknown'."""
        if not raw_gender:
            return 'unknown'
        g = str(raw_gender).strip().lower()
        return cls.GENDER_NORMALIZATION.get(g, 'unknown')

    @classmethod
    def is_kids_product(cls, normalized_text: str) -> Tuple[bool, str]:
        """Detects if a product is intended for children/teens/babies."""
        for pat in cls.KIDS_PATTERNS:
            m = re.search(pat, normalized_text)
            if m:
                return True, m.group(0)
        return False, ""

    @classmethod
    def normalize_title(cls, title: str) -> str:
        """
        Normalizes a product title per Section 16:
          - lowercase
          - remove punctuation
          - normalize whitespace
          - remove tracking fragments
          - remove irrelevant size tokens (e.g. Size M, - Size: XL, Size 38)
          - remove marketing / fluff words
        """
        if not title:
            return ""
        t = title.lower()
        t = re.sub(r'https?://\S+', '', t)
        # Remove size markers e.g. "- Size M", "(Size: L)", "Size 38", "/ M"
        t = re.sub(r'[\-\|\(\[\/]?\s*\b(?:size|sz)?\s*(?:xxxl|xxl|xl|xs|[sml])\b\s*[\)\/\]]?', ' ', t)
        t = re.sub(r'[\-\|\(\[\/]?\s*\b(?:size|sz)\s*[:\-]?\s*\d+\b\s*[\)\/\]]?', ' ', t)
        # Remove punctuation
        t = re.sub(r'[^a-z0-9\s]', ' ', t)
        noise = {
            'new', 'latest', 'stylish', 'trendy', 'hot', 'exclusive', 'offer', 'sale',
            'online', 'india', 'buy', 'best', 'fashion', 'collection', 'pack', 'piece',
            'premium', 'women', 'womens', 'men', 'mens', 'unisex'
        }
        words = [w for w in t.split() if w not in noise]
        return " ".join(words)

    @staticmethod
    def canonicalize_url(raw_url: Optional[str]) -> str:
        """
        Strips tracking query parameters and canonicalizes retailer product URLs for deduplication.
        """
        if not raw_url or not isinstance(raw_url, str):
            return ""
        cand = raw_url.strip()
        try:
            parsed = urllib.parse.urlparse(cand)
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'srsltid', 'gclid', 'fbclid', 'source', 'ref_', 'psc', 'tag',
                'pf_rd_r', 'pf_rd_p', 'pf_rd_m', 'pf_rd_s', 'pf_rd_t', 'pf_rd_i',
                'pd_rd_r', 'pd_rd_w', 'pd_rd_wg', 'linkcode', 'camp', 'creative', 'ref',
                'spm', '_x_tr_sl', '_x_tr_tl', '_x_tr_hl', 'size', 'sz', 'color', 'colour'
            }
            qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)
            cleaned_qs = {k: v for k, v in qs.items() if k.lower() not in tracking_params and not k.lower().startswith('utm_')}
            new_query = urllib.parse.urlencode(cleaned_qs, doseq=True)
            clean_path = parsed.path
            
            # Amazon ASIN canonicalization
            asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', clean_path, re.IGNORECASE)
            if 'amazon' in parsed.netloc.lower() and asin_match:
                asin = asin_match.group(1).upper()
                return f"https://www.amazon.in/dp/{asin}"

            # Myntra canonicalization: /productId/buy
            if 'myntra' in parsed.netloc.lower():
                m_id = re.search(r'/(\d+)/buy', clean_path)
                if m_id:
                    return f"https://www.myntra.com/{m_id.group(1)}/buy"

            return urllib.parse.urlunparse((
                parsed.scheme or 'https',
                parsed.netloc.lower(),
                clean_path.rstrip('/'),
                parsed.params,
                new_query,
                ''
            ))
        except Exception:
            return cand

    @classmethod
    def extract_canonical_product_id(cls, product: dict, retailer: str, direct_url: str) -> str:
        """
        Deterministic canonical product identity per Section 13:
          Use strongest available identifier in order:
            1. retailer product ID / merchant product ID / ASIN / PID
            2. SKU
            3. extracted direct URL identifier
            4. fallback hash of retailer + canonical URL or normalized title
        """
        ret_prefix = (retailer or 'store').lower().replace(' ', '').replace('&', 'n')
        for k in ('retailer_product_id', 'merchant_product_id', 'product_id', 'asin', 'sku', 'id'):
            val = product.get(k)
            if val and str(val).strip():
                clean_val = str(val).strip().replace('serpapi_', '').replace('serpapi_sim_', '')
                if clean_val:
                    return f"{ret_prefix}:{clean_val}"

        if direct_url:
            u = direct_url.lower()
            asin_m = re.search(r'/(?:dp|gp/product)/([a-z0-9]{10})', u)
            if 'amazon' in ret_prefix and asin_m:
                return f"amazon:{asin_m.group(1).upper()}"
            myntra_m = re.search(r'/(\d+)/buy', direct_url)
            if 'myntra' in ret_prefix and myntra_m:
                return f"myntra:{myntra_m.group(1)}"
            ajio_m = re.search(r'/p/([0-9a-z_]+)', u)
            if 'ajio' in ret_prefix and ajio_m:
                return f"ajio:{ajio_m.group(1)}"
            flipkart_m = re.search(r'pid=([a-z0-9]+)', u)
            if 'flipkart' in ret_prefix and flipkart_m:
                return f"flipkart:{flipkart_m.group(1).upper()}"
            meesho_m = re.search(r'/p/([0-9a-z]+)', u)
            if 'meesho' in ret_prefix and meesho_m:
                return f"meesho:{meesho_m.group(1)}"
            hm_m = re.search(r'/productpage\.([0-9]+)\.html', u)
            if ('h&m' in ret_prefix or 'hm' in ret_prefix) and hm_m:
                return f"hm:{hm_m.group(1)}"

            norm_u = SerpApiShoppingService.canonicalize_url(direct_url) if direct_url else ""
            h = hashlib.sha256(norm_u.encode('utf-8')).hexdigest()[:16]
            return f"{ret_prefix}:{h}"

        norm_t = cls.normalize_title(product.get('title') or product.get('name') or '')
        h = hashlib.sha256(f"{ret_prefix}_{norm_t}".encode('utf-8')).hexdigest()[:16]
        return f"{ret_prefix}:{h}"

    @classmethod
    def is_gender_compatible(
        cls,
        product: dict,
        target_gender: str = 'female',
        target_category: str = 'dress'
    ) -> Tuple[bool, str, str]:
        """
        Centralized gender classification per Section 4, 5, 6.
        Returns: (is_compatible_bool, detected_gender, reason)
        For women's profiles: rejects any opposite gender (men's) or kids products.
        For men's profiles: rejects any opposite gender (women's) or kids products.
        """
        norm_target = cls.normalize_gender(target_gender)
        if norm_target not in ('female', 'male'):
            return True, 'unconstrained', 'Gender unconstrained'

        # Extract all textual signals per Section 3
        title = str(product.get('title') or product.get('name') or '')
        desc = str(product.get('description') or product.get('snippet') or '')
        cat = str(product.get('category') or '')
        ptype = str(product.get('product_type') or '')
        dept = str(product.get('department') or '')
        brand = str(product.get('brand') or '')
        ret = str(product.get('retailer') or product.get('store') or product.get('source') or '')
        url = str(product.get('link') or product.get('product_url') or '')
        breadcrumbs = str(product.get('breadcrumbs') or '')

        normalized_text = f"{title} {desc} {cat} {ptype} {dept} {brand} {ret} {url} {breadcrumbs}".lower()

        # Section 6: KIDS MUST NOT BE MIXED WITH ADULT RESULTS
        is_kid, kid_word = cls.is_kids_product(normalized_text)
        if is_kid:
            return False, 'kids', f"Kids product rejected for adult profile ({kid_word})"

        if norm_target == 'female':
            # Hard Opposite-Gender Rejection (Section 5)
            has_male_signal = any(bool(re.search(pat, normalized_text)) for pat in cls.MALE_PATTERNS)
            if has_male_signal:
                return False, 'male', 'rejected opposite gender (male) product'

            # Positive Female Signals (Section 4)
            has_female_signal = any(bool(re.search(pat, normalized_text)) for pat in cls.FEMALE_PATTERNS)
            has_female_garment = any(bool(re.search(pat, normalized_text)) for pat in cls.FEMALE_GARMENTS)
            has_unisex = any(bool(re.search(pat, normalized_text)) for pat in cls.UNISEX_PATTERNS)

            if has_female_signal or has_female_garment:
                return True, 'female', 'valid female product'
            if has_unisex:
                return True, 'unisex', 'valid unisex product'

            return False, 'unknown', 'no positive female signals found'

        elif norm_target == 'male':
            # Hard Opposite-Gender Rejection (Section 5)
            has_female_signal = any(bool(re.search(pat, normalized_text)) for pat in cls.FEMALE_PATTERNS + cls.FEMALE_GARMENTS)
            if has_female_signal:
                return False, 'female', 'rejected opposite gender (female) product'

            # Positive Male Signals (Section 4)
            has_male_signal = any(bool(re.search(pat, normalized_text)) for pat in cls.MALE_PATTERNS)
            has_male_garment = any(bool(re.search(pat, normalized_text)) for pat in cls.MALE_GARMENTS)
            has_unisex = any(bool(re.search(pat, normalized_text)) for pat in cls.UNISEX_PATTERNS)

            if has_male_signal or has_male_garment:
                return True, 'male', 'valid male product'
            if has_unisex:
                return True, 'unisex', 'valid unisex product'

            return False, 'unknown', 'no positive male signals found'

        return False, 'unknown', 'invalid gender matching'

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
        """Backwards-compatible wrapper around is_gender_compatible."""
        prod = {
            'title': title,
            'description': description,
            'category': category,
            'link': url
        }
        if metadata:
            prod.update(metadata)
        ok, _, reason = cls.is_gender_compatible(prod, target_gender=target_gender)
        return ok, reason

    @classmethod
    def is_actual_dress(cls, product: dict) -> Tuple[bool, str, str]:
        """
        Strict women's dress classification per Section 7, 8, 9, 10, 11.
        Returns: (is_dress_bool, detected_category, reason)
        """
        title = str(product.get('title') or product.get('name') or '').strip()
        desc = str(product.get('description') or product.get('snippet') or '')
        cat = str(product.get('category') or '')
        ptype = str(product.get('product_type') or '')
        url = str(product.get('link') or product.get('product_url') or '')
        breadcrumbs = str(product.get('breadcrumbs') or '')

        normalized_text = f"{title} {desc} {cat} {ptype} {url} {breadcrumbs}".lower()
        title_low = title.lower()

        # Section 8: False "Dress" Matches MUST be rejected
        for pat in cls.FALSE_DRESS_PATTERNS:
            m = re.search(pat, normalized_text)
            if m:
                return False, 'false_dress', f"rejected false dress match ({m.group(0)})"

        # Section 11: Check primary category priority (e.g. "Women's Heels for Party Dress")
        primary_for_dress = re.search(r'\b(shoes?|sandals?|heels?|boots?|sneakers?|pumps?|clutch|bags?|handbags?|earrings?|necklace|jewellery|jewelry)\s+for\s+(?:(?:women\'?s|party|evening|summer)\s+)?dress(?:es)?\b', normalized_text)
        if primary_for_dress:
            return False, 'excluded_accessory', f"primary product is {primary_for_dress.group(1)} for dress"

        # URL path check for primary excluded categories
        if url:
            u_low = url.lower()
            for excluded_path, cat_name in [
                ('/shoes/', 'footwear'), ('/footwear/', 'footwear'), ('/sandals/', 'footwear'),
                ('/bags/', 'bag'), ('/handbags/', 'bag'), ('/jewellery/', 'jewellery'),
                ('/jewelry/', 'jewellery'), ('/accessories/', 'accessory'), ('/bottoms/', 'bottoms'),
                ('/pants/', 'bottoms'), ('/jeans/', 'bottoms'), ('/tops/', 'tops')
            ]:
                if excluded_path in u_low and not any(dp in u_low for dp in ['dress', 'dresses']):
                    return False, cat_name, f"URL path belongs to excluded category {cat_name}"

        # Section 9 & 10: Hard Category Exclusion List
        # Mask approved dress compounds so their sub-words (e.g. shirt in "shirt dress") don't trigger top exclusions
        t_masked = re.sub(
            r'\b(?:shirt|t-shirt|tshirt|tee|sweater|blazer|jacket|hoodie|sweatshirt|slip|camisole)\s+dress(?:es)?\b',
            '[DRESS_COMPOUND]',
            normalized_text,
            flags=re.IGNORECASE
        )

        for pat, cat_name in cls.EXCLUDED_DRESS_PATTERNS:
            m = re.search(pat, t_masked)
            if m:
                matched_term = m.group(0)
                return False, cat_name, f"excluded category ({cat_name}: {matched_term})"

        # Section 7: Must match at least one approved dress style
        matched_dress = any(bool(re.search(dp, title_low)) for dp in cls.DRESS_REQUIRED_PATTERNS) or \
                        any(bool(re.search(dp, normalized_text)) for dp in cls.DRESS_REQUIRED_PATTERNS)

        if matched_dress:
            return True, 'dress', 'valid women\'s dress'

        return False, 'non_dress', 'no approved dress pattern matched'

    @classmethod
    def detect_category(cls, title: str, description: str = '', category_field: str = '') -> str:
        """Detect product category from title, description, and metadata for structured logging."""
        p_mock = {'title': title, 'description': description, 'category': category_field}
        is_d, det_c, _ = cls.is_actual_dress(p_mock)
        if is_d:
            return 'dress'
        combined = f"{title} {description} {category_field}".lower()
        for pat, c_name in cls.EXCLUDED_DRESS_PATTERNS:
            if re.search(pat, combined):
                return c_name
        return 'general clothing'

    @classmethod
    def validate_category(
        cls,
        title_or_product: Any = None,
        description: str = '',
        category: str = '',
        target_category: str = 'dress',
        target_gender: str = 'female',
        title: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Category validation: enforces actual dresses for dress requests, appropriate menswear for male requests.
        Returns (is_valid, reason).
        """
        if title is not None and title_or_product is None:
            title_or_product = title

        if isinstance(title_or_product, dict):
            prod = title_or_product
        else:
            prod = {
                'title': str(title_or_product or title or ''),
                'description': description,
                'category': category
            }

        norm_gender = cls.normalize_gender(target_gender)

        if norm_gender == 'female' or target_category == 'dress':
            is_dress, det_cat, reason = cls.is_actual_dress(prod)
            return is_dress, reason

        elif norm_gender == 'male':
            t = f"{prod.get('title', '')} {prod.get('description', '')}".lower()
            for exp in cls.MENSWEAR_EXCLUDED_PATTERNS:
                m = re.search(exp, t)
                if m:
                    return False, f"non-menswear or excluded category matched ({m.group(0)})"
            for mp in cls.MENSWEAR_ACCEPTED_PATTERNS:
                if re.search(mp, t):
                    return True, 'valid menswear category'
            return False, 'does not match approved menswear categories'

        return True, 'category unconstrained'

    @classmethod
    def validate_image(cls, image_url: Optional[str]) -> Tuple[bool, str]:
        """Validate that the image URL is an authentic, non-placeholder, non-mock image."""
        if not image_url or not isinstance(image_url, str):
            return False, 'Image URL missing'
        url_clean = image_url.strip().lower()
        if not (url_clean.startswith('http://') or url_clean.startswith('https://')):
            return False, 'Invalid image protocol'
        # Reject placeholders, mock domains, Unsplash, generic defaults
        if any(bad in url_clean for bad in ['aurafit.store', 'example.com', 'placeholder', 'unsplash', 'default_avatar', 'no-image', 'avatar']):
            return False, 'Disallowed placeholder or mock image domain'
        return True, 'Valid authentic image'


def detect_product_gender(product: dict) -> str:
    """
    Detects product gender strictly using actual shopping data evidence.
    Returns: 'female', 'male', 'unisex', or 'unknown'.
    """
    if not product or not isinstance(product, dict):
        return 'unknown'
    _, det_g, _ = ProductValidator.is_gender_compatible(product, 'female')
    if det_g in ('female', 'kids'):
        return det_g
    _, det_m, _ = ProductValidator.is_gender_compatible(product, 'male')
    if det_m == 'male':
        return 'male'
    return det_g



ProductValidator.detect_product_gender = staticmethod(detect_product_gender)


def parse_price_range(
    range_str: Optional[str] = None,
    custom_min: Optional[float] = None,
    custom_max: Optional[float] = None
) -> Tuple[Optional[float], Optional[float], str]:
    """
    Parses price filter into (min_price, max_price, display_label).
    Supports preset ranges and custom min/max.
    """
    has_custom = False
    c_min = None
    c_max = None
    if custom_min is not None and str(custom_min).strip() != '':
        try:
            c_min = float(custom_min)
            has_custom = True
        except (ValueError, TypeError):
            pass
    if custom_max is not None and str(custom_max).strip() != '':
        try:
            c_max = float(custom_max)
            has_custom = True
        except (ValueError, TypeError):
            pass

    if has_custom:
        if c_min is not None and c_max is not None:
            label = f"₹{int(c_min):,} – ₹{int(c_max):,}"
        elif c_min is not None:
            label = f"Above ₹{int(c_min):,}"
        elif c_max is not None:
            label = f"Under ₹{int(c_max):,}"
        else:
            label = "All Prices"
        return c_min, c_max, label

    if not range_str or str(range_str).strip().lower() in ('all', 'all prices', 'all_prices', ''):
        return None, None, 'All Prices'

    r = str(range_str).strip().lower()
    if r in ('under_500', 'under 500', 'under-500', '<500', 'under ₹500'):
        return None, 500.0, 'Under ₹500'
    elif r in ('500_1000', '500-1000', '500 - 1000', '500_1,000', '₹500 – ₹1,000', '₹500 - ₹1,000'):
        return 500.0, 1000.0, '₹500 – ₹1,000'
    elif r in ('1000_2000', '1000-2000', '1000 - 2000', '1,000 - 2,000', '₹1,000 – ₹2,000', '₹1,000 - ₹2,000'):
        return 1000.0, 2000.0, '₹1,000 – ₹2,000'
    elif r in ('1000_2500', '1000-2500', '1000 - 2500', '1,000 - 2,500', '₹1,000 – ₹2,500', '₹1,000 - ₹2,500'):
        return 1000.0, 2500.0, '₹1,000 – ₹2,500'
    elif r in ('1000_3000', '1000-3000', '1000 - 3000', '1,000 - 3,000', '₹1,000 – ₹3,000', '₹1,000 - ₹3,000'):
        return 1000.0, 3000.0, '₹1,000 – ₹3,000'
    elif r in ('2000_3000', '2000-3000', '2000 - 3000', '2,000 - 3,000', '₹2,000 – ₹3,000', '₹2,000 - ₹3,000'):
        return 2000.0, 3000.0, '₹2,000 – ₹3,000'
    elif r in ('2500_5000', '2500-5000', '2500 - 5000', '2,500 - 5,000', '₹2,500 – ₹5,000', '₹2,500 - ₹5,000'):
        return 2500.0, 5000.0, '₹2,500 – ₹5,000'
    elif r in ('3000_5000', '3000-5000', '3000 - 5000', '3,000 - 5,000', '₹3,000 – ₹5,000', '₹3,000 - ₹5,000'):
        return 3000.0, 5000.0, '₹3,000 – ₹5,000'
    elif r in ('5000_10000', '5000-10000', '5000 - 10000', '5,000 - 10,000', '₹5,000 – ₹10,000', '₹5,000 - ₹10,000'):
        return 5000.0, 10000.0, '₹5,000 – ₹10,000'
    elif r in ('5000_plus', '5000+', 'above_5000', 'above 5000', '>5000', '₹5,000+'):
        return 5000.0, None, '₹5,000+'
    elif r in ('above_10000', 'above 10000', 'above-10000', '>10000', 'above ₹10,000'):
        return 10000.0, None, 'Above ₹10,000'

    # Try numeric range matching e.g. "1000-2500"
    m = re.match(r'(\d+)\s*[-_–]\s*(\d+)', r)
    if m:
        mn, mx = float(m.group(1)), float(m.group(2))
        return mn, mx, f"₹{int(mn):,} – ₹{int(mx):,}"

    m_plus = re.match(r'(?:above|over|>)\s*(\d+)|(\d+)\s*(?:\+|plus)', r)
    if m_plus:
        val = float(m_plus.group(1) or m_plus.group(2))
        return val, None, f"Above ₹{int(val):,}"

    m_under = re.match(r'(?:under|below|<)\s*(\d+)', r)
    if m_under:
        val = float(m_under.group(1))
        return None, val, f"Under ₹{int(val):,}"

    return None, None, 'All Prices'


ProductValidator.parse_price_range = staticmethod(parse_price_range)


def validate_price(
    price: Optional[float],
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> Tuple[bool, str]:
    """Validates that price is within the specified min/max range strictly on current selling price."""
    if price is None:
        return False, "NO"
    try:
        p = float(price)
    except (ValueError, TypeError):
        return False, "NO"
    if p <= 0:
        return False, "NO"
    if min_price is not None and p < min_price:
        return False, "NO"
    if max_price is not None and p > max_price:
        return False, "NO"
    return True, "YES"


ProductValidator.validate_price = staticmethod(validate_price)


def get_price_query_cue(price_range: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None) -> str:
    """Returns search query price terms to guide SerpApi Google Shopping."""
    min_p, max_p, _ = parse_price_range(price_range, min_price, max_price)
    if min_p is None and max_p is not None:
        return f"under {int(max_p)}"
    elif min_p is not None and max_p is not None:
        return f"{int(min_p)} to {int(max_p)}"
    elif min_p is not None and max_p is None:
        return f"above {int(min_p)}"
    return ""


def validate_retailer(
    product_retailer: str,
    requested_retailer: Optional[str] = None
) -> Tuple[bool, str]:
    """Validates that product retailer matches the requested retailer filter."""
    if not requested_retailer or requested_retailer.lower() in ('all', 'all retailers', '', 'none'):
        return True, "YES"
    p_ret = (product_retailer or '').strip().lower()
    req_ret = requested_retailer.strip().lower()
    if 'amazon' in req_ret:
        return ('amazon' in p_ret), "YES" if ('amazon' in p_ret) else "NO"
    if 'myntra' in req_ret:
        return ('myntra' in p_ret), "YES" if ('myntra' in p_ret) else "NO"
    if 'ajio' in req_ret:
        return ('ajio' in p_ret), "YES" if ('ajio' in p_ret) else "NO"
    if 'flipkart' in req_ret:
        return ('flipkart' in p_ret), "YES" if ('flipkart' in p_ret) else "NO"
    if 'nykaa' in req_ret:
        return ('nykaa' in p_ret), "YES" if ('nykaa' in p_ret) else "NO"
    if 'meesho' in req_ret:
        return ('meesho' in p_ret), "YES" if ('meesho' in p_ret) else "NO"
    if 'zara' in req_ret:
        return ('zara' in p_ret), "YES" if ('zara' in p_ret) else "NO"
    if 'h&m' in req_ret or 'hm' in req_ret:
        return ('h&m' in p_ret or 'hm' in p_ret), "YES" if ('h&m' in p_ret or 'hm' in p_ret) else "NO"
    if 'tata' in req_ret or 'cliq' in req_ret:
        return ('tata cliq' in p_ret or 'tatacliq' in p_ret), "YES" if ('tata cliq' in p_ret or 'tatacliq' in p_ret) else "NO"
    if 'newme' in req_ret:
        return ('newme' in p_ret), "YES" if ('newme' in p_ret) else "NO"
    if 'vero moda' in req_ret:
        return ('vero moda' in p_ret), "YES" if ('vero moda' in p_ret) else "NO"
    if req_ret in p_ret or p_ret in req_ret:
        return True, "YES"
    return False, "NO"


ProductValidator.validate_retailer = staticmethod(validate_retailer)


# ------------------------------------------------------------------------------
# SKIN-TONE COLOR PALETTES (Section 5)
# ------------------------------------------------------------------------------
SKIN_TONE_PALETTES = {
    'fair': ['emerald', 'burgundy', 'navy', 'lavender', 'rose', 'pastel blue', 'forest green', 'wine', 'red'],
    'light': ['soft blue', 'lavender', 'peach', 'mint green', 'rose pink', 'emerald', 'navy', 'wine'],
    'medium': ['olive', 'emerald', 'mustard', 'rust', 'burgundy', 'teal', 'coral', 'beige', 'cream', 'navy'],
    'olive': ['rust', 'coral', 'cream', 'charcoal', 'deep teal', 'olive', 'emerald', 'mustard', 'burgundy'],
    'deep': ['emerald', 'cobalt blue', 'royal blue', 'burgundy', 'plum', 'mustard', 'orange', 'fuchsia', 'ivory', 'teal']
}

DEFAULT_SKIN_PALETTE = ['emerald', 'burgundy', 'navy', 'olive', 'coral', 'royal blue', 'wine', 'rust', 'cream', 'teal']


def _safe_print(msg: str):
    """Safely prints text handling Windows console encoding issues."""
    try:
        print(msg)
    except (UnicodeEncodeError, Exception):
        try:
            cleaned = msg.encode('ascii', errors='replace').decode('ascii')
            print(cleaned)
        except Exception:
            pass


# ------------------------------------------------------------------------------
# STRUCTURED DEBUG LOGGING (Section 27)
# ------------------------------------------------------------------------------
def log_shopping_request(gender: str, occasion: str, season: str, skin_tone: str, colors: List[str], price_range: str, retailer: Optional[str], target: int):
    """Outputs standardized [SHOPPING REQUEST] logging."""
    _safe_print(
        f"\n[SHOPPING REQUEST]\n"
        f"Gender: {gender}\n"
        f"Occasion: {occasion}\n"
        f"Season: {season}\n"
        f"Skin Tone: {skin_tone}\n"
        f"Colors: {', '.join(colors) if colors else 'default'}\n"
        f"Price Range: {price_range}\n"
        f"Retailer: {retailer or 'All Retailers'}\n"
        f"Target: {target}"
    )


def log_shopping_query(query: str, returned: int, accepted: int, rejected: int):
    """Outputs standardized [SHOPPING QUERY] logging."""
    _safe_print(
        f"\n[SHOPPING QUERY]\n"
        f"Query: {query}\n"
        f"Returned: {returned}\n"
        f"Accepted: {accepted}\n"
        f"Rejected: {rejected}"
    )


def log_shopping_filter(
    title: str,
    retailer: str,
    requested_gender: str,
    detected_gender: str,
    requested_category: str,
    detected_category: str,
    price: Optional[float],
    requested_price_range: str,
    decision: str = "ACCEPT",
    reason: str = "All filters matched",
    canonical_product_id: str = "N/A"
):
    """Outputs standardized [SHOPPING FILTER] logging matching Section 37."""
    price_str = f"{int(price)}" if price is not None else "N/A"
    _safe_print(
        f"\n[SHOPPING FILTER]\n\n"
        f"Title: {title}\n"
        f"Retailer: {retailer}\n"
        f"Requested Gender: {requested_gender}\n"
        f"Detected Gender: {detected_gender}\n"
        f"Requested Category: {requested_category}\n"
        f"Detected Category: {detected_category}\n"
        f"Price: {price_str}\n"
        f"Requested Price Range: {requested_price_range}\n"
        f"Decision: {decision}\n"
        f"Reason: {reason}\n"
        f"Canonical Product ID: {canonical_product_id}"
    )


def log_filter_decision(
    title: str,
    retailer: str,
    detected_gender: str,
    requested_gender: str,
    detected_category: str,
    requested_category: str,
    live_price: Optional[float] = None,
    selected_price_range: str = "All Prices",
    price_match: str = "YES",
    gender_match: str = "YES",
    category_match: str = "YES",
    decision: str = "ACCEPT",
    reason: str = "All filters matched",
    color: str = "N/A",
    availability: str = "IN STOCK",
    url: str = "N/A",
    canonical_product_id: str = "N/A"
):
    """Backwards-compatible wrapper around log_shopping_filter."""
    log_shopping_filter(
        title=title,
        retailer=retailer,
        requested_gender=requested_gender,
        detected_gender=detected_gender,
        requested_category=requested_category,
        detected_category=detected_category,
        price=live_price,
        requested_price_range=selected_price_range,
        decision=decision,
        reason=reason,
        canonical_product_id=canonical_product_id
    )


def log_shopping_summary(
    requested_gender: str,
    requested_category: str,
    requested_occasion: str,
    requested_season: str,
    requested_price_range: str,
    candidates: int,
    gender_rejected: int,
    category_rejected: int,
    kids_rejected: int,
    image_rejected: int,
    url_rejected: int,
    price_rejected: int,
    duplicates_removed: int,
    final_products: int,
    retailers: Any,
    processing_time: float = 0.0
):
    """Outputs standardized [SHOPPING SUMMARY] logging matching Section 38."""
    if isinstance(retailers, (set, list)):
        ret_str = ", ".join(sorted(list(retailers))) if retailers else "None"
    else:
        ret_str = str(retailers)
    _safe_print(
        f"\n[SHOPPING SUMMARY]\n\n"
        f"Requested Gender: {requested_gender}\n"
        f"Requested Category: {requested_category}\n"
        f"Requested Occasion: {requested_occasion}\n"
        f"Requested Season: {requested_season}\n"
        f"Requested Price Range: {requested_price_range}\n\n"
        f"SerpApi Candidates: {candidates}\n"
        f"Gender Rejected: {gender_rejected}\n"
        f"Category Rejected: {category_rejected}\n"
        f"Kids Rejected: {kids_rejected}\n"
        f"Image Rejected: {image_rejected}\n"
        f"Invalid URL: {url_rejected}\n"
        f"Invalid Price: {price_rejected}\n"
        f"Duplicates Removed: {duplicates_removed}\n"
        f"Final Valid Products: {final_products}\n\n"
        f"Retailers: {ret_str}\n"
        f"Average Processing Time: {processing_time:.2f}s\n"
    )



def log_shopping_inventory(
    gender: str,
    skin_tone: str,
    occasion: str,
    season: str,
    price_range: str,
    requested: int,
    candidates: int,
    gender_valid: int,
    dress_valid: int,
    image_valid: int,
    price_valid: int,
    direct_url_valid: int,
    after_dedup: int,
    final_result: int
):
    """Outputs standardized [SHOPPING INVENTORY] diagnostics matching Section 23."""
    _safe_print(
        f"\n[SHOPPING INVENTORY]\n"
        f"Gender: {gender}\n"
        f"Skin Tone: {skin_tone}\n"
        f"Occasion: {occasion}\n"
        f"Season: {season}\n"
        f"Price Range: {price_range}\n"
        f"Requested: {requested}\n\n"
        f"SerpApi Candidates: {candidates}\n"
        f"Gender Valid: {gender_valid}\n"
        f"Dress Valid: {dress_valid}\n"
        f"Image Valid: {image_valid}\n"
        f"Price Valid: {price_valid}\n"
        f"Direct URL Valid: {direct_url_valid}\n"
        f"After Deduplication: {after_dedup}\n\n"
        f"FINAL RESULT: {final_result}"
    )
    if final_result < requested:
        _safe_print(
            f"\n[SHOPPING INVENTORY]\n"
            f"Requested: {requested}\n"
            f"Final genuine products: {final_result}\n"
            f"Status: INSUFFICIENT LIVE INVENTORY"
        )


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
    _quota_exhausted_until: Optional[datetime] = None

    @classmethod
    def mark_quota_exhausted(cls, seconds: int = 300):
        """Activates circuit breaker when SerpApi quota or rate limit is reached."""
        cls._quota_exhausted_until = datetime.utcnow() + timedelta(seconds=seconds)
        print(f"[ShoppingService] SerpApi quota exhausted / rate limited. Circuit breaker active for {seconds}s.")

    @classmethod
    def is_quota_exhausted(cls) -> bool:
        """Returns True if SerpApi searches should be bypassed due to quota exhaustion."""
        if cls._quota_exhausted_until:
            if datetime.utcnow() < cls._quota_exhausted_until:
                return True
            cls._quota_exhausted_until = None
        return False

    def __init__(self):
        self.api_key = os.environ.get('SERPAPI_KEY') or os.environ.get('SERP_API_KEY')
        if not self.api_key:
            from dotenv import load_dotenv
            env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
            if os.path.exists(env_path):
                load_dotenv(env_path, override=True)
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
    def canonicalize_url(raw_url: Optional[str]) -> str:
        return ProductValidator.canonicalize_url(raw_url)

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
            '/search?', '/search/', 'rawquery=', '?q=', '&q=', 'searchterm=', '/s?k='
        ]):
            return False
        # Reject Google Shopping search pages
        if any(gp in u for gp in ['google.com/shopping', 'google.com/search', 'google.com/url?']):
            return False
        # Reject root domain homepages
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.path or parsed.path.strip('/') == '':
                return False
        except Exception:
            pass
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

    # ------------------------------------------------------------------
    # Multi-Query Search Strategy & Parallel Execution (Sections 5, 6, 15)
    # ------------------------------------------------------------------

    def generate_search_passes(
        self,
        norm_gender: str,
        occasion: str,
        season: str,
        palette: List[str],
        price_cue: str = "",
        target_category: str = 'dress',
        retailer: Optional[str] = None
    ) -> List[List[str]]:
        """
        Controlled Multi-Pass Search Expansion using OccasionClassifier query families.
        For female dress requests, uses precision occasion-specific queries so that
        party searches yield party/cocktail/sequin products (not casual/office ones).
        """
        season_term = (season or '').lower()
        if season_term in ('all', ''):
            season_term = ''
        p_cue = price_cue.strip()

        passes = []

        if norm_gender == 'female':
            # PASS 1+2: Occasion-specific precision queries from OccasionClassifier families
            # These are the PRIMARY source of inventory — each query is occasion-targeted.
            occasion_queries = get_occasion_search_queries(
                requested_occasion=occasion,
                season=season_term,
                colors=palette[:3] if palette else [],
                retailer=retailer,
                price_cue=p_cue,
                max_queries=12
            )
            # Split into two passes for progressive loading
            mid = max(2, len(occasion_queries) // 2)
            passes.append([q for q in occasion_queries[:mid] if q])
            passes.append([q for q in occasion_queries[mid:] if q])

            # PASS 3: Skin-tone color + occasion combos
            norm_occ_key = classify_normalize_occasion(occasion)
            p3 = []
            for col in (palette or DEFAULT_SKIN_PALETTE)[:4]:
                q = f"women {col} {norm_occ_key} dress"
                if season_term:
                    q += f" {season_term}"
                if p_cue:
                    q += f" {p_cue}"
                p3.append(q.strip())
            passes.append([q for q in p3 if q])

            # PASS 4: Season-specific synonyms for the occasion
            seas_syns = {
                'spring': ['spring floral dress', 'pastel dress', 'light cotton dress', 'floral midi dress'],
                'summer': ['summer cotton dress', 'linen dress', 'sundress', 'summer maxi dress'],
                'autumn': ['autumn midi dress', 'long sleeve dress', 'fall wrap dress', 'earthy tone dress'],
                'winter': ['winter knit dress', 'sweater dress', 'velvet dress', 'warm midi dress'],
            }.get(season_term, [])
            if seas_syns:
                p4 = [f"women {syn} {norm_occ_key} {p_cue}".strip() for syn in seas_syns[:3]]
                passes.append([q for q in p4 if q])

            # PASS 5: Retailer-targeted occasion queries
            if retailer:
                p5 = [
                    f"{retailer} women {norm_occ_key} dress {p_cue}".strip(),
                    f"{retailer} women dress {p_cue}".strip()
                ]
            else:
                p5 = [
                    f"women {norm_occ_key} dress myntra {p_cue}".strip(),
                    f"women {norm_occ_key} dress amazon india {p_cue}".strip(),
                    f"women {norm_occ_key} dress ajio {p_cue}".strip(),
                    f"women {norm_occ_key} dress tatacliq {p_cue}".strip(),
                ]
            passes.append([q for q in p5 if q])

            # PASS 6: Additional colors from skin-tone palette (broader fallback)
            p6 = [f"women {col} dress {p_cue}".strip() for col in (palette or DEFAULT_SKIN_PALETTE)[4:8]]
            passes.append([q for q in p6 if q])

            # PASS 7: Traditional/ethnic fallback (always valid for dresses)
            p7 = [
                f"women ethnic anarkali dress {norm_occ_key} {p_cue}".strip(),
                f"women kurti dress {norm_occ_key} {p_cue}".strip()
            ]
            passes.append([q for q in p7 if q])

            # PASS 8: Broad dress fallback (last resort)
            p8 = [
                f"women dress online india {p_cue}".strip(),
                f"women stylish dress {p_cue}".strip()
            ]
            passes.append([q for q in p8 if q])

        else:  # Male
            occ_term = OCCASION_SEARCH_MAP.get((occasion or '').lower(), (occasion or '').lower())
            if occ_term == 'all':
                occ_term = ''
            p1 = [f"men {occ_term} casual shirt {season_term} {p_cue}".strip()]
            passes.append(p1)

            p2 = [f"men {col} {occ_term} shirt {p_cue}".strip() for col in (palette or DEFAULT_SKIN_PALETTE)[:4]]
            passes.append(p2)

            p3 = [f"men {st} {occ_term} {p_cue}".strip() for st in ['casual shirt', 'polo t-shirt', 'formal shirt', 'blazer']]
            passes.append(p3)

            p4 = [f"men {occ_term} clothing {season_term} {p_cue}".strip()]
            passes.append(p4)

            p5 = [f"men {season_term} shirt {p_cue}".strip()]
            passes.append(p5)

            p6 = [f"men {col} casual shirt {p_cue}".strip() for col in (palette or DEFAULT_SKIN_PALETTE)[4:8]]
            passes.append(p6)

            if retailer:
                p7 = [f"{retailer} men {occ_term} shirt {p_cue}".strip()]
            else:
                p7 = [f"men {occ_term} shirt {ret} {p_cue}".strip() for ret in ['myntra', 'amazon', 'ajio']]
            passes.append(p7)

            p8 = [f"men {occ_term} menswear {p_cue}".strip()]
            passes.append(p8)

            p9 = [f"men casual clothing india {p_cue}".strip()]
            passes.append(p9)

        return passes

    def generate_multi_queries(
        self,
        norm_gender: str,
        occasion: str,
        season: str,
        skin_palette: List[str],
        target_category: str = 'dress',
        price_cue: str = ""
    ) -> List[str]:
        """
        Builds a multi-query search set flattening passes 1 to 4 for immediate parallel execution.
        """
        passes = self.generate_search_passes(norm_gender, occasion, season, skin_palette, price_cue, target_category)
        queries = []
        for p in passes[:4]:
            queries.extend(p)

        seen = set()
        deduped = []
        for q in queries:
            cleaned = " ".join(q.split())
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                deduped.append(cleaned)
        return deduped

    def generate_broadening_queries(
        self,
        norm_gender: str,
        occasion: str,
        season: str,
        price_cue: str = ""
    ) -> List[str]:
        """Progressive broadening queries (Section 15, Levels 3 & 4) preserving gender and category."""
        occ_term = OCCASION_SEARCH_MAP.get((occasion or '').lower(), (occasion or '').lower())
        if occ_term == 'all':
            occ_term = ''
        season_term = (season or '').lower()
        if season_term in ('all', ''):
            season_term = ''
        p_cue = price_cue.strip()

        broadening = []
        if norm_gender == 'female':
            if occ_term and season_term:
                broadening.append(f"women {occ_term} dress {season_term} {p_cue}".strip())
            if season_term:
                broadening.append(f"women dress {season_term} {p_cue}".strip())
            broadening.append(f"women dress online india {p_cue}".strip())
        else:
            if occ_term and season_term:
                broadening.append(f"men {occ_term} clothing {season_term} {p_cue}".strip())
            broadening.append(f"men casual clothing {p_cue}".strip())
        
        seen = set()
        deduped = []
        for q in broadening:
            cleaned = " ".join(q.split())
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                deduped.append(cleaned)
        return deduped

    def _execute_single_serpapi_query(self, query: str, timeout: int = 5) -> Tuple[str, List[dict]]:
        """Executes a single SerpApi Google Shopping query with timeout and circuit breaker handling."""
        if self.is_quota_exhausted():
            return query, []

        params = {
            'engine': 'google_shopping',
            'q': query,
            'gl': 'in',
            'hl': 'en',
            'api_key': self.api_key,
            'num': 30
        }
        try:
            resp = requests.get(self.base_url, params=params, timeout=timeout)
            if resp.status_code == 429:
                print(f"[ShoppingService] HTTP 429 (quota exhausted) for query '{query}'. Triggering circuit breaker.")
                self.mark_quota_exhausted(300)
                return query, []
            elif resp.ok:
                data = resp.json()
                if data.get('error') and any(err_term in str(data.get('error')).lower() for err_term in ['run out of searches', 'searches depleted', 'quota reached', 'rate limit']):
                    print(f"[ShoppingService] Quota error in SerpApi response: {data.get('error')}. Triggering circuit breaker.")
                    self.mark_quota_exhausted(300)
                    return query, []
                results = data.get('shopping_results', []) or []
                return query, results
            else:
                print(f"[ShoppingService] HTTP {resp.status_code} for query '{query}'")
        except Exception as e:
            print(f"[ShoppingService] Timeout/error querying '{query}': {e}")
        return query, []

    @staticmethod
    def calculate_ranking_score(
        title: str,
        matched_color: bool,
        occasion: str,
        season: str,
        availability: str,
        is_direct: bool,
        retailer_count: int,
        brand: Optional[str]
    ) -> float:
        """
        Calculates recommendation ranking score per Section 24:
        occasion relevance: +25
        season relevance: +20
        skin-tone color match: +20
        availability: +15
        direct product page: +10
        retailer diversity: +5
        brand/quality metadata: +5
        """
        score = 0.0
        t_low = title.lower()
        occ_low = (occasion or '').lower()
        seas_low = (season or '').lower()

        # Occasion relevance: +35 if match, -25 if conflicting
        if occ_low and occ_low != 'all':
            occ_res = OccasionClassifier.classify({'title': title}, occ_low, debug=False)
            if occ_res.decision == 'ACCEPT':
                score += 35.0 * max(0.5, occ_res.confidence)
            elif occ_res.decision == 'SECONDARY':
                score += 15.0 * max(0.3, occ_res.confidence)
            else:
                score -= 25.0
        else:
            score += 10.0

        # Season relevance: +20
        if seas_low and seas_low != 'all':
            seas_res = SeasonClassifier.classify({'title': title}, seas_low, debug=False)
            if seas_res.decision == 'ACCEPT':
                score += 20.0 * max(0.5, seas_res.confidence)
            else:
                score -= 15.0
        else:
            score += 10.0

        # Skin-tone color match: +20
        if matched_color:
            score += 20.0
        else:
            score += 5.0

        # Availability: +15
        if availability == "IN STOCK":
            score += 15.0
        elif availability == "LIMITED":
            score += 10.0

        # Direct product page: +10
        if is_direct:
            score += 10.0

        # Retailer diversity: +5 (if not oversaturated)
        if retailer_count <= 2:
            score += 5.0

        # Brand / quality metadata: +5
        if brand and brand.lower() not in ('online store', 'retailer', ''):
            score += 5.0

        return score

    def _process_candidate_items(
        self,
        raw_items: List[dict],
        norm_gender: str,
        target_category: str,
        req_ret: Optional[str],
        min_p: Optional[float],
        max_p: Optional[float],
        price_label: str,
        occasion: str,
        season: str,
        palette: List[str],
        seen_canonical_ids: set,
        seen_urls: set,
        seen_title_brand_keys: set,
        seen_title_price_keys: set,
        seen_images: set,
        retailer_candidate_counts: dict,
        stats: dict
    ) -> List[dict]:
        """
        Filters and scores raw SerpApi items under strict gender, category, image, URL,
        and price range constraints with Section 37 structured logging.
        """
        accepted_candidates = []

        for it in raw_items:
            stats['candidates'] += 1
            title = (it.get('title') or it.get('name') or '').strip()
            thumbnail = (it.get('thumbnail') or it.get('image') or it.get('image_url') or '').strip()
            price = it.get('extracted_price')
            raw_source = it.get('source') or it.get('store') or it.get('brand') or 'Online Store'
            pre_retailer = self.clean_retailer_name(raw_source)
            det_cat = ProductValidator.detect_category(title, it.get('snippet', ''), it.get('category', ''))
            canonical_id = ProductValidator.extract_canonical_product_id(it, pre_retailer, it.get('link') or it.get('product_url') or '')

            # Basic field presence
            if not title or not thumbnail or price is None:
                stats['category_rejected'] += 1
                log_shopping_filter(title or 'Unknown', pre_retailer, norm_gender, "unknown", target_category, det_cat, price, price_label, decision="REJECT", reason="Missing title, thumbnail, or price", canonical_product_id=canonical_id)
                continue

            # Hard reject mock retailer
            if pre_retailer.lower() == 'aurafit official':
                continue

            # 1. Retailer filter (Section 24)
            ret_ok, _ = validate_retailer(pre_retailer, req_ret)
            if not ret_ok:
                log_shopping_filter(title, pre_retailer, norm_gender, "unknown", target_category, det_cat, price, price_label, decision="REJECT", reason=f"Retailer mismatch ({pre_retailer} != {req_ret})", canonical_product_id=canonical_id)
                continue

            # 2. Strict authentic image validation (Section 12)
            img_ok, img_reason = ProductValidator.validate_image(thumbnail)
            if not img_ok:
                stats['image_rejected'] += 1
                log_shopping_filter(title, pre_retailer, norm_gender, "unknown", target_category, det_cat, price, price_label, decision="REJECT", reason=f"Invalid image: {img_reason}", canonical_product_id=canonical_id)
                continue

            # 3. Strict gender validation (Section 4, 5, 6)
            gender_ok, det_gender, g_reason = ProductValidator.is_gender_compatible(
                product=it,
                target_gender=norm_gender,
                target_category=target_category
            )
            if not gender_ok:
                if det_gender == 'kids':
                    stats['kids_rejected'] += 1
                else:
                    stats['gender_rejected'] += 1
                log_shopping_filter(title, pre_retailer, norm_gender, det_gender, target_category, det_cat, price, price_label, decision="REJECT", reason=g_reason, canonical_product_id=canonical_id)
                continue

            # 4. Strict category validation (Section 7, 8, 9, 10, 11)
            cat_ok, c_reason = ProductValidator.validate_category(
                title_or_product=it,
                target_category=target_category,
                target_gender=norm_gender
            )
            if not cat_ok:
                stats['category_rejected'] += 1
                log_shopping_filter(title, pre_retailer, norm_gender, det_gender, target_category, det_cat, price, price_label, decision="REJECT", reason=c_reason, canonical_product_id=canonical_id)
                continue

            # 4b. Occasion classification (post-retrieval validation)
            # Apply to BOTH genders when occasion is specific (not 'all')
            if occasion and occasion.lower() not in ('all', ''):
                occ_result = OccasionClassifier.classify(it, occasion, debug=False)
                if occ_result.decision == 'REJECT':
                    stats['occasion_rejected'] = stats.get('occasion_rejected', 0) + 1
                    log_shopping_filter(title, pre_retailer, norm_gender, det_gender, target_category, det_cat, price, price_label, decision="REJECT", reason=f"Occasion mismatch: {occ_result.reason}", canonical_product_id=canonical_id)
                    continue

            # 4c. Season classification (post-retrieval validation)
            if season and season.lower() not in ('all', ''):
                seas_result = SeasonClassifier.classify(it, season, debug=False)
                if seas_result.decision == 'REJECT':
                    stats['season_rejected'] = stats.get('season_rejected', 0) + 1
                    log_shopping_filter(title, pre_retailer, norm_gender, det_gender, target_category, det_cat, price, price_label, decision="REJECT", reason=f"Season mismatch: {seas_result.reason}", canonical_product_id=canonical_id)
                    continue

            # 5. Price Range Validation (Section 22)
            live_price = float(price)
            price_ok, p_reason = ProductValidator.validate_price(live_price, min_p, max_p)
            if not price_ok:
                stats['price_rejected'] += 1
                log_shopping_filter(title, pre_retailer, norm_gender, det_gender, target_category, det_cat, live_price, price_label, decision="REJECT", reason=f"Price INR {int(live_price)} not in requested range ({price_label})", canonical_product_id=canonical_id)
                continue

            # 6. Fast direct URL extraction (Section 23)
            cand = self.unwrap_and_clean_url(it.get('link') or it.get('product_link') or it.get('product_url'))
            direct_url = None
            resolved_source = raw_source
            original_price = it.get('extracted_old_price') or it.get('extracted_original_price')

            if cand and self.is_valid_direct_url(cand):
                direct_url = cand
            elif it.get('immersive_product_page_token'):
                store_offer = self.resolve_immersive_store_offer(it)
                if store_offer and store_offer.get('direct_url'):
                    direct_url = store_offer['direct_url']
                    if store_offer.get('price'):
                        live_price = float(store_offer['price'])
                    if store_offer.get('store_name'):
                        resolved_source = store_offer['store_name']
                    if store_offer.get('original_price'):
                        original_price = float(store_offer['original_price'])

            if not direct_url or not self.is_valid_direct_url(direct_url):
                stats['url_rejected'] += 1
                log_shopping_filter(title, pre_retailer, norm_gender, det_gender, target_category, det_cat, live_price, price_label, decision="REJECT", reason="No valid direct retailer URL", canonical_product_id=canonical_id)
                continue

            final_retailer = self.clean_retailer_name(resolved_source)
            if final_retailer.lower() == 'aurafit official':
                continue

            ret_ok2, _ = validate_retailer(final_retailer, req_ret)
            if not ret_ok2:
                continue

            # Re-extract canonical product ID with resolved retailer and direct URL
            canonical_id = ProductValidator.extract_canonical_product_id(it, final_retailer, direct_url)

            # Deduplication Level 1: Canonical Product ID (Section 13 & 14)
            if canonical_id in seen_canonical_ids:
                stats['duplicates_removed'] += 1
                log_shopping_filter(title, final_retailer, norm_gender, det_gender, target_category, det_cat, live_price, price_label, decision="REJECT", reason="Duplicate canonical product ID", canonical_product_id=canonical_id)
                continue

            # Deduplication Level 2: Normalized Direct Product URL (Section 14 & 15)
            canon_url = self.canonicalize_url(direct_url)
            if canon_url in seen_urls:
                stats['duplicates_removed'] += 1
                log_shopping_filter(title, final_retailer, norm_gender, det_gender, target_category, det_cat, live_price, price_label, decision="REJECT", reason="Duplicate canonical direct product URL", canonical_product_id=canonical_id)
                continue

            # Deduplication Level 3: Retailer + Normalized Title + Brand (Section 14 & 16)
            norm_title = ProductValidator.normalize_title(title)
            brand_val = (it.get('brand') or final_retailer or '').strip().lower()
            l3_key = f"{final_retailer.lower()}_{norm_title}_{brand_val}"
            if l3_key in seen_title_brand_keys:
                stats['duplicates_removed'] += 1
                log_shopping_filter(title, final_retailer, norm_gender, det_gender, target_category, det_cat, live_price, price_label, decision="REJECT", reason="Duplicate normalized title and brand for retailer", canonical_product_id=canonical_id)
                continue

            # Deduplication Level 4: Normalized Title + Price + Retailer (Section 14 & 17)
            l4_key = f"{final_retailer.lower()}_{norm_title}_{int(live_price)}"
            if l4_key in seen_title_price_keys:
                stats['duplicates_removed'] += 1
                log_shopping_filter(title, final_retailer, norm_gender, det_gender, target_category, det_cat, live_price, price_label, decision="REJECT", reason="Duplicate normalized title, price and retailer", canonical_product_id=canonical_id)
                continue

            # Deduplication Level 5: Image Fingerprint (Section 14)
            tbn_match = re.search(r'q=tbn:([^&]+)', thumbnail)
            img_key = tbn_match.group(1) if tbn_match else thumbnail.split('?')[0].strip()
            if img_key in seen_images:
                stats['duplicates_removed'] += 1
                log_shopping_filter(title, final_retailer, norm_gender, det_gender, target_category, det_cat, live_price, price_label, decision="REJECT", reason="Duplicate image fingerprint", canonical_product_id=canonical_id)
                continue

            # Availability
            availability = self.parse_availability(it.get('details_and_offers', []), it.get('delivery'))
            if availability == "OUT OF STOCK":
                log_shopping_filter(title, final_retailer, norm_gender, det_gender, target_category, det_cat, live_price, price_label, decision="REJECT", reason="Product is out of stock", canonical_product_id=canonical_id)
                continue

            # Register in all 5 deduplication sets
            seen_canonical_ids.add(canonical_id)
            seen_urls.add(canon_url)
            seen_title_brand_keys.add(l3_key)
            seen_title_price_keys.add(l4_key)
            seen_images.add(img_key)
            stats['retailers'].add(final_retailer)

            # Discount calculation
            discount_str = None
            if original_price and original_price > live_price:
                discount_pct = round((1 - (live_price / original_price)) * 100)
                if discount_pct > 0:
                    discount_str = f"{discount_pct}% OFF"

            # Color matching & palette detection
            matched_color = any(c.lower() in title.lower() for c in palette)
            detected_colors = [c for c in palette if c.lower() in title.lower()]
            if not detected_colors:
                detected_colors = [palette[0]] if palette else ['emerald']

            # Section 24 Candidate Ranking Score
            score = self.calculate_ranking_score(
                title=title,
                matched_color=matched_color,
                occasion=occasion,
                season=season,
                availability=availability,
                is_direct=True,
                retailer_count=retailer_candidate_counts.get(final_retailer, 0),
                brand=it.get('brand')
            )

            retailer_candidate_counts[final_retailer] = retailer_candidate_counts.get(final_retailer, 0) + 1
            candidate_item = {
                'it': it,
                'title': title,
                'canonical_product_id': canonical_id,
                'canonical_url': canon_url,
                'thumbnail': thumbnail,
                'retailer_name': final_retailer,
                'brand': it.get('brand') or final_retailer,
                'final_price': live_price,
                'original_price': original_price,
                'discount_str': discount_str,
                'availability': availability,
                'direct_url': direct_url,
                'det_gender': det_gender,
                'ranking_score': score,
                'colors': detected_colors
            }
            accepted_candidates.append(candidate_item)

            log_shopping_filter(
                title=title,
                retailer=final_retailer,
                requested_gender=norm_gender,
                detected_gender=det_gender,
                requested_category=target_category,
                detected_category=det_cat,
                price=live_price,
                requested_price_range=price_label,
                decision="ACCEPT",
                reason=f"All filters matched (ranking score: {score})",
                canonical_product_id=canonical_id
            )

        return accepted_candidates

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
        limit: int = 25,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        price_range: Optional[str] = None,
        retailer: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches live products from SerpApi Google Shopping using parallel multi-query execution.
        Enforces strict gender validation, category validation, exact-URL verification,
        real price range filtering, and retailer diversity.
        Returns immutable standardized dicts backed by database records.
        """
        import time
        start_time = time.time()

        if not self.is_configured():
            print("[ShoppingService] SERPAPI_KEY is not configured")
            return []

        norm_gender = ProductValidator.normalize_gender(getattr(profile, 'gender', None) if profile else None)
        if norm_gender not in ('female', 'male'):
            norm_gender = 'female'

        min_p, max_p, price_label = parse_price_range(price_range, min_price, max_price)
        req_ret = (retailer or '').strip() if retailer and retailer.lower() not in ('all', 'all retailers', 'none', '') else None
        target_limit = max(15, int(limit or 25))

        skin_tone = (getattr(profile, 'skin_tone', None) or '').lower()
        palette = list(SKIN_TONE_PALETTES.get(skin_tone, DEFAULT_SKIN_PALETTE))
        if compatible_colors:
            for c in compatible_colors:
                if c and c.lower() not in palette:
                    palette.insert(0, c.lower())

        # Structured Log: Shopping Request (Section 27)
        log_shopping_request(
            gender=norm_gender,
            occasion=occasion,
            season=season,
            skin_tone=skin_tone or 'unspecified',
            colors=palette[:5],
            price_range=price_label,
            retailer=req_ret or 'All Retailers',
            target=target_limit
        )

        # Check Cache with full dimension key (Section 42)
        cache_key = f"{norm_gender}:{target_category}:{occasion}:{season}:{skin_tone}:{price_label}:{req_ret or 'all'}:{target_limit}"
        cached = _shopping_cache.get(cache_key)
        if cached:
            print(f"[ShoppingService] Returning {len(cached)} live products from cache ({cache_key})")
            return cached

        # Generate Controlled Multi-Pass Search Sets (Sections 3, 5, 6, 7, 8, 17)
        price_cue = get_price_query_cue(price_range, min_p, max_p)
        search_passes = self.generate_search_passes(
            norm_gender=norm_gender,
            occasion=occasion,
            season=season,
            palette=palette,
            price_cue=price_cue,
            target_category=target_category,
            retailer=req_ret
        )

        stats = {
            'candidates': 0,
            'gender_rejected': 0,
            'category_rejected': 0,
            'occasion_rejected': 0,
            'season_rejected': 0,
            'kids_rejected': 0,
            'image_rejected': 0,
            'url_rejected': 0,
            'price_rejected': 0,
            'duplicates_removed': 0,
            'final_products': 0,
            'retailers': set()
        }

        seen_canonical_ids = set()
        seen_urls = set()
        seen_title_brand_keys = set()
        seen_title_price_keys = set()
        seen_images = set()
        retailer_candidate_counts = {}
        all_candidates = []
        executed_queries_count = 0
        seen_queries = set()

        # Fast circuit breaker check: If SerpApi quota is currently depleted, skip network overhead
        if not self.is_quota_exhausted():
            for pass_idx, pass_queries in enumerate(search_passes, 1):
                if len(all_candidates) >= target_limit:
                    break

                unseen_queries = [q for q in pass_queries if q and q not in seen_queries]
                if not unseen_queries:
                    continue

                for q in unseen_queries:
                    seen_queries.add(q)

                with ThreadPoolExecutor(max_workers=min(4, len(unseen_queries))) as executor:
                    future_to_query = {executor.submit(self._execute_single_serpapi_query, q, 5): q for q in unseen_queries}
                    for future in as_completed(future_to_query):
                        executed_queries_count += 1
                        q = future_to_query[future]
                        try:
                            _, raw_results = future.result()
                        except Exception as e:
                            print(f"[ShoppingService] Query failed '{q}': {e}")
                            raw_results = []

                        candidates_from_query = self._process_candidate_items(
                            raw_items=raw_results,
                            norm_gender=norm_gender,
                            target_category=target_category,
                            req_ret=req_ret,
                            min_p=min_p,
                            max_p=max_p,
                            price_label=price_label,
                            occasion=occasion,
                            season=season,
                            palette=palette,
                            seen_canonical_ids=seen_canonical_ids,
                            seen_urls=seen_urls,
                            seen_title_brand_keys=seen_title_brand_keys,
                            seen_title_price_keys=seen_title_price_keys,
                            seen_images=seen_images,
                            retailer_candidate_counts=retailer_candidate_counts,
                            stats=stats
                        )
                        all_candidates.extend(candidates_from_query)

                        log_shopping_query(
                            query=q,
                            returned=len(raw_results),
                            accepted=len(candidates_from_query),
                            rejected=len(raw_results) - len(candidates_from_query)
                        )

                        if len(all_candidates) >= int(target_limit * 1.5):
                            break

                if len(all_candidates) >= target_limit:
                    break
        else:
            print("[ShoppingService] SerpApi quota circuit breaker active. Bypassing external calls and using authentic live SerpApi database catalog directly.")

        # Resilient live catalog: if candidates are below target_limit,
        # supplement from authentic live SerpApi products previously persisted in the database.
        # Strict validation (gender, category, price range, retailer, image, direct URL, dedup) is STILL enforced identically!
        if len(all_candidates) < target_limit:
            print(f"[ShoppingService] Live queries yielded {len(all_candidates)}/{target_limit}. Supplementing from persisted live SerpApi items under identical strict filters...")
            from models.outfit import Outfit
            db_query = Outfit.query.filter(Outfit.source.like('serpapi%'), Outfit.in_stock == True)
            if req_ret:
                db_query = db_query.filter(Outfit.store.ilike(f"%{req_ret}%"))
            live_db_outfits = db_query.all()
            if live_db_outfits:
                db_raw_items = [
                    {
                        'title': o.name,
                        'thumbnail': o.image_url,
                        'thumbnails': o.additional_images or [],
                        'extracted_price': o.price,
                        'price': f"INR {int(o.price)}" if o.price else None,
                        'extracted_old_price': o.original_price,
                        'source': o.store or o.brand or 'Online Store',
                        'brand': o.brand,
                        'link': o.product_url,
                        'product_id': (o.external_id or '').replace('serpapi_', '').replace('serpapi_sim_', ''),
                        'delivery': 'In Stock',
                        'category': o.category
                    }
                    for o in live_db_outfits
                ]
                db_candidates = self._process_candidate_items(
                    raw_items=db_raw_items,
                    norm_gender=norm_gender,
                    target_category=target_category,
                    req_ret=req_ret,
                    min_p=min_p,
                    max_p=max_p,
                    price_label=price_label,
                    occasion=occasion,
                    season=season,
                    palette=palette,
                    seen_canonical_ids=seen_canonical_ids,
                    seen_urls=seen_urls,
                    seen_title_brand_keys=seen_title_brand_keys,
                    seen_title_price_keys=seen_title_price_keys,
                    seen_images=seen_images,
                    retailer_candidate_counts=retailer_candidate_counts,
                    stats=stats
                )
                all_candidates.extend(db_candidates)

        # Multi-retailer diversification & ranking
        all_candidates.sort(key=lambda x: x['ranking_score'], reverse=True)

        selected_candidates = []
        retailer_pick_counts = {}
        max_per_retailer = max(3, target_limit // 4)

        # Pass 1: Diversify across retailers when "All Retailers" is selected
        for c in all_candidates:
            r = c['retailer_name']
            if not req_ret and retailer_pick_counts.get(r, 0) >= max_per_retailer:
                continue
            selected_candidates.append(c)
            retailer_pick_counts[r] = retailer_pick_counts.get(r, 0) + 1
            if len(selected_candidates) >= target_limit:
                break

        # Pass 2: Backfill from remaining valid ranked candidates if below target_limit
        if len(selected_candidates) < target_limit:
            for c in all_candidates:
                if c in selected_candidates:
                    continue
                selected_candidates.append(c)
                if len(selected_candidates) >= target_limit:
                    break

        # Persist selected candidates and build standardized response (Section 21)
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
            ext_id = self.generate_stable_external_id(it, direct_url, retailer_name, is_similar=False)

            extra_imgs = []
            if isinstance(it.get('thumbnails'), list):
                for t_url in it.get('thumbnails'):
                    if t_url and t_url != thumbnail and ProductValidator.validate_image(t_url)[0]:
                        extra_imgs.append(t_url)

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
                gender=c.get('det_gender') if c.get('det_gender') in ('female', 'male', 'unisex') else norm_gender,
                category=target_category,
                occasion=OccasionClassifier.detect_primary_occasion({'title': title}) or OCCASION_DB_MAP.get(occasion.lower(), 'casual'),
                season=season if season != 'all' else 'all',
                colors=c['colors'],
                additional_images=extra_imgs,
                commit=False
            )

            if outfit_record:
                p_dict = outfit_record.to_dict()
                p_dict['title'] = outfit_record.name
                p_dict['availability'] = availability
                p_dict['canonical_product_id'] = c.get('canonical_product_id', ext_id)
                p_dict['canonical_url'] = c.get('canonical_url', direct_url)
                p_dict['shopping_links'] = { retailer_name.lower().replace(' ', ''): direct_url }
                p_dict['match_score'] = round(c['ranking_score'] / 100.0, 2)
                live_products.append(p_dict)

        # Execute single batch commit for SQLite performance
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[ShoppingService] Batch DB commit error: {e}")

        elapsed_time = time.time() - start_time

        # Structured Log: Shopping Summary (Section 38)
        log_shopping_summary(
            requested_gender=norm_gender,
            requested_category=target_category,
            requested_occasion=occasion,
            requested_season=season,
            requested_price_range=price_label,
            candidates=stats['candidates'],
            gender_rejected=stats['gender_rejected'],
            category_rejected=stats['category_rejected'],
            kids_rejected=stats['kids_rejected'],
            image_rejected=stats['image_rejected'],
            url_rejected=stats['url_rejected'],
            price_rejected=stats['price_rejected'],
            duplicates_removed=stats['duplicates_removed'],
            final_products=len(live_products),
            retailers=stats['retailers'],
            processing_time=elapsed_time
        )

        self.last_stats = dict(stats)
        if live_products:
            _shopping_cache.set(cache_key, live_products)

        return live_products


    # ------------------------------------------------------------------
    # Similar Recommendations Query (Sections 25 & 9)
    # ------------------------------------------------------------------

    def fetch_similar_live_products(
        self,
        main_product: Dict[str, Any],
        profile,
        limit: int = 4,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        price_range: Optional[str] = None,
        retailer: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates a live shopping query based on the main recommended item
        and returns real SerpApi products passing the exact same strict gender,
        dress category, price range, and retailer validation.
        """
        if not self.is_configured():
            return []

        norm_gender = ProductValidator.normalize_gender(main_product.get('gender') or getattr(profile, 'gender', None))
        if norm_gender not in ('female', 'male'):
            norm_gender = 'female'

        color = (main_product.get('colors') or ['emerald'])[0]
        occasion = main_product.get('occasion') or 'party'
        target_category = main_product.get('category') or ('dress' if norm_gender == 'female' else 'casual shirt')

        min_p, max_p, price_label = parse_price_range(price_range, min_price, max_price)
        req_ret = (retailer or '').strip() if retailer and retailer.lower() not in ('all', 'all retailers', 'none', '') else None

        cache_key = f"similar_{norm_gender}_{color}_{occasion}_{target_category}_{min_p}_{max_p}_{req_ret or 'all'}"
        cached = _shopping_cache.get(cache_key)
        if cached:
            return cached

        if norm_gender == 'female':
            similar_query = f"women {color} {occasion} dress".strip()
        else:
            similar_query = f"men {target_category} {color} {occasion}".strip()

        if self.is_quota_exhausted():
            results = []
        else:
            print(f"[ShoppingService] Similar live query: '{similar_query}'")
            _, results = self._execute_single_serpapi_query(similar_query, timeout=4)

        if not results:
            print("[ShoppingService] Similar query returned 0 results. Checking persisted live SerpApi items under strict validation...")
            from models.outfit import Outfit
            db_query = Outfit.query.filter(Outfit.source.like('serpapi%'), Outfit.in_stock == True)
            if req_ret:
                db_query = db_query.filter(Outfit.store.ilike(f"%{req_ret}%"))
            live_db_outfits = db_query.all()
            if live_db_outfits:
                results = [
                    {
                        'title': o.name,
                        'thumbnail': o.image_url,
                        'thumbnails': o.additional_images or [],
                        'extracted_price': o.price,
                        'price': f"INR {int(o.price)}" if o.price else None,
                        'extracted_old_price': o.original_price,
                        'source': o.store or o.brand or 'Online Store',
                        'brand': o.brand,
                        'link': o.product_url,
                        'product_id': (o.external_id or '').replace('serpapi_', '').replace('serpapi_sim_', ''),
                        'delivery': 'In Stock',
                        'category': o.category
                    }
                    for o in live_db_outfits
                ]

        similar_items = []
        seen_sim_urls = set()
        seen_sim_images = set()
        seen_sim_retailers = {}

        main_img = (main_product.get('image_url') or main_product.get('image') or '').strip()
        if main_img:
            tbn_m = re.search(r'q=tbn:([^&]+)', main_img)
            seen_sim_images.add(tbn_m.group(1) if tbn_m else main_img.split('?')[0].strip())

        for it in results:
            title = (it.get('title') or '').strip()
            thumbnail = (it.get('thumbnail') or '').strip()
            price = it.get('extracted_price')
            raw_source = it.get('source') or 'Online Store'
            pre_retailer = self.clean_retailer_name(raw_source)
            det_cat = ProductValidator.detect_category(title, it.get('snippet', ''), it.get('category', ''))

            if not title or not thumbnail or price is None:
                continue
            if it.get('product_id') == main_product.get('external_id') or title.lower() == (main_product.get('title') or '').lower():
                continue
            if pre_retailer.lower() == 'aurafit official':
                continue

            # Strict image deduplication against main item and previous similar items
            tbn_m = re.search(r'q=tbn:([^&]+)', thumbnail)
            sim_img_key = tbn_m.group(1) if tbn_m else thumbnail.split('?')[0].strip()
            if sim_img_key in seen_sim_images:
                continue
            seen_sim_images.add(sim_img_key)

            # 1. Retailer filter
            ret_ok, _ = validate_retailer(pre_retailer, req_ret)
            if not ret_ok:
                continue

            # 2. Strict image validation
            img_ok, _ = ProductValidator.validate_image(thumbnail)
            if not img_ok:
                continue

            # 3. Strict gender validation
            det_gender = detect_product_gender(it)
            gender_ok, det_gender, _ = ProductValidator.is_gender_compatible(
                product=it,
                target_gender=norm_gender,
                target_category=target_category
            )
            if not gender_ok:
                continue

            # 4. Strict category validation
            cat_ok, _ = ProductValidator.validate_category(
                title=title,
                description=it.get('snippet', '') or it.get('description', ''),
                category=it.get('category', ''),
                target_category=target_category,
                target_gender=norm_gender
            )
            if not cat_ok:
                continue

            # 5. Price validation
            live_price = float(price)
            price_ok, _ = validate_price(live_price, min_p, max_p)
            if not price_ok:
                continue

            # 6. Fast direct URL extraction
            cand = self.unwrap_and_clean_url(it.get('link') or it.get('product_link'))
            direct_url = None
            resolved_source = raw_source
            original_price = it.get('extracted_old_price') or it.get('extracted_original_price')

            if cand and self.is_valid_direct_url(cand):
                direct_url = cand
            elif it.get('immersive_product_page_token'):
                store_offer = self.resolve_immersive_store_offer(it)
                if store_offer and store_offer.get('direct_url'):
                    direct_url = store_offer['direct_url']
                    if store_offer.get('price'):
                        live_price = float(store_offer['price'])
                    if store_offer.get('store_name'):
                        resolved_source = store_offer['store_name']
                    if store_offer.get('original_price'):
                        original_price = float(store_offer['original_price'])

            if not direct_url or not self.is_valid_direct_url(direct_url):
                continue
            canon_sim_url = self.canonicalize_url(direct_url)
            if canon_sim_url in seen_sim_urls:
                continue
            seen_sim_urls.add(canon_sim_url)

            final_retailer = self.clean_retailer_name(resolved_source)
            if final_retailer.lower() == 'aurafit official':
                continue

            ret_ok2, _ = validate_retailer(final_retailer, req_ret)
            if not ret_ok2:
                continue

            if not req_ret and seen_sim_retailers.get(final_retailer, 0) >= 2:
                continue
            seen_sim_retailers[final_retailer] = seen_sim_retailers.get(final_retailer, 0) + 1

            discount_str = None
            if original_price and original_price > live_price:
                discount_pct = round((1 - (live_price / original_price)) * 100)
                if discount_pct > 0:
                    discount_str = f"{discount_pct}% OFF"

            sim_ext_id = self.generate_stable_external_id(it, direct_url, final_retailer, is_similar=True)
            outfit_record = self._persist_live_outfit(
                external_id=sim_ext_id,
                title=title,
                brand=it.get('brand') or final_retailer,
                retailer=final_retailer,
                image_url=thumbnail,
                price=live_price,
                original_price=original_price,
                discount=discount_str,
                product_url=direct_url,
                gender=det_gender if det_gender in ('female', 'male', 'unisex') else norm_gender,
                category=target_category,
                occasion=OCCASION_DB_MAP.get(occasion.lower(), 'casual'),
                season='all',
                colors=[color],
                additional_images=it.get('thumbnails') or [],
                commit=False
            )

            if outfit_record:
                sim_dict = outfit_record.to_dict()
                sim_dict['title'] = outfit_record.name
                sim_dict['availability'] = "IN STOCK"
                sim_dict['shopping_links'] = { final_retailer.lower().replace(' ', ''): direct_url }
                similar_items.append(sim_dict)

            if len(similar_items) >= limit:
                break

        # Batch commit similar items
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[ShoppingService] Similar items batch DB commit error: {e}")

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
        discount: Optional[str] = None,
        commit: bool = True
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
                # CRITICAL FIX: Never overwrite existing intrinsic occasion with the requested
                # occasion — this prevents DB corruption when a product is fetched under a
                # different occasion in a later request.
                # Only update occasion if the record has a blank/unknown placeholder.
                if not existing.occasion or existing.occasion in ('', 'all', 'unknown', 'casual') and occasion not in ('', 'all', 'unknown'):
                    existing.occasion = occasion
                existing.season = season
                existing.in_stock = True
                existing.purchasable = True
                existing.source = 'serpapi'
                if commit:
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
            if commit:
                db.session.commit()
            return new_outfit
        except Exception as e:
            db.session.rollback()
            print(f"[ShoppingService] DB save error for {external_id}: {e}")
            return None
