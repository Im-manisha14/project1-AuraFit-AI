"""
AuraFit AI — Dress Style Classifier & Occasion-Style Compatibility Engine
Provides deterministic, request-independent classification of garment styles
and validates mutual compatibility between dress style and requested occasion.

Key Functions:
- classify_dress_style(product) -> Dict[str, Any]
- classify_primary_occasion(product) -> str
- is_style_compatible(product, requested_occasion) -> Tuple[bool, str, str]
- validate_occasion_and_style(product, requested_occasion) -> Tuple[bool, str, Dict[str, Any]]
"""

import re
from typing import Dict, Any, Tuple, List, Optional

# Supported canonical style labels
STYLE_LABELS = [
    'formal',
    'office',
    'casual',
    'party',
    'cocktail',
    'evening',
    'wedding_guest',
    'bridal',
    'traditional',
    'festive',
    'vacation',
    'brunch',
    'dinner',
    'ambiguous',
]

def clean_description(desc: Optional[str]) -> str:
    """Strip synthetic retailer boilerplate prefix while preserving occasion and style descriptors."""
    if not desc:
        return ""
    d = str(desc)
    d = re.sub(r'curated\s+live\s+from\s+[a-z0-9\s\-&]+\.?', ' ', d, flags=re.I)
    d = re.sub(r'live\s+[a-z0-9\s\-&]+\s+in\s+authentic\s+collection\.?', ' ', d, flags=re.I)
    return d.strip()

def build_normalized_text(product: Any) -> str:
    """Concatenate title, description, category, brand, and metadata into lowercase string."""
    if hasattr(product, 'to_dict'):
        p = product.to_dict()
    elif isinstance(product, dict):
        p = product
    else:
        p = {
            'title': getattr(product, 'name', None) or getattr(product, 'title', None),
            'description': getattr(product, 'description', None),
            'brand': getattr(product, 'brand', None),
            'category': getattr(product, 'category', None),
            'product_type': getattr(product, 'category', None),
            'department': getattr(product, 'gender', None),
            'retailer': getattr(product, 'store', None) or getattr(product, 'retailer', None),
        }

    raw_desc = p.get("description") or p.get("snippet") or ""
    clean_desc = clean_description(raw_desc)

    fields = [
        p.get("title") or p.get("name") or "",
        clean_desc,
        p.get("brand") or "",
        p.get("category") or "",
        p.get("product_type") or "",
        p.get("department") or "",
        p.get("retailer") or p.get("store") or p.get("source") or "",
    ]
    raw = " ".join(str(f) for f in fields if f).lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", raw)
    return re.sub(r"\s+", " ", cleaned).strip()


# ---------------------------------------------------------------------------
# Bodycon Classification Logic
# ---------------------------------------------------------------------------
BODYCON_PARTY_PATTERNS = [
    r'\b(club|clubwear|nightclub|night\s*out|bachelorette|prom|party|partywear|nightlife|rave)\b',
    r'\b(mini|micro|micro\s+mini|short\s+mini|ruched\s+mini|slit\s+mini)\b',
    r'\b(cutout|cut-out|plunge|plunging|deep\s+v|backless|sexy|strappy|strapless|halter|bandage)\b',
    r'\b(sequin|sequins|glitter|shimmer|metallic|sparkle|rhinestone|latex|faux\s+leather|mesh|sheer|corset|bustier)\b',
    r'\b(bodycon\s+party|party\s+bodycon|club\s+dress)\b',
]

BODYCON_CASUAL_PATTERNS = [
    r'\b(cotton|ribbed|rib|t-shirt|tee|jersey|everyday|basic|casual|loungewear|simple|stretch\s+casual|tank\s+bodycon|daily\s+wear)\b',
]

BODYCON_STRUCTURED_FORMAL_PATTERNS = [
    r'\b(tailored|structured|formal|sheath|pencil|crepe|ponte|scuba\s+crepe|modest|sophisticated|business\s+formal)\b',
]

BODYCON_STRUCTURED_OFFICE_PATTERNS = [
    r'\b(office|workwear|work\s+dress|corporate|business\s+casual|desk\s+to\s+dinner)\b',
]

