"""
AuraFit AI — Single Authoritative Production Product Validator
Single source of truth for live product validation, normalization, and deduplication.
Every candidate product must pass validate_live_product() before entering:
- POST /api/recommendations/generate
- GET /api/recommendations/collections
- Similar recommendations
- Persisted live-product records
- Final API responses
"""

import re
import urllib.parse
from typing import Dict, Any, Optional, Set, Tuple, List

from services.occasion_classifier import (
    OccasionClassifier,
    SeasonClassifier,
    normalize_occasion,
    normalize_season,
    build_normalized_product_text
)
from services.product_contract import (
    format_recommendation_contract,
    parse_discount_value
)

# ---------------------------------------------------------------------------
# Tracking Parameter Stripping & Canonicalization
# ---------------------------------------------------------------------------
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'srsltid', 'gclid', 'fbclid', 'ref', 'ref_', 'tag', 'psc', 'qid', 'sr_',
    'ie', 'keywords', 'sprefix', 'crid', 'pd_rd_w', 'pd_rd_r', 'pd_rd_wg',
    'pf_rd_p', 'pf_rd_r', 'pf_rd_s', 'pf_rd_t', 'pf_rd_i', 'pf_rd_m',
    'storecontext', 'th'
}

def canonicalize_url(url: Optional[str]) -> str:
    """Normalize direct retailer product URL and strip all tracking/query noise."""
    if not url or not isinstance(url, str):
        return ""
    u = url.strip()
    if not (u.startswith('http://') or u.startswith('https://')):
        return ""
    try:
        parsed = urllib.parse.urlparse(u)
        q_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_params = [
            (k, v) for k, v in q_params
            if k.lower() not in TRACKING_PARAMS and not k.lower().startswith('utm_') and not k.lower().startswith('ref')
        ]
        new_query = urllib.parse.urlencode(cleaned_params)
        canon = urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower().replace('www.', ''),
            parsed.path.rstrip('/'),
            '',
            new_query,
            ''
        ))
        return canon
    except Exception:
        return u.split('?')[0].rstrip('/')

def normalize_title(title: Optional[str]) -> str:
    """Normalize title for duplicate detection."""
    if not title:
        return ""
    t = str(title).lower().strip()
    # Strip common size/variant tails
    t = re.sub(r'[\(\[\{].*?[\)\]\}]', ' ', t)
    t = re.sub(r'\b(size|sz)\s*[:\-]?\s*[a-z0-9]+\b', ' ', t)
    t = re.sub(r'\b(xs|s|m|l|xl|xxl|2xl|3xl|free size)\b', ' ', t)
    t = re.sub(r'\b(by|at)\s+(myntra|amazon|flipkart|ajio|tatacliq|nykaa)\b', ' ', t)
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def extract_image_key(img_url: Optional[str]) -> str:
    """Extract canonical image identifier (handles Google thumbnail q=tbn: keys)."""
    if not img_url or not isinstance(img_url, str):
        return ""
    u = img_url.strip()
    m = re.search(r'q=tbn:([^&]+)', u)
    if m:
        return m.group(1).strip()
    return u.split('?')[0].strip()

def clean_retailer_name(raw: Optional[str]) -> str:
    """Clean and standardize retailer name."""
    if not raw:
        return "Online Store"
    r = str(raw).strip()
    r_lower = r.lower()
    if 'myntra' in r_lower: return 'Myntra'
    if 'amazon' in r_lower: return 'Amazon'
    if 'ajio' in r_lower: return 'AJIO'
    if 'flipkart' in r_lower: return 'Flipkart'
    if 'nykaa' in r_lower: return 'Nykaa'
    if 'zara' in r_lower: return 'Zara'
    if 'h&m' in r_lower or 'hm.com' in r_lower: return 'H&M'
    if 'pantaloons' in r_lower: return 'Pantaloons'
    if 'tatacliq' in r_lower or 'tata cliq' in r_lower: return 'Tata CLiQ'
    if 'savana' in r_lower: return 'Savana'
    if 'newme' in r_lower: return 'NEWME'
    if 'vero moda' in r_lower: return 'Vero Moda'
    if 'shein' in r_lower: return 'Shein India'
    if 'forever 21' in r_lower: return 'Forever 21'
    if 'urbanic' in r_lower: return 'Urbanic'
    if 'snitch' in r_lower: return 'Snitch'
    if 'marks & spencer' in r_lower or 'marks and spencer' in r_lower: return 'Marks & Spencer'
    if 'bewakoof' in r_lower: return 'Bewakoof'
    if 'koovs' in r_lower: return 'Koovs'
    # Strip url junk
    r = re.sub(r'\.(com|in|co\.in|org|net)$', '', r, flags=re.I)
    return r.title() if len(r) > 1 else "Online Store"