def analyze_bodycon(text: str) -> Dict[str, Any]:
    """
    Analyzes whether a bodycon dress is partywear/clubwear, casual loungewear,
    or rare structured formal/office wear.
    """
    if not re.search(r'\bbodycon\b', text):
        return {'is_bodycon': False, 'bodycon_type': 'none', 'evidence': []}

    party_evidence = [p for p in BODYCON_PARTY_PATTERNS if re.search(p, text)]
    casual_evidence = [p for p in BODYCON_CASUAL_PATTERNS if re.search(p, text)]
    formal_evidence = [p for p in BODYCON_STRUCTURED_FORMAL_PATTERNS if re.search(p, text)]
    office_evidence = [p for p in BODYCON_STRUCTURED_OFFICE_PATTERNS if re.search(p, text)]

    # If any party, clubwear, mini, revealing, or glitter signals are present:
    # it is strictly partywear / clubwear
    if party_evidence:
        return {
            'is_bodycon': True,
            'bodycon_type': 'party_club',
            'style': 'party',
            'evidence': [f"party_marker:{e}" for e in party_evidence]
        }

    # If structured/tailored signals exist and NO party/casual markers exist:
    if formal_evidence and not casual_evidence:
        # Check length / modesty
        if re.search(r'\b(midi|knee\s+length|below\s+knee|high\s+neck|boat\s+neck|square\s+neck)\b', text):
            return {
                'is_bodycon': True,
                'bodycon_type': 'structured_formal',
                'style': 'formal',
                'evidence': [f"structured_formal:{e}" for e in formal_evidence]
            }

    if office_evidence and not casual_evidence:
        return {
            'is_bodycon': True,
            'bodycon_type': 'structured_office',
            'style': 'office',
            'evidence': [f"structured_office:{e}" for e in office_evidence]
        }

    # If casual/ribbed/cotton signals exist:
    if casual_evidence:
        return {
            'is_bodycon': True,
            'bodycon_type': 'casual',
            'style': 'casual',
            'evidence': [f"casual_marker:{e}" for e in casual_evidence]
        }

    # Plain / unadorned / generic bodycon without explicit formal tailoring:
    # In retail, unadorned bodycon defaults to party or ambiguous, NEVER formal!
    return {
        'is_bodycon': True,
        'bodycon_type': 'unspecified',
        'style': 'ambiguous',
        'evidence': ['unadorned_bodycon_no_formal_evidence']
    }