def canonical_product_key(product: Any) -> str:
    """
    Step 3: One Canonical Product Identity function.
    Priority:
    1. external_id (normalized, stripping any 'sim_' prefix variance)
    2. retailer + canonical product URL
    3. retailer + product ID
    4. retailer + normalized brand + normalized title
    5. normalized brand + normalized title
    """
    if hasattr(product, 'to_dict'):
        p = product.to_dict()
    elif isinstance(product, dict):
        p = product
    else:
        return ""

    retailer = clean_retailer_name(
        p.get('retailer') or p.get('store') or p.get('source') or p.get('brand') or ''
    ).lower()

    # 1. external_id
    ext_id = str(p.get('external_id') or '').strip().lower()
    if ext_id and ext_id not in ('none', 'null', ''):
        # Normalize serpapi_sim_ -> serpapi_
        norm_ext = re.sub(r'^serpapi_sim_', 'serpapi_', ext_id)
        if norm_ext and norm_ext != 'serpapi_':
            return f"ext:{norm_ext}"

    # 2. retailer + canonical product URL
    raw_url = str(p.get('product_url') or p.get('shopping_url') or p.get('link') or '').strip()
    canon_u = canonicalize_url(raw_url)
    if canon_u:
        return f"url:{retailer}:{canon_u}"

    # 3. retailer + product ID
    prod_id = str(p.get('product_id') or p.get('id') or '').strip()
    if prod_id and prod_id not in ('none', 'null', '', '0'):
        return f"pid:{retailer}:{prod_id}"

    # 4 & 5. retailer + normalized brand + normalized title
    title = str(p.get('title') or p.get('name') or '').strip()
    norm_t = normalize_title(title)
    brand = str(p.get('brand') or '').strip().lower()
    norm_b = re.sub(r'[^a-z0-9]', '', brand)

    if retailer and norm_b and norm_t:
        return f"rbt:{retailer}:{norm_b}:{norm_t}"
    if retailer and norm_t:
        return f"rt:{retailer}:{norm_t}"
    if norm_b and norm_t:
        return f"bt:{norm_b}:{norm_t}"
    if norm_t:
        return f"t:{norm_t}"

    return ""

# ---------------------------------------------------------------------------
# Strict Category Rules (Phase 4)
# ---------------------------------------------------------------------------
FALSE_DRESS_PATTERNS = [
    r'\bdress\s+shirt\b',
    r'\bdress\s+shoes?\b',
    r'\bdress\s+socks?\b',
    r'\bdress\s+material\b',
    r'\bdress\s+fabric\b',
    r'\bdress\s+pattern\b',
    r'\bdress\s+watch(es)?\b',
    r'\bdress\s+belt\b',
    r'\bdress\s+pumps?\b',
    r'\bdress\s+sandals?\b',
    r'\bdress\s+boots?\b',
]

FORBIDDEN_FEMALE_DRESS_PATTERNS = [
    # Footwear
    (r'\b(shoes?|sneakers?|heels?|sandals?|boots?|flats?|slippers?|footwear|loafers?|oxfords?|pumps?|wedges?|stilettos?|juttis?|kolhapuris?)\b', 'shoes'),
    # Bags & Accessories
    (r'\b(handbags?|bags?|totes?|clutch(es)?|wallets?|backpacks?|purses?|sling\s+bag|shoulder\s+bag|potli)\b', 'bags'),
    (r'\b(jeweller?y|earrings?|necklaces?|bracelets?|bangles?|pendants?|anklets?|rings?|chains?|mangalsutra|jhumkas?)\b', 'jewellery'),
    (r'\b(watches?|wristwatches?|timepiece|sunglasses?|shades|eyewear|spectacles|goggles)\b', 'accessories'),
    (r'\b(belts?|scarf|scarves|stoles?|shawls?|hats?|caps?|hair\s+accessories|hairband)\b', 'accessories'),
    # Cosmetics & Fragrance
    (r'\b(cosmetics?|perfumes?|fragrance|makeup|lipstick|eyeliner|eau\s+de\s+parfum|cologne)\b', 'cosmetics'),
    # Separates
    (r'\b(skirts?|mini\s+skirt|midi\s+skirt|pleated\s+skirt|pencil\s+skirt)\b', 'skirts'),
    (r'\b(trousers?|pants?|jeans?|denims?|shorts?|leggings?|jeggings?|palazzos?|culottes?|cargos?|joggers?|trackpants?)\b', 'pants'),
    (r'\b(tops?|crop\s+top|tank\s+top|shirts?|blouses?|t-shirts?|tees?|tunics?|camisoles?|sweaters?|cardigans?|hoodies?|sweatshirts?)\b', 'tops'),
    (r'\b(jackets?|blazers?|coats?|shrugs?|capes?|waistcoats?|overcoats?|windcheater|trench\s+coat)\b', 'jackets'),
    # Nightwear & Lingerie
    (r'\b(lingerie|bras?|panties?|briefs?|underwear|sleepwear|nightwear|nighty|nightdress|pajamas?|pyjamas?|bathrobes?|towels?)\b', 'sleepwear'),
    # Fabric/Material
    (r'\b(dress\s+material|unstitched|fabric|cloth\s+piece|running\s+material|sewing)\b', 'fabric'),
]

ACCEPTED_DRESS_PATTERNS = [
    r'\b(dress|dresses)\b',
    r'\b(gown|gowns)\b',
    r'\b(kurti|kurtis|kurta|kurtas)\b',
    r'\b(saree|sari|sarees|saris)\b',
    r'\b(anarkali|anarkalis)\b',
    r'\b(lehenga|lehengas)\b',
    r'\b(salwar\s+suit|salwar\s+kameez)\b',
    r'\b(jumpsuit|jumpsuits|romper|rompers)\b',
]

MENSWEAR_FORBIDDEN = [
    r'\b(women|women\'s|womens|woman|ladies|lady|girls|girl|womenswear|dress|gown|saree|kurti|anarkali|lehenga|bra|skirt)\b'
]

MENSWEAR_ACCEPTED = [
    r'\b(shirt|shirts|casual\s+shirt|formal\s+shirt|t-shirt|tshirt|tee|polo)\b',
    r'\b(blazer|blazers|suit|suits|tuxedo|coat|jacket|jackets)\b',
    r'\b(trouser|trousers|pant|pants|jeans|denim|chinos|shorts|cargo)\b',
    r'\b(kurta|kurtas|sherwani|nehru\s+jacket|bandhgala|ethnic\s+wear)\b',
    r'\b(sweater|sweatshirt|hoodie|cardigan|pullover|vest)\b',
    r'\b(tracksuit|activewear|sportswear|jersey)\b',
]