# ---------------------------------------------------------------------------
# Style Definitions (Positive & Negative Rule-sets)
# ---------------------------------------------------------------------------
STYLE_TAXONOMY = {
    'formal': {
        'positive': [
            (r'\b(tailored\s+sheath|structured\s+sheath|formal\s+sheath|crepe\s+sheath|ponte\s+sheath)\b', 12),
            (r'\b(formal\s+dress|formal\s+wear|formal\s+midi|formal\s+gown)\b', 12),
            (r'\b(tailored\s+dress|tailored\s+formal|structured\s+formal)\b', 12),
            (r'\b(blazer\s+dress|tailored\s+blazer|pencil\s+dress)\b', 11),
            (r'\b(evening\s+gown|floor\s+length\s+gown|gala\s+gown|black\s+tie)\b', 12),
            (r'\b(sophisticated\s+formal|refined\s+formal|elegant\s+formal)\b', 10),
            (r'\b(business\s+formal|formal\s+event|formal\s+banquet|black\s+tie\s+formal)\b', 10),
            (r'\b(pleated\s+formal\s+midi|scuba\s+crepe\s+formal)\b', 10),
        ],
        'negative': [
            (r'\b(casual|casual\s+wear|everyday|daily\s+wear|relaxed\s+fit|loungewear|lounge\s+wear)\b', -25),
            (r'\b(t-shirt\s+dress|tshirt\s+dress|tee\s+dress|denim\s+dress|shift\s+dress)\b', -25),
            (r'\b(party\s+dress|partywear|party\s+wear|parties|clubwear|club\s+dress|nightclub|bachelorette)\b', -25),
            (r'\b(micro\s+mini|mini\s+dress|ruched\s+mini|cutout|cut-out|backless\s+sexy|plunge)\b', -20),
            (r'\b(sequin|sequins|glitter|shimmer|metallic\s+mini)\b', -20),
            (r'\b(beach\s+dress|beachwear|resort|resort\s*wear|vacation|vacation\s*wear|kaftan|sundress|bohemian|boho)\b', -25),
            (r'\b(anarkali|kurti|kurta|saree|sari|lehenga|salwar|ethnic)\b', -20),
            (r'\b(sleepwear|nightwear|nightdress|bath\s+towel|pyjama)\b', -25),
        ],
        'threshold': 0.50,
    },

    'office': {
        'positive': [
            (r'\b(office\s+dress|office\s+wear|workwear|work\s+dress)\b', 12),
            (r'\b(business\s+casual|professional\s+dress|corporate\s+dress)\b', 12),
            (r'\b(9\s+to\s+5|9-to-5|desk\s+to\s+dinner|meeting\s+dress)\b', 10),
            (r'\b(sheath\s+dress|pencil\s+dress|shirt\s+dress)\b', 9),
            (r'\b(tailored\s+work|modest\s+midi|formal\s+office)\b', 10),
        ],
        'negative': [
            (r'\b(party|partywear|clubwear|nightclub|night\s*out)\b', -15),
            (r'\b(micro\s+mini|backless|sexy|deep\s+v|cutout|cut-out|plunge)\b', -15),
            (r'\b(sequin|sequins|glitter|shimmer)\b', -12),
            (r'\b(beachwear|resort|swim|bikini|cover-up)\b', -15),
            (r'\b(ball\s+gown|black\s+tie\s+gala|evening\s+gown|bridal)\b', -12),
            (r'\b(sleepwear|pyjama)\b', -20),
        ],
        'threshold': 0.45,
    },

    'casual': {
        'positive': [
            (r'\b(casual\s+dress|casual|everyday\s+dress|daily\s+wear)\b', 12),
            (r'\b(cotton\s+casual|simple\s+dress|relaxed\s+fit|comfortable\s+daywear)\b', 10),
            (r'\b(t-shirt\s+dress|tshirt\s+dress|tee\s+dress)\b', 12),
            (r'\b(shirt\s+dress|denim\s+dress|linen\s+dress)\b', 10),
            (r'\b(casual\s+midi|tiered\s+cotton|casual\s+sundress|shift\s+dress)\b', 9),
        ],
        'negative': [
            (r'\b(evening\s+gown|ball\s+gown|formal\s+gown|black\s+tie|gala)\b', -18),
            (r'\b(wedding\s+gown|bridal|bridesmaid)\b', -15),
            (r'\b(clubwear|nightclub|party\s+mini|sequin\s+dress|glitter)\b', -15),
            (r'\b(formal\s+sheath|tailored\s+formal|business\s+formal)\b', -12),
            (r'\b(anarkali|kurti|saree|lehenga)\b', -15),
        ],
        'threshold': 0.45,
    },

    'party': {
        'positive': [
            (r'\b(party\s+dress|partywear|party\s+wear|parties|night\s*out)\b', 12),
            (r'\b(clubwear|nightclub|club\s+dress|bachelorette|prom\s+dress)\b', 12),
            (r'\b(sequin|sequins|glitter|shimmer|metallic\s+dress)\b', 12),
            (r'\b(satin\s+mini|velvet\s+mini|ruched\s+mini|cutout\s+dress|bandage\s+dress)\b', 11),
            (r'\b(cocktail\s+dress|statement\s+dress|glam|glamorous)\b', 10),
        ],
        'negative': [
            (r'\b(office\s+dress|workwear|corporate|business\s+formal|9\s+to\s+5)\b', -15),
            (r'\b(t-shirt\s+dress|cotton\s+simple|daily\s+casual|sleepwear)\b', -15),
            (r'\b(formal\s+sheath|pencil\s+office)\b', -12),
            (r'\b(anarkali|kurti|saree|lehenga)\b', -15),
        ],
        'threshold': 0.45,
    },

    'cocktail': {
        'positive': [
            (r'\b(cocktail\s+dress|cocktail\s+party|cocktail|cocktails)\b', 14),
            (r'\b(midi\s+cocktail|mini\s+cocktail|satin\s+cocktail|off-shoulder\s+cocktail)\b', 12),
            (r'\b(evening\s+party|chic\s+cocktail|semi-formal\s+party)\b', 10),
        ],
        'negative': [
            (r'\b(office\s+uniform|corporate\s+workwear|business\s+formal)\b', -12),
            (r'\b(t-shirt\s+dress|cotton\s+casual|daily\s+wear|denim)\b', -15),
            (r'\b(gymwear|sleepwear|bridal\s+gown)\b', -15),
        ],
        'threshold': 0.45,
    },

    'evening': {
        'positive': [
            (r'\b(evening\s+dress|evening\s+gown|evening\s+wear|after\s+dark)\b', 14),
            (r'\b(black\s+tie|gala\s+gown|floor\s+length\s+gown|dinner\s+party\s+dress)\b', 12),
            (r'\b(velvet\s+evening|satin\s+evening|sophisticated\s+maxi)\b', 10),
        ],
        'negative': [
            (r'\b(casual\s+cotton|t-shirt|beachwear|sportswear|sleepwear)\b', -15),
            (r'\b(office\s+uniform|work\s+shirt)\b', -10),
        ],
        'threshold': 0.45,
    },

    'wedding_guest': {
        'positive': [
            (r'\b(wedding\s+guest|wedding\s+guest\s+dress|wedding\s+reception|reception\s+dress)\b', 14),
            (r'\b(bridesmaid\s+dress|bridesmaid|wedding\s+ceremony\s+dress)\b', 12),
            (r'\b(wedding\s+attendee|chiffon\s+wedding\s+guest|silk\s+wedding\s+guest)\b', 11),
            (r'\b(wedding\s+occasion|celebratory\s+wedding)\b', 10),
        ],
        'negative': [
            (r'\b(bridal\s+gown|wedding\s+gown\s+for\s+bride|bride\s+to\s+be|white\s+bridal|bridal\s+trousseau)\b', -20),
            (r'\b(clubwear|nightclub|micro\s+mini|t-shirt\s+dress|casual\s+cotton)\b', -15),
            (r'\b(office\s+workwear|corporate)\b', -12),
        ],
        'threshold': 0.45,
    },

    'bridal': {
        'positive': [
            (r'\b(bridal\s+gown|wedding\s+gown|bridal\s+dress|bride\s+dress)\b', 15),
            (r'\b(white\s+wedding\s+gown|bridal\s+trousseau|bridal\s+lehenga|bridal\s+saree)\b', 14),
            (r'\b(wedding\s+dress\s+for\s+bride|bridal\s+collection)\b', 12),
        ],
        'negative': [
            (r'\b(wedding\s+guest|bridesmaid|guest\s+wear)\b', -15),
            (r'\b(office|casual|clubwear)\b', -15),
        ],
        'threshold': 0.50,
    },

    'traditional': {
        'positive': [
            (r'\b(traditional|ethnic|ethnic\s+dress|indian\s+wear)\b', 12),
            (r'\b(anarkali|anarkalis|kurti|kurtis|kurta|saree|sari|sarees|lehenga|salwar)\b', 14),
            (r'\b(dupatta|handloom|chanderi|silk\s+saree|bandhani|kalamkari)\b', 10),
            (r'\b(indo\s+western|cultural\s+wear)\b', 9),
        ],
        'negative': [
            (r'\b(western\s+mini|western\s+clubwear|t-shirt|denim\s+dress)\b', -15),
            (r'\b(nightclub|sleepwear|activewear)\b', -15),
        ],
        'threshold': 0.50,
    },

    'festive': {
        'positive': [
            (r'\b(festive|festive\s+wear|festival|celebration\s+dress)\b', 12),
            (r'\b(diwali|navratri|eid|embellished\s+ethnic|zari|mirror\s+work|resham)\b', 12),
            (r'\b(shimmer\s+festive|ornate\s+festive|festive\s+anarkali)\b', 10),
        ],
        'negative': [
            (r'\b(office\s+uniform|plain\s+corporate|gymwear|plain\s+cotton\s+casual)\b', -15),
            (r'\b(sleepwear|pyjama)\b', -15),
        ],
        'threshold': 0.45,
    },

    'vacation': {
        'positive': [
            (r'\b(vacation\s+dress|vacation|resort\s+wear|resort\s+dress|holiday\s+dress)\b', 12),
            (r'\b(tropical\s+dress|tropical\s+maxi|kaftan|caftan|breezy\s+sundress)\b', 11),
            (r'\b(bohemian\s+dress|travel\s+dress|linen\s+vacation|beach\s+vacation)\b', 10),
        ],
        'negative': [
            (r'\b(office\s+dress|sheath\s+dress|business\s+suit|corporate)\b', -15),
            (r'\b(black\s+tie|formal\s+gown|evening\s+gown|clubwear)\b', -12),
        ],
        'threshold': 0.45,
    },

    'brunch': {
        'positive': [
            (r'\b(brunch\s+dress|brunch|daytime\s+chic|day\s+dress\s+brunch)\b', 12),
            (r'\b(floral\s+midi|wrap\s+dress\s+floral|fit\s+and\s+flare\s+floral|pastel\s+sundress)\b', 10),
            (r'\b(garden\s+party|daytime\s+event\s+dress)\b', 9),
        ],
        'negative': [
            (r'\b(nightclub|clubwear|black\s+tie|business\s+suit|sleepwear)\b', -15),
        ],
        'threshold': 0.45,
    },

    'dinner': {
        'positive': [
            (r'\b(dinner\s+dress|dinner\s+date|dining\s+dress|restaurant\s+dress)\b', 12),
            (r'\b(satin\s+slip\s+dress|cowl\s+neck\s+slip|sophisticated\s+wrap\s+dress)\b', 10),
            (r'\b(evening\s+dinner|chic\s+dinner)\b', 9),
        ],
        'negative': [
            (r'\b(sportswear|activewear|gym|casual\s+t-shirt|beachwear)\b', -15),
        ],
        'threshold': 0.45,
    },

    'date': {
        'positive': [
            (r'\b(date\s+night|date\s+dress|romantic\s+dress|dinner\s+date)\b', 12),
            (r'\b(slip\s+dress|cowl\s+neck|sweetheart\s+neckline|romantic\s+wrap)\b', 11),
            (r'\b(satin\s+slip|velvet\s+slip|flattering\s+date)\b', 10),
        ],
        'negative': [
            (r'\b(office\s+uniform|corporate\s+workwear|gymwear|sleepwear)\b', -15),
        ],
        'threshold': 0.45,
    },
}