def check_category_suitability(
    product_dict: Dict[str, Any],
    target_gender: str = 'female',
    target_category: str = 'dress'
) -> Tuple[bool, str, str]:
    """
    Returns (is_valid, detected_category, reason)
    Phase 4: Strict category enforcement.
    """
    t = f"{product_dict.get('title', '')} {product_dict.get('description', '')} {product_dict.get('category', '')}".lower()

    if target_gender == 'female' and target_category == 'dress':
        # 1. False dress keyword check (Phase 4)
        for fdp in FALSE_DRESS_PATTERNS:
            m = re.search(fdp, t)
            if m:
                return False, 'false_dress', f"Rejected false dress pattern ({m.group(0)})"

        # 2. Check forbidden categories
        # Exception: if title clearly has an accepted dress keyword, check if forbidden word is secondary
        has_allowed_dress = any(re.search(pat, t) for pat in ACCEPTED_DRESS_PATTERNS)
        for pat, cat_name in FORBIDDEN_FEMALE_DRESS_PATTERNS:
            m = re.search(pat, t)
            if m:
                # If it's a "shirt dress", that's allowed!
                if cat_name == 'tops' and re.search(r'\bshirt\s+dress\b', t):
                    continue
                # If it contains both dress and shoes/bags/etc., it's almost always shoes or bag
                return False, cat_name, f"Forbidden non-dress category detected ({m.group(0)} - {cat_name})"

        # 3. Must match at least one allowed dress pattern
        if has_allowed_dress:
            return True, 'dress', 'Valid female dress'

        return False, 'non_dress', 'Title does not match any accepted female dress category'

    elif target_gender == 'male':
        # Check forbidden women's terms
        for exp in MENSWEAR_FORBIDDEN:
            m = re.search(exp, t)
            if m:
                return False, 'womenswear_in_male', f"Opposite gender term detected in menswear ({m.group(0)})"
        # Check approved menswear
        for mp in MENSWEAR_ACCEPTED:
            m = re.search(mp, t)
            if m:
                return True, 'menswear', 'Valid menswear category'
        return False, 'unapproved_menswear', 'Does not match approved menswear categories'

    return True, 'clothing', 'Category accepted'

# ---------------------------------------------------------------------------
# Strict Gender Rules (Phase 3)
# ---------------------------------------------------------------------------
def check_gender_suitability(
    product_dict: Dict[str, Any],
    target_gender: str = 'female',
    target_category: str = 'dress'
) -> Tuple[bool, str, str]:
    """
    Returns (is_compatible, detected_gender, reason)
    Phase 3: Gender must be strict and from the shopping product.
    """
    t = f"{product_dict.get('title', '')} {product_dict.get('description', '')} {product_dict.get('category', '')} {product_dict.get('product_url', '')}".lower()

    if target_gender == 'female':
        # Hard reject opposite gender: male evidence
        # Use negative lookbehind to ensure "women" is not matched by "men"
        male_pattern = r'(?<!wo)(?<!wo-)\b(men|men\'s|mens|man|boys|boy|menswear|male)\b'
        m = re.search(male_pattern, t)
        if m:
            return False, 'male', f"Hard reject opposite gender (male) evidence: '{m.group(0)}'"

        # Look for female signals
        female_pattern = r'\b(women|women\'s|womens|woman|female|ladies|lady|girls|girl|womenswear|female\s+clothing)\b'
        if re.search(female_pattern, t):
            return True, 'female', 'Strong female evidence found'

        # If target_category is dress and it is an actual dress, accept as female
        if target_category == 'dress':
            is_dress, _, _ = check_category_suitability(product_dict, 'female', 'dress')
            if is_dress:
                return True, 'female', 'Dress inherently female in catalog'

        return False, 'unknown_gender', 'Insufficient female evidence on product'

    elif target_gender == 'male':
        # Hard reject opposite gender: female evidence
        female_pattern = r'\b(women|women\'s|womens|woman|female|ladies|lady|girls|girl|womenswear|female\s+clothing|dress|gown|saree|kurti|anarkali|lehenga)\b'
        m = re.search(female_pattern, t)
        if m:
            return False, 'female', f"Hard reject opposite gender (female) evidence: '{m.group(0)}'"

        # Look for male signals
        male_pattern = r'(?<!wo)(?<!wo-)\b(men|men\'s|mens|man|boys|boy|menswear|male)\b'
        if re.search(male_pattern, t):
            return True, 'male', 'Strong male evidence found'

        return False, 'unknown_gender', 'Insufficient male evidence on product'

    return True, 'unisex', 'Gender unconstrained'

# ---------------------------------------------------------------------------
# Strict Price Range Rules (Phase 17)
# ---------------------------------------------------------------------------
PRICE_RANGES = {
    'under_500':   (0.0, 500.0),
    '500_1000':    (500.0, 1000.0),
    '1000_2000':   (1000.0, 2000.0),
    '1000_2500':   (1000.0, 2500.0),
    '2000_3000':   (2000.0, 3000.0),
    '2500_5000':   (2500.0, 5000.0),
    '3000_5000':   (3000.0, 5000.0),
    '5000_10000':  (5000.0, 10000.0),
    '5000_plus':   (5000.0, float('inf')),
    'above_10000': (10000.0, float('inf')),
}

def check_price_suitability(
    price: float,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    price_range: Optional[str] = None
) -> Tuple[bool, str]:
    """Validate extracted current selling price against range filters."""
    if price <= 0:
        return False, "Price must be greater than zero"

    min_p, max_p = None, None
    if price_range and price_range.lower() in PRICE_RANGES:
        min_p, max_p = PRICE_RANGES[price_range.lower()]
    if price_min is not None:
        min_p = float(price_min)
    if price_max is not None:
        max_p = float(price_max)

    if min_p is not None and price < min_p:
        return False, f"Price INR {price:.1f} is below minimum INR {min_p:.1f}"
    if max_p is not None and price > max_p:
        return False, f"Price INR {price:.1f} is above maximum INR {max_p:.1f}"

    return True, "Price in valid range"