# ---------------------------------------------------------------------------
# Style-Occasion Compatibility Matrix
# ---------------------------------------------------------------------------
STYLE_OCCASION_COMPATIBILITY = {
    'formal': {
        'compatible_styles': {'formal'},
        'disallowed_styles': {'party', 'casual', 'office', 'cocktail', 'vacation', 'brunch', 'bridal', 'traditional', 'festive', 'ambiguous'},
        'allow_evening_gown': True,
    },
    'office': {
        'compatible_styles': {'office'},
        'disallowed_styles': {'formal', 'party', 'casual', 'cocktail', 'vacation', 'brunch', 'bridal', 'traditional', 'festive', 'ambiguous'},
    },
    'casual': {
        'compatible_styles': {'casual'},
        'disallowed_styles': {'formal', 'office', 'party', 'cocktail', 'evening', 'wedding_guest', 'bridal', 'traditional', 'festive', 'ambiguous'},
    },
    'party': {
        'compatible_styles': {'party', 'cocktail'},
        'disallowed_styles': {'formal', 'office', 'casual', 'traditional', 'festive', 'bridal', 'ambiguous'},
    },
    'cocktail': {
        'compatible_styles': {'cocktail', 'party'},
        'disallowed_styles': {'formal', 'office', 'casual', 'traditional', 'festive', 'bridal', 'ambiguous'},
    },
    'wedding': {
        'compatible_styles': {'wedding_guest', 'traditional', 'festive'},
        'disallowed_styles': {'bridal', 'casual', 'office', 'party', 'clubwear', 'ambiguous'},
    },
    'date': {
        'compatible_styles': {'date', 'dinner', 'evening'},
        'disallowed_styles': {'office', 'casual', 'sports', 'bridal', 'ambiguous'},
    },
    'evening': {
        'compatible_styles': {'evening', 'formal', 'dinner'},
        'disallowed_styles': {'casual', 'sports', 'beachwear', 'office', 'ambiguous'},
    },
    'dinner': {
        'compatible_styles': {'dinner', 'date', 'evening'},
        'disallowed_styles': {'casual', 'sports', 'beachwear', 'office', 'ambiguous'},
    },
    'traditional': {
        'compatible_styles': {'traditional', 'festive'},
        'disallowed_styles': {'casual', 'formal', 'party', 'cocktail', 'western', 'ambiguous'},
    },
    'festive': {
        'compatible_styles': {'festive', 'traditional'},
        'disallowed_styles': {'casual', 'office', 'sports', 'ambiguous'},
    },
    'vacation': {
        'compatible_styles': {'vacation', 'brunch'},
        'disallowed_styles': {'formal', 'office', 'evening', 'black tie', 'ambiguous'},
    },
    'brunch': {
        'compatible_styles': {'brunch', 'casual'},
        'disallowed_styles': {'formal', 'black tie', 'clubwear', 'nightclub', 'ambiguous'},
    },
}