# ---------------------------------------------------------------------------
# Single Authoritative Production Validator (Phase 2)
# ---------------------------------------------------------------------------
def validate_live_product(
    candidate: Any,
    profile: Optional[Any] = None,
    requested_gender: Optional[str] = None,
    requested_category: Optional[str] = None,
    requested_occasion: Optional[str] = None,
    requested_season: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    price_range: Optional[str] = None,
    retailer: Optional[str] = None,
    seen_identity_keys: Optional[Set[str]] = None,
    seen_urls: Optional[Set[str]] = None,
    seen_images: Optional[Set[str]] = None,
    occasion_registry: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    ONE authoritative production function: validate_live_product(candidate, profile).
    Enforces all checks:
    - Normalization
    - Phase 13: Live SerpApi product integrity (no mock, no placeholder)
    - Phase 9: Authentic image validation
    - Phase 10 & 11: Exact canonical identity & deduplication
    - Phase 3: Strict gender validation
    - Phase 4: Strict category validation (real dresses for female)
    - Phase 5 & 6: Occasion validation & primary occasion exclusivity
    - Phase 7: Season validation
    - Phase 17: Price filter
    - Retailer filter
    - Phase 12: Cross-occasion duplicate protection
    - Phase 18: Response contract construction

    Returns:
    {
        "accepted": True / False,
        "reason": "...",
        "normalized_product": {...} or None
    }
    """
    # 1. Normalize candidate input
    if hasattr(candidate, 'to_dict'):
        c = candidate.to_dict()
    elif isinstance(candidate, dict):
        c = dict(candidate)
    else:
        return {"accepted": False, "reason": "Candidate must be dict or Outfit model", "normalized_product": None}

    title = (c.get('title') or c.get('name') or '').strip()
    if not title or len(title) < 4:
        return {"accepted": False, "reason": "Missing or empty product title", "normalized_product": None}

    # 2. Phase 13: Live Product Integrity
    # If source exists, it must start with serpapi
    src = (c.get('source') or '').strip().lower()
    if src and not src.startswith('serpapi'):
        return {"accepted": False, "reason": f"Disallowed non-live or mock source: '{src}'", "normalized_product": None}

    # Reject AuraFit Official or mock stores
    raw_retailer = (c.get('store') or c.get('retailer') or c.get('source') or c.get('brand') or 'Online Store').strip()
    clean_ret = clean_retailer_name(raw_retailer)
    if clean_ret.lower() == 'aurafit official':
        return {"accepted": False, "reason": "Disallowed mock retailer 'AuraFit Official'", "normalized_product": None}

    # Retailer filter check
    if retailer and retailer.lower() not in ('all', 'all retailers', 'none', ''):
        req_ret_clean = clean_retailer_name(retailer).lower()
        if req_ret_clean not in clean_ret.lower() and clean_ret.lower() not in req_ret_clean:
            return {"accepted": False, "reason": f"Retailer mismatch (got {clean_ret}, requested {retailer})", "normalized_product": None}

    # 3. Phase 9: Authentic Image Validation
    img_url = (c.get('image_url') or c.get('image') or c.get('thumbnail') or '').strip()
    if not img_url or not (img_url.startswith('http://') or img_url.startswith('https://')):
        return {"accepted": False, "reason": "Invalid or missing image URL protocol", "normalized_product": None}
    
    img_lower = img_url.lower()
    disallowed_img_markers = [
        'aurafit.store', 'example.com', 'placeholder', 'dummy', 'unsplash',
        'default_avatar', 'no-image', '1v2w3', '1mo2p', '61j7k', 't67u1a',
        'test_img', 'mock', 'sample', 'image_unavailable', 'broken'
    ]
    if any(bad in img_lower for bad in disallowed_img_markers):
        return {"accepted": False, "reason": "Disallowed placeholder/mock/dummy image URL", "normalized_product": None}

    img_key = extract_image_key(img_url)
    if seen_images is not None and img_key:
        if img_key in seen_images:
            return {"accepted": False, "reason": "Duplicate image URL detected", "normalized_product": None}

    # 4. Direct Retailer URL Extraction & Validation
    prod_url = (c.get('product_url') or c.get('shopping_url') or c.get('link') or '').strip()
    if not prod_url or not (prod_url.startswith('http://') or prod_url.startswith('https://')):
        return {"accepted": False, "reason": "Invalid or missing direct product URL", "normalized_product": None}

    p_lower = prod_url.lower()
    if any(sp in p_lower for sp in ['/search', 'rawquery=', 'searchterm=', 'google.com/url', 'google.com/search']):
        return {"accepted": False, "reason": "Disallowed search/query result URL", "normalized_product": None}

    canon_url = canonicalize_url(prod_url)
    if seen_urls is not None and canon_url:
        if canon_url in seen_urls:
            return {"accepted": False, "reason": "Duplicate canonical product URL", "normalized_product": None}

    # Deterministic Identity Key (Phase 10 & 11, Step 3 & 4)
    norm_t = normalize_title(title)
    brand_title_key = f"{clean_ret}:{norm_t}"
    identity_key = f"{clean_ret}:{c.get('external_id') or canon_url or norm_t}"
    canon_prod_key = canonical_product_key(c)

    if seen_identity_keys is not None:
        if canon_prod_key and canon_prod_key in seen_identity_keys:
            return {"accepted": False, "reason": f"Duplicate canonical product key: {canon_prod_key}", "normalized_product": None}
        if identity_key in seen_identity_keys:
            return {"accepted": False, "reason": "Duplicate product identity key", "normalized_product": None}
        if brand_title_key in seen_identity_keys:
            return {"accepted": False, "reason": "Duplicate retailer + normalized title", "normalized_product": None}
        if norm_t in seen_identity_keys:
            return {"accepted": False, "reason": "Duplicate normalized title", "normalized_product": None}

    # 5. Phase 3: Strict Gender Validation
    target_g = requested_gender or (getattr(profile, 'gender', None) if profile else None) or c.get('gender') or 'female'
    norm_target_g = 'male' if 'male' in target_g.lower() and 'female' not in target_g.lower() else 'female'

    target_c = requested_category or ('dress' if norm_target_g == 'female' else 'clothing')
    g_ok, det_g, g_reason = check_gender_suitability(c, norm_target_g, target_c)
    if not g_ok:
        return {"accepted": False, "reason": f"Gender rejected: {g_reason}", "normalized_product": None}

    # 6. Phase 4: Strict Category Validation
    c_ok, det_c, c_reason = check_category_suitability(c, norm_target_g, target_c)
    if not c_ok:
        return {"accepted": False, "reason": f"Category rejected: {c_reason}", "normalized_product": None}

    # 7. Phase 5 & 6: Occasion Validation & Primary Occasion Exclusivity
    norm_occ = normalize_occasion(requested_occasion) if requested_occasion else 'all'
    primary_occ, best_score = OccasionClassifier.detect_primary_occasion_with_score(c)
    occ_res = None
    occ_conf = 0.85

    if norm_occ and norm_occ not in ('all', 'trending', 'seasonal', 'skin_tone', 'body_shape', 'minimalist'):
        occ_res = OccasionClassifier.classify(c, norm_occ, debug=False)
        occ_conf = occ_res.confidence

        # Phase 6 & Phase 5: Occasion must match product intrinsic occasion
        if occ_res.decision == 'REJECT':
            return {"accepted": False, "reason": f"Occasion mismatch: {occ_res.reason}", "normalized_product": None}

        # Primary Occasion Exclusivity: Distinct occasions cannot cross-contaminate
        if norm_occ in ('party', 'casual', 'formal', 'office', 'wedding', 'vacation', 'sports', 'date', 'brunch', 'dinner', 'cocktail', 'traditional'):
            if primary_occ != norm_occ:
                if primary_occ == 'casual' and norm_occ in ('party', 'formal', 'office', 'wedding'):
                    return {
                        "accepted": False,
                        "reason": f"Occasion mismatch: Casual dress cannot appear under {norm_occ} (primary_occasion=casual)",
                        "normalized_product": None
                    }
                if primary_occ in ('party', 'cocktail') and norm_occ in ('casual', 'formal', 'office', 'sports'):
                    return {
                        "accepted": False,
                        "reason": f"Occasion mismatch: Party/cocktail dress cannot appear under {norm_occ} (primary_occasion={primary_occ})",
                        "normalized_product": None
                    }
                if best_score >= 8.0 and best_score > (occ_res.confidence * 16.0 * 1.05):
                    return {
                        "accepted": False,
                        "reason": f"Occasion mismatch: Primary intrinsic occasion is '{primary_occ}' (score {best_score:.1f} vs requested {norm_occ})",
                        "normalized_product": None
                    }

    # Phase 12: Cross-occasion duplicate protection
    if occasion_registry is not None and norm_occ not in ('all', 'trending', 'seasonal', 'skin_tone', 'body_shape'):
        registered_occ = occasion_registry.get(identity_key) or (occasion_registry.get(canon_url) if canon_url else None) or (occasion_registry.get(img_key) if img_key else None)
        if registered_occ and registered_occ != norm_occ:
            return {
                "accepted": False,
                "reason": f"Cross-occasion violation: Product already registered for '{registered_occ}', cannot appear in '{norm_occ}'",
                "normalized_product": None
            }

    # 8. Phase 7: Season Validation
    norm_seas = normalize_season(requested_season) if requested_season else 'all'
    seas_conf = 0.80
    if norm_seas and norm_seas != 'all':
        seas_res = SeasonClassifier.classify(c, norm_seas, debug=False)
        seas_conf = seas_res.confidence
        if seas_res.decision == 'REJECT':
            return {"accepted": False, "reason": f"Season mismatch: {seas_res.reason}", "normalized_product": None}

    # 9. Phase 17: Strict Price Validation
    try:
        raw_p = c.get('price') or c.get('extracted_price') or 0.0
        price_val = float(raw_p)
    except (ValueError, TypeError):
        price_val = 0.0

    p_ok, p_reason = check_price_suitability(price_val, price_min, price_max, price_range)
    if not p_ok:
        return {"accepted": False, "reason": f"Price rejected: {p_reason}", "normalized_product": None}

    # 10. Extract / Build Original Price & Discount
    raw_orig = c.get('original_price') or c.get('extracted_old_price') or c.get('extracted_original_price')
    try:
        orig_val = float(raw_orig) if raw_orig is not None else None
    except (ValueError, TypeError):
        orig_val = None
    if orig_val is not None and orig_val <= price_val:
        orig_val = None

    discount_val = c.get('discount')
    if not discount_val and orig_val and orig_val > price_val:
        pct = int(round((1.0 - (price_val / orig_val)) * 100.0))
        discount_val = f"{pct}% OFF"

    # Register into tracking sets if provided
    if seen_identity_keys is not None:
        if canon_prod_key:
            seen_identity_keys.add(canon_prod_key)
        seen_identity_keys.add(identity_key)
        seen_identity_keys.add(brand_title_key)
        seen_identity_keys.add(norm_t)
    if seen_urls is not None and canon_url:
        seen_urls.add(canon_url)
    if seen_images is not None and img_key:
        seen_images.add(img_key)
    if occasion_registry is not None and norm_occ not in ('all', 'trending', 'seasonal', 'skin_tone', 'body_shape'):
        assigned_occ = norm_occ or primary_occ
        if canon_prod_key:
            occasion_registry[canon_prod_key] = assigned_occ
        occasion_registry[identity_key] = assigned_occ
        if canon_url:
            occasion_registry[canon_url] = assigned_occ
        if img_key:
            occasion_registry[img_key] = assigned_occ

    # 11. Phase 18: Build Standardized Contract Product
    ext_id = (c.get('external_id') or f"serpapi_{c.get('id') or identity_key}").strip()
    raw_colors = c.get('colors') or []
    if isinstance(raw_colors, str):
        colors = [col.strip() for col in raw_colors.split(',') if col.strip()]
    elif isinstance(raw_colors, list):
        colors = [str(col).strip() for col in raw_colors if col]
    else:
        colors = []

    normalized_p = {
        'id': int(c.get('id') or 1),
        'external_id': ext_id,
        'title': title,
        'name': title,
        'gender': norm_target_g,
        'category': det_c,
        'occasion': primary_occ if (norm_occ in ('all', 'trending', 'seasonal', 'skin_tone', 'body_shape')) else norm_occ,
        'season': norm_seas,
        'style_type': c.get('style_type') or primary_occ or 'casual',
        'brand': c.get('brand') or clean_ret,
        'retailer': clean_ret,
        'store': clean_ret,
        'price': price_val,
        'currency': c.get('currency') or 'INR',
        'original_price': orig_val,
        'discount': str(discount_val) if discount_val else None,
        'availability': 'IN STOCK',
        'is_live': True,
        'is_purchasable': True,
        'in_stock': True,
        'image_url': img_url,
        'additional_images': c.get('additional_images') or [],
        'product_url': prod_url,
        'shopping_url': prod_url,
        'exact_product_link_available': True,
        'colors': colors,
        'description': c.get('description') or f"Live {clean_ret} {det_c} in authentic collection.",
        'match_score': c.get('match_score') or 0.95,
        'primary_occasion': primary_occ,
        'occasion_confidence': round(occ_conf, 2),
        'season_confidence': round(seas_conf, 2),
        'gender_confidence': 1.0,
        'category_confidence': 1.0,
        'image_valid': True,
        'product_identity_key': canon_prod_key or identity_key,
        'canonical_product_key': canon_prod_key or identity_key,
        'canonical_url': canon_url,
    }

    # Wrap in format_recommendation_contract
    formatted_contract = format_recommendation_contract(
        item=normalized_p,
        fallback_gender=norm_target_g,
        fallback_category=det_c,
        fallback_occasion=normalized_p['occasion'],
        fallback_season=norm_seas,
        overall_score=normalized_p['match_score']
    )
    # Ensure all extra contract fields are preserved
    formatted_contract['primary_occasion'] = primary_occ
    formatted_contract['occasion_confidence'] = round(occ_conf, 2)
    formatted_contract['season_confidence'] = round(seas_conf, 2)
    formatted_contract['gender_confidence'] = 1.0
    formatted_contract['category_confidence'] = 1.0
    formatted_contract['image_valid'] = True
    formatted_contract['product_identity_key'] = canon_prod_key or identity_key
    formatted_contract['canonical_product_key'] = canon_prod_key or identity_key
    formatted_contract['canonical_url'] = canon_url

    return {
        "accepted": True,
        "reason": "All production validation checks passed",
        "normalized_product": formatted_contract
    }