# ---------------------------------------------------------------------------
# Core Classification Functions
# ---------------------------------------------------------------------------

def classify_dress_style(product: Any) -> Dict[str, Any]:
    """
    Classify a dress's inherent style deterministically and independently of any request.
    Returns:
    {
        'style': 'formal' | 'office' | 'casual' | 'party' | 'cocktail' | 'evening' |
                 'wedding_guest' | 'bridal' | 'traditional' | 'festive' | 'vacation' |
                 'brunch' | 'dinner' | 'ambiguous',
        'confidence': float,
        'evidence': List[str],
        'is_bodycon': bool,
        'bodycon_type': 'none' | 'party_club' | 'casual' | 'structured_formal' | 'structured_office' | 'unspecified',
        'scores': Dict[str, float]
    }
    """
    text = build_normalized_text(product)
    if not text:
        return {
            'style': 'ambiguous',
            'confidence': 0.0,
            'evidence': ['empty_text'],
            'is_bodycon': False,
            'bodycon_type': 'none',
            'scores': {}
        }

    # 1. Specialized Bodycon Analysis
    bodycon_info = analyze_bodycon(text)
    if bodycon_info['is_bodycon']:
        b_type = bodycon_info['bodycon_type']
        if b_type == 'party_club':
            return {
                'style': 'party',
                'confidence': 0.90,
                'evidence': bodycon_info['evidence'],
                'is_bodycon': True,
                'bodycon_type': b_type,
                'scores': {'party': 15.0}
            }
        elif b_type == 'casual':
            return {
                'style': 'casual',
                'confidence': 0.85,
                'evidence': bodycon_info['evidence'],
                'is_bodycon': True,
                'bodycon_type': b_type,
                'scores': {'casual': 12.0}
            }
        elif b_type == 'structured_formal':
            return {
                'style': 'formal',
                'confidence': 0.85,
                'evidence': bodycon_info['evidence'],
                'is_bodycon': True,
                'bodycon_type': b_type,
                'scores': {'formal': 12.0}
            }
        elif b_type == 'structured_office':
            return {
                'style': 'office',
                'confidence': 0.85,
                'evidence': bodycon_info['evidence'],
                'is_bodycon': True,
                'bodycon_type': b_type,
                'scores': {'office': 12.0}
            }
        elif b_type == 'unspecified':
            # Unadorned bodycon without explicit formal markers cannot be accepted as formal
            return {
                'style': 'party',
                'confidence': 0.60,
                'evidence': ['unadorned_bodycon_default_party'],
                'is_bodycon': True,
                'bodycon_type': b_type,
                'scores': {'party': 8.0}
            }

    # 2. General Style Scoring across STYLE_TAXONOMY
    scores = {}
    evidence_map = {}

    for style_name, rules in STYLE_TAXONOMY.items():
        pos_score = 0.0
        neg_score = 0.0
        ev = []

        for pat, weight in rules['positive']:
            m = re.search(pat, text)
            if m:
                pos_score += weight
                ev.append(f"+{weight}:{m.group(0)}")

        for pat, weight in rules['negative']:
            m = re.search(pat, text)
            if m:
                neg_score += abs(weight)
                ev.append(f"-{abs(weight)}:{m.group(0)}")

        net = max(0.0, pos_score - neg_score)
        scores[style_name] = net
        if ev:
            evidence_map[style_name] = ev

    # Find top scoring style
    sorted_styles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_style, best_score = sorted_styles[0] if sorted_styles else ('ambiguous', 0.0)

    # Confidence calculation
    confidence = min(1.0, best_score / 15.0) if best_score > 0 else 0.0
    threshold = STYLE_TAXONOMY.get(best_style, {}).get('threshold', 0.45)

    if best_score < 4.0 or confidence < threshold:
        final_style = 'ambiguous'
        confidence = max(0.0, round(confidence, 2))
    else:
        final_style = best_style
        confidence = round(confidence, 2)

    return {
        'style': final_style,
        'confidence': confidence,
        'evidence': evidence_map.get(final_style, []),
        'is_bodycon': bodycon_info['is_bodycon'],
        'bodycon_type': bodycon_info['bodycon_type'],
        'scores': scores
    }


def classify_primary_occasion(product: Any) -> str:
    """
    Returns the single primary occasion key for the product.
    Independent of requested occasion.
    """
    from services.occasion_classifier import OccasionClassifier
    return OccasionClassifier.detect_primary_occasion(product)


def is_style_compatible(product: Any, requested_occasion: str) -> Tuple[bool, str, str]:
    """
    Validates whether the product's garment style is appropriate for the requested occasion.
    Returns:
    (is_compatible: bool, detected_style: str, reason: str)
    """
    req_occ = (requested_occasion or '').lower().strip()
    style_info = classify_dress_style(product)
    det_style = style_info['style']
    b_type = style_info.get('bodycon_type', 'none')

    compat_rules = STYLE_OCCASION_COMPATIBILITY.get(req_occ)
    if not compat_rules:
        # Default lenient pass if requested occasion not in strict compatibility table
        return True, det_style, f"Style '{det_style}' accepted (no specific rule for occasion '{req_occ}')"

    # Explicit rejection of ambiguous dresses for high-stakes occasions
    if det_style == 'ambiguous' and req_occ in ('formal', 'office', 'wedding'):
        return False, det_style, f"Ambiguous dress style cannot be verified for strict '{req_occ}' occasion"

    # Specific Formal Occasion Safeguards:
    if req_occ == 'formal':
        text = build_normalized_text(product)
        # 1. Reject products explicitly described as casual, beachwear, resort wear, vacation wear, clubwear, partywear, or loungewear
        disallowed_casual_party = [
            r'\b(casual|casual\s+wear|everyday|daily\s+wear|loungewear|lounge\s+wear|t-shirt\s+dress|tee\s+dress)\b',
            r'\b(beach|beachwear|resort\s*wear|vacation\s*wear|sundress|boho|bohemian|holiday\s+wear)\b',
            r'\b(clubwear|nightclub|club\s+dress|partywear|party\s+wear|night\s*out|bachelorette|rave)\b',
            r'\b(sleepwear|nightwear|nightdress|pyjama|gymwear|activewear)\b',
        ]
        has_casual_or_party = any(re.search(pat, text) for pat in disallowed_casual_party)

        # 2. Require positive evidence of formal/business suitability
        positive_formal_patterns = [
            r'\b(formal|formal\s+wear|formal\s+dress|formal\s+midi|formal\s+gown|evening\s+gown|floor\s+length\s+gown|black\s+tie|gala)\b',
            r'\b(tailored|structured|blazer\s+dress|pencil\s+dress|business\s+formal|tailored\s+sheath|structured\s+sheath|crepe\s+sheath|ponte\s+sheath)\b',
        ]
        has_positive_formal = any(re.search(pat, text) for pat in positive_formal_patterns)

        if has_casual_or_party and re.search(r'\b(casual|casual\s+wear|loungewear|lounge\s+wear|beachwear|resort\s*wear|clubwear|sleepwear)\b', text):
            return False, det_style, f"Product explicitly described as casual/beach/club/loungewear cannot be classified as Formal"

        if has_casual_or_party and not has_positive_formal:
            return False, det_style, f"Rejected casual/party/resort garment without independent formal suitability for 'formal'"

        if not has_positive_formal:
            return False, det_style, f"Rejected dress for Formal: lacks required positive formal/tailored/structured evidence (found '{det_style}')"

        if style_info.get('is_bodycon') and b_type != 'structured_formal':
            return False, det_style, f"Rejected bodycon style '{b_type}' for Formal (only structured/tailored bodycon permitted)"

    # Specific Office Bodycon Safeguard:
    if req_occ == 'office' and style_info.get('is_bodycon'):
        if b_type not in ('structured_office', 'structured_formal'):
            return False, det_style, f"Rejected bodycon style '{b_type}' for Office (only structured work bodycon permitted)"

    # Check allowed styles
    allowed = compat_rules.get('compatible_styles', set())
    disallowed = compat_rules.get('disallowed_styles', set())

    # Evening gown special allowance for Formal
    if req_occ == 'formal' and compat_rules.get('allow_evening_gown'):
        if det_style == 'evening':
            text = build_normalized_text(product)
            if re.search(r'\b(gown|floor\s+length|black\s+tie|gala)\b', text):
                return True, det_style, f"Evening gown style '{det_style}' accepted for Formal (black tie/gala)"

    if det_style in disallowed:
        return False, det_style, f"Incompatible dress style '{det_style}' for requested occasion '{req_occ}'"

    if det_style in allowed:
        return True, det_style, f"Dress style '{det_style}' matches requested occasion '{req_occ}'"

    # If not explicitly allowed
    return False, det_style, f"Dress style '{det_style}' is not certified compatible with '{req_occ}'"


def validate_occasion_and_style(product: Any, requested_occasion: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Enforces BOTH validations:
    1. Occasion compatibility
    2. Dress-style compatibility

    Returns:
    (is_valid: bool, reason: str, details: Dict[str, Any])
    """
    req_occ = (requested_occasion or '').lower().strip()
    if not req_occ or req_occ in ('all', 'trending', 'seasonal', 'skin_tone', 'body_shape'):
        return True, "No specific occasion requested", {}

    from services.occasion_classifier import OccasionClassifier, normalize_occasion

    norm_occ = normalize_occasion(req_occ)

    # 1. Classify dress style independently
    style_info = classify_dress_style(product)
    style_ok, det_style, style_reason = is_style_compatible(product, norm_occ)

    if not style_ok:
        return False, f"Style rejected: {style_reason}", {
            'style_info': style_info,
            'detected_style': det_style,
            'requested_occasion': norm_occ
        }

    # 2. Classify occasion independently
    occ_res = OccasionClassifier.classify(product, norm_occ, debug=False)
    primary_occ, best_score = OccasionClassifier.detect_primary_occasion_with_score(product)

    if occ_res.decision == 'REJECT':
        return False, f"Occasion rejected: {occ_res.reason}", {
            'style_info': style_info,
            'occasion_res': occ_res,
            'primary_occasion': primary_occ,
            'requested_occasion': norm_occ
        }

    # 3. Occasion Exclusivity Check
    if norm_occ in ('party', 'casual', 'formal', 'office', 'wedding', 'vacation', 'sports', 'date', 'brunch', 'dinner', 'cocktail', 'traditional', 'festive'):
        alias_groups = [
            {'party', 'cocktail'},
            {'traditional', 'festive'},
            {'evening', 'dinner'},
        ]
        is_alias = any(norm_occ in g and primary_occ in g for g in alias_groups)
        if primary_occ != norm_occ and not is_alias:
            return False, f"Occasion mismatch: Primary occasion '{primary_occ}' does not match requested '{norm_occ}'", {
                'style_info': style_info,
                'primary_occasion': primary_occ,
                'requested_occasion': norm_occ
            }

    return True, "Occasion and dress style both verified", {
        'style_info': style_info,
        'detected_style': det_style,
        'primary_occasion': primary_occ,
        'requested_occasion': norm_occ,
        'confidence': min(style_info['confidence'], occ_res.confidence)
    }
