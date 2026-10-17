"""
AuraFit AI -- Centralized Occasion and Season Classifier
Single source of truth for product occasion and season classification.

Implements:
  - OccasionClassifier.classify(product) -> OccasionResult
  - SeasonClassifier.classify(product)   -> SeasonResult
  - OccasionProfile taxonomy (18+ occasions)
  - Weighted positive/negative signal scoring
  - Multi-label compatible_occasions
  - Debug-friendly structured logging
  - Occasion-specific search query generation
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from services.dress_style_classifier import (
    classify_dress_style,
    is_style_compatible,
    validate_occasion_and_style,
)


class OccasionDecision:
    SUITABLE = "SUITABLE"
    UNSUITABLE = "UNSUITABLE"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class ThreeStateOccasionResult:
    """Three-state occasion decision per Phase 3 requirement."""
    status: str  # SUITABLE | UNSUITABLE | UNCERTAIN
    occasion: str
    confidence: float
    evidence_strength: float
    primary_occasion: str
    positive_signals: List[str]
    negative_signals: List[str]
    reason: str


@dataclass
class OccasionResult:
    """Full classification result for one product / one requested occasion."""
    occasion: str
    confidence: float
    primary_occasion: str
    compatible_occasions: List[str]
    positive_signals: List[str]
    negative_signals: List[str]
    evidence: List[str]
    decision: str  # ACCEPT | SECONDARY | REJECT
    reason: str
    three_state_decision: str = "UNCERTAIN"


@dataclass
class SeasonResult:
    """Full classification result for season."""
    season: str
    confidence: float
    detected_season: str
    compatible_seasons: List[str]
    positive_signals: List[str]
    negative_signals: List[str]
    decision: str  # ACCEPT | REJECT
    reason: str


OCCASION_TAXONOMY = {
    "party": {
        "aliases": ["party", "partywear", "party wear", "parties", "prom",
                    "new year", "birthday", "bachelorette", "nightlife", "club", "clubwear"],
        "positive": [
            ("party", 10), ("partywear", 10), ("party wear", 10), ("cocktail", 9),
            ("sequin", 10), ("sequins", 10), ("glitter", 9), ("shimmer", 9),
            ("metallic", 8), ("satin mini", 8), ("velvet mini", 8), ("embellished", 7),
            ("bodycon party", 10), ("ruched mini", 8), ("nightclub", 9), ("club dress", 9),
            ("glam", 8), ("glamorous", 8), ("statement mini", 8),
        ],
        "negative": [
            ("office", -10), ("workwear", -10), ("work dress", -10), ("business", -10),
            ("daily wear", -10), ("casual", -8), ("t-shirt dress", -10), ("cotton simple", -8),
            ("anarkali", -10), ("kurti", -10), ("saree", -10), ("formal sheath", -8),
        ],
        "strong_combos": [
            ("sequin", "dress"), ("party", "mini"), ("glitter", "dress"),
            ("metallic", "dress"), ("club", "dress"), ("cocktail", "dress"),
        ],
        "hard_rejects": [
            "sleepwear", "pyjama", "nightwear", "office uniform", "workwear",
            "anarkali", "kurti", "saree", "lehenga", "salwar", "t-shirt dress",
            "daily casual", "linen tiered", "formal sheath", "casual cotton"
        ],
        "threshold": 0.45,
    },
    "casual": {
        "aliases": ["casual", "everyday", "daily", "day dress", "day out",
                    "daywear", "regular", "basics", "lounge"],
        "positive": [
            ("casual", 10), ("everyday", 9), ("day dress", 9), ("daily wear", 9),
            ("cotton casual", 9), ("t-shirt dress", 9), ("shirt dress", 8),
            ("denim dress", 9), ("relaxed fit", 8), ("simple dress", 8),
            ("casual midi", 8), ("tiered cotton", 8),
        ],
        "negative": [
            ("sequin", -12), ("glitter", -12), ("metallic", -10), ("cocktail", -10),
            ("party", -10), ("evening gown", -12), ("ball gown", -12), ("formal gown", -12),
            ("clubwear", -12), ("nightclub", -12), ("backless sexy", -10),
            ("anarkali", -10), ("saree", -10), ("lehenga", -10), ("formal sheath", -10),
        ],
        "strong_combos": [
            ("cotton", "casual"), ("denim", "dress"), ("everyday", "dress"),
            ("t-shirt", "dress"), ("shirt", "dress"),
        ],
        "hard_rejects": [
            "sequin", "glitter", "metallic", "evening gown", "ball gown", "clubwear",
            "nightwear", "anarkali", "saree", "lehenga", "formal gown", "formal sheath", "black tie"
        ],
        "threshold": 0.45,
    },
    "date": {
        "aliases": ["date", "date night", "dinner date", "romantic", "romance", "date wear"],
        "positive": [
            ("date night", 12), ("romantic", 10), ("dinner date", 10), ("slip dress", 10),
            ("cowl neck", 9), ("sweetheart", 9), ("romantic wrap", 9), ("satin slip", 10),
            ("velvet slip", 9), ("lace slip", 9), ("dinner dress", 8),
        ],
        "negative": [
            ("office", -10), ("workwear", -10), ("corporate", -10), ("gym", -10),
            ("t-shirt dress", -10), ("anarkali", -10), ("kurti", -10), ("casual cotton", -8),
            ("clubwear", -6),
        ],
        "strong_combos": [
            ("date", "dress"), ("slip", "satin"), ("romantic", "dress"),
            ("cowl", "neck"), ("dinner", "dress"),
        ],
        "hard_rejects": ["anarkali", "kurti", "t-shirt dress", "gymwear", "sleepwear", "sports jersey"],
        "threshold": 0.45,
    },
    "wedding": {
        "aliases": ["wedding", "wedding guest", "wedding reception", "wedding ceremony",
                    "bridesmaid", "engagement", "bridal", "reception", "anniversary"],
        "positive": [
            ("wedding guest", 12), ("wedding", 10), ("bridesmaid", 11), ("reception", 9),
            ("anarkali", 10), ("lehenga", 10), ("saree", 10), ("chiffon gown", 9),
            ("silk gold zari", 10), ("embroidered gown", 10), ("traditional maxi", 9),
        ],
        "negative": [
            ("mini dress", -12), ("short dress", -10), ("clubwear", -12), ("casual", -10),
            ("t-shirt", -12), ("crop", -10), ("workwear", -10), ("beach", -10),
        ],
        "strong_combos": [
            ("wedding", "gown"), ("anarkali", "gown"), ("zari", "saree"),
            ("embroidered", "gown"), ("bridesmaid", "dress"),
        ],
        "hard_rejects": ["mini dress", "short dress", "clubwear", "nightwear", "gymwear", "t-shirt dress", "casual", "daily wear"],
        "threshold": 0.45,
    },
    "formal": {
        "aliases": ["formal", "formal wear", "gala", "black tie",
                    "evening gown", "business formal"],
        "positive": [
            ("tailored sheath", 12), ("formal sheath", 12), ("structured sheath", 12),
            ("crepe sheath", 10), ("ponte sheath", 10),
            ("formal", 10), ("formal wear", 12), ("formal dress", 12), ("formal midi", 12),
            ("formal gown", 12), ("evening gown", 12), ("gala", 10), ("black tie", 12),
            ("tailored formal", 12), ("structured formal", 12), ("floor length gown", 10),
            ("sophisticated formal", 10), ("blazer dress", 12), ("pencil dress", 10),
            ("business formal", 12), ("pleated formal", 10),
        ],
        "negative": [
            ("casual", -25), ("casual wear", -25), ("daily wear", -25), ("regular fit", -15), ("everyday", -20),
            ("t-shirt", -25), ("beach", -25), ("vacation", -25), ("resort", -25), ("boho", -20),
            ("mini dress", -15), ("clubwear", -25), ("nightclub", -25), ("party", -20),
            ("partywear", -25), ("party wear", -25), ("cocktail", -15),
            ("sequin", -15), ("glitter", -15), ("shimmer", -15),
            ("loungewear", -25), ("lounge wear", -25), ("sleepwear", -25),
            ("anarkali", -15), ("kurti", -15), ("saree", -15), ("lehenga", -15), ("salwar", -15), ("ethnic", -12),
        ],
        "strong_combos": [
            ("formal", "gown"), ("evening", "gown"),
            ("black tie", "dress"), ("formal", "sheath"), ("formal", "dress"),
            ("blazer", "dress"), ("tailored", "dress"), ("tailored", "formal"),
            ("structured", "formal"), ("business", "formal"),
        ],
        "hard_rejects": [
            "sleepwear", "nightwear", "pyjama", "gymwear", "mini dress", "clubwear",
            "club dress", "nightclub dress", "party dress", "partywear", "party wear",
            "bachelorette", "cocktail dress",
            "t-shirt dress", "sundress", "beachwear", "casual wear", "casual", "daily wear",
            "loungewear", "lounge wear", "resort wear", "vacation wear", "relaxed fit",
            "anarkali", "kurti", "saree", "lehenga", "salwar", "sequin", "glitter", "shimmer"
        ],
        "threshold": 0.45,
    },
    "office": {
        "aliases": ["office", "work", "workwear", "business", "business casual",
                    "professional", "corporate", "9 to 5", "9-to-5"],
        "positive": [
            ("office dress", 12), ("workwear", 11), ("work dress", 11), ("business casual", 10),
            ("professional", 10), ("office sheath", 10), ("work sheath", 10), ("shirt dress", 9),
            ("pencil dress for work", 10), ("tailored work", 10), ("corporate", 10),
        ],
        "negative": [
            ("party", -12), ("clubwear", -12), ("nightclub", -12), ("sequin", -12),
            ("glitter", -12), ("backless", -10), ("micro mini", -12), ("sexy", -8),
        ],
        "strong_combos": [
            ("office", "dress"), ("work", "dress"), ("professional", "dress"),
            ("business", "dress"), ("office", "sheath"), ("work", "sheath"),
            ("corporate", "dress"),
        ],
        "hard_rejects": ["party dress", "nightclub dress", "sequin", "glitter", "sleepwear", "pyjama", "bikini"],
        "threshold": 0.45,
    },
    "college": {
        "aliases": ["college", "campus", "student", "university", "school",
                    "back to school", "teen"],
        "positive": [
            ("college", 10), ("campus", 9), ("t-shirt dress", 10), ("denim dress", 10),
            ("casual mini", 8), ("youthful", 8), ("trendy day dress", 8),
        ],
        "negative": [
            ("wedding gown", -12), ("bridal", -12), ("formal gown", -10), ("sleepwear", -12),
        ],
        "strong_combos": [
            ("denim", "dress"), ("t-shirt", "dress"), ("campus", "dress"),
        ],
        "hard_rejects": ["sleepwear", "nightwear", "bridal gown", "ball gown"],
        "threshold": 0.45,
    },
    "vacation": {
        "aliases": ["vacation", "holiday", "travel", "resort", "getaway", "leisure", "trip"],
        "positive": [
            ("vacation", 12), ("holiday", 10), ("resort", 10), ("resort wear", 11),
            ("travel dress", 10), ("tropical", 9), ("kaftan", 10), ("bohemian", 9),
            ("breezy sundress", 9), ("holiday dress", 10),
        ],
        "negative": [
            ("office dress", -12), ("sheath dress", -10), ("business suit", -12),
            ("evening gown", -10), ("black tie", -12), ("sequin club", -10),
        ],
        "strong_combos": [
            ("vacation", "dress"), ("resort", "wear"), ("holiday", "dress"),
            ("tropical", "dress"), ("resort", "dress"),
        ],
        "hard_rejects": ["office dress", "sheath dress", "business suit", "evening gown", "black tie", "sequin mini"],
        "threshold": 0.45,
    },
    "beach": {
        "aliases": ["beach", "beachwear", "seaside", "poolside", "pool party", "water", "coastal"],
        "positive": [
            ("beach", 12), ("beachwear", 12), ("cover-up", 11), ("beach maxi", 10),
            ("crochet beach", 10), ("sarong", 10), ("coastal sundress", 9),
        ],
        "negative": [
            ("formal gown", -12), ("office", -12), ("workwear", -12),
            ("sleepwear", -12), ("winter knit", -10), ("heavy velvet", -10),
        ],
        "strong_combos": [
            ("beach", "dress"), ("beach", "maxi"), ("crochet", "beach"),
        ],
        "hard_rejects": ["formal gown", "office uniform", "business suit", "sleepwear"],
        "threshold": 0.45,
    },
    "brunch": {
        "aliases": ["brunch", "brunch outfit", "day brunch", "daytime"],
        "positive": [
            ("brunch", 12), ("floral midi", 9), ("wrap dress", 8), ("fit and flare floral", 9),
            ("pastel sundress", 9), ("daytime chic", 8),
        ],
        "negative": [
            ("clubwear", -10), ("nightclub", -10), ("formal black tie", -12),
            ("work uniform", -10), ("gym", -10),
        ],
        "strong_combos": [
            ("brunch", "dress"), ("floral", "midi"), ("fit and flare", "floral"),
        ],
        "hard_rejects": ["nightclub", "black tie", "gymwear", "sleepwear"],
        "threshold": 0.45,
    },
    "evening": {
        "aliases": ["evening", "evening wear", "after dark", "dinner party", "evening event"],
        "positive": [
            ("evening", 8), ("evening dress", 8), ("evening wear", 8),
            ("cocktail", 6), ("dinner", 6), ("gala", 6), ("elegant", 6),
            ("satin", 5), ("velvet", 5), ("sequin", 5), ("shimmer", 5),
            ("maxi", 4), ("midi", 4), ("gown", 6), ("sophisticated", 5),
        ],
        "negative": [
            ("sleepwear", -8), ("nightwear", -8), ("beachwear", -5),
            ("sportswear", -6), ("casual cotton", -4), ("everyday", -4),
        ],
        "strong_combos": [
            ("evening", "gown"), ("elegant", "satin"), ("cocktail", "midi"),
            ("dinner", "dress"), ("velvet", "maxi"),
        ],
        "hard_rejects": ["sleepwear", "pyjama", "nightwear"],
        "threshold": 0.50,
    },
    "festive": {
        "aliases": ["festive", "festival", "celebration", "occasion wear",
                    "ethnic festival", "diwali", "navratri", "eid"],
        "positive": [
            ("festive", 9), ("festive wear", 9), ("celebration", 7), ("festival", 7),
            ("occasion wear", 7), ("embellished", 6), ("embroidered", 6),
            ("shimmer", 6), ("metallic", 5), ("ethnic", 6), ("traditional", 5),
            ("rich fabric", 5), ("statement", 5), ("ornate", 6), ("sequin", 5),
            ("vibrant", 4), ("zari", 6), ("mirror work", 6), ("resham", 5),
        ],
        "negative": [
            ("sleepwear", -8), ("nightwear", -8), ("office casual", -4),
            ("plain cotton casual", -4),
        ],
        "strong_combos": [
            ("festive", "embroidered"), ("ethnic", "embellished"),
            ("shimmer", "festive"), ("occasion", "embroidered"),
        ],
        "hard_rejects": ["sleepwear", "pyjama", "nightwear", "activewear"],
        "threshold": 0.50,
    },
    "traditional": {
        "aliases": ["traditional", "ethnic", "indian wear", "ethnic wear", "cultural", "heritage"],
        "positive": [
            ("traditional", 9), ("ethnic", 8), ("indian wear", 8), ("anarkali", 8),
            ("kurti", 7), ("kurta", 6), ("saree", 8), ("sari", 8),
            ("salwar", 7), ("ethnic dress", 8), ("embroidered", 6), ("dupatta", 7),
            ("cultural wear", 7), ("ethnic print", 6), ("block print", 5),
            ("handloom", 6), ("chanderi", 6), ("silk dress", 5), ("kalamkari", 6),
            ("bandhani", 6), ("lehenga", 7), ("indo western", 6),
        ],
        "negative": [
            ("western", -3), ("sleepwear", -8), ("nightwear", -8), ("beachwear", -5),
        ],
        "strong_combos": [
            ("ethnic", "embroidered"), ("traditional", "anarkali"),
            ("kurti", "dress"), ("saree", "style"),
        ],
        "hard_rejects": ["sleepwear", "pyjama", "nightwear", "activewear"],
        "threshold": 0.55,
    },
    "sports": {
        "aliases": ["sports", "athletic", "gym", "activewear", "fitness", "workout", "performance"],
        "positive": [
            ("sports dress", 9), ("active dress", 9), ("tennis dress", 9),
            ("golf dress", 8), ("athletic dress", 8), ("workout", 7),
            ("performance", 7), ("activewear", 8), ("stretch", 5),
            ("moisture wicking", 7), ("athletic fit", 7), ("gym dress", 8),
            ("training dress", 7), ("sport", 5),
        ],
        "negative": [
            ("formal gown", -8), ("evening gown", -8), ("wedding", -7),
            ("party dress", -6), ("cocktail", -6), ("office", -5),
        ],
        "strong_combos": [
            ("sports", "dress"), ("athletic", "wear"), ("tennis", "dress"),
            ("gym", "dress"), ("workout", "dress"),
        ],
        "hard_rejects": ["bridal gown", "evening gown", "wedding dress"],
        "threshold": 0.60,
    },
    "summer_casual": {
        "aliases": ["summer casual", "summer", "hot weather", "warm weather",
                    "beach casual", "summer day"],
        "positive": [
            ("summer", 7), ("sundress", 7), ("summer casual", 8), ("cotton", 5),
            ("linen", 5), ("lightweight", 5), ("breathable", 5), ("floral", 4),
            ("sleeveless", 5), ("short sleeve", 4), ("flowy", 4), ("breezy", 5),
        ],
        "negative": [
            ("winter knit", -7), ("heavy velvet", -6), ("heavy wool", -7),
            ("thermal", -7), ("coat dress", -5), ("thick", -4),
            ("sleepwear", -8), ("nightwear", -8),
        ],
        "strong_combos": [
            ("cotton", "summer"), ("linen", "summer"), ("sundress", "floral"),
        ],
        "hard_rejects": ["sleepwear", "pyjama", "nightwear"],
        "threshold": 0.50,
    },
    "winter": {
        "aliases": ["winter", "cold weather", "winterwear", "cozy"],
        "positive": [
            ("winter", 8), ("winterwear", 8), ("knit dress", 8), ("sweater dress", 8),
            ("wool", 7), ("fleece", 7), ("velvet", 5), ("long sleeve", 6),
            ("full sleeve", 6), ("ribbed knit", 7), ("warm", 6), ("thermal", 6),
            ("cold weather", 7), ("cozy", 5), ("turtleneck", 6),
        ],
        "negative": [
            ("beach cover", -6), ("sundress", -6), ("ultra light", -5),
            ("sleeveless summer", -5), ("sleepwear", -8), ("nightwear", -8),
        ],
        "strong_combos": [
            ("knit", "dress"), ("sweater", "dress"), ("wool", "midi"),
            ("velvet", "long sleeve"),
        ],
        "hard_rejects": ["sleepwear", "pyjama", "nightwear", "beach cover-up"],
        "threshold": 0.55,
    },
    "dinner": {
        "aliases": ["dinner", "dinner date", "dining", "restaurant"],
        "positive": [
            ("dinner", 8), ("dinner date", 8), ("evening", 6), ("elegant", 6),
            ("satin", 5), ("slip dress", 5), ("midi", 4), ("maxi", 4),
            ("wrap", 5), ("fitted", 4), ("sophisticated", 5), ("date night", 5),
            ("chic", 4), ("charming", 4),
        ],
        "negative": [
            ("sleepwear", -8), ("nightwear", -8), ("sportswear", -6),
            ("activewear", -6), ("gym", -6), ("beachwear", -5),
        ],
        "strong_combos": [
            ("dinner", "dress"), ("dinner", "elegant"), ("dinner", "satin"),
        ],
        "hard_rejects": ["sleepwear", "pyjama", "nightwear", "activewear"],
        "threshold": 0.50,
    },
    "cocktail": {
        "aliases": ["cocktail", "cocktail party", "cocktail dress", "mixer", "happy hour"],
        "positive": [
            ("cocktail", 9), ("cocktail dress", 9), ("cocktail party", 9),
            ("evening party", 7), ("midi cocktail", 7), ("mini cocktail", 7),
            ("fitted", 5), ("satin", 5), ("sequin", 6), ("velvet", 5),
            ("embellished", 5), ("off shoulder", 5), ("bodycon", 5),
        ],
        "negative": [
            ("casual everyday", -6), ("beachwear", -7), ("sleepwear", -8),
            ("sportswear", -7), ("office only", -5), ("cotton casual", -5),
        ],
        "strong_combos": [
            ("cocktail", "dress"), ("cocktail", "midi"), ("satin", "mini"),
            ("sequin", "bodycon"),
        ],
        "hard_rejects": ["sleepwear", "pyjama", "nightwear", "activewear"],
        "threshold": 0.60,
    },
}

_ALIAS_MAP = {}
for _occ_key, _occ_data in OCCASION_TAXONOMY.items():
    for _alias in _occ_data.get("aliases", []):
        _ALIAS_MAP[_alias.lower()] = _occ_key
    _ALIAS_MAP[_occ_key] = _occ_key

DB_OCCASION_TO_KEY = {
    "casual": "casual", "party": "party", "date": "date",
    "work": "office", "formal": "formal", "gym": "sports",
    "all": "casual", "shopping": "casual", "wedding": "wedding",
    "brunch": "brunch", "beach": "beach", "vacation": "vacation",
    "college": "college", "traditional": "traditional", "festive": "festive",
    "evening": "evening", "dinner": "dinner", "cocktail": "cocktail",
    "winter": "winter", "summer_casual": "summer_casual", "sports": "sports",
}

OCCASION_KEY_TO_DB = {
    "casual": "casual", "party": "party", "date": "date",
    "office": "work", "formal": "formal", "sports": "gym",
    "wedding": "wedding", "brunch": "brunch", "beach": "beach",
    "vacation": "vacation", "college": "college",
    "traditional": "traditional", "festive": "festive",
    "evening": "evening", "dinner": "dinner", "cocktail": "cocktail",
    "winter": "winter", "summer_casual": "summer_casual",
}

SEASON_TAXONOMY = {
    "summer": {
        "aliases": ["summer", "hot", "warm"],
        "positive": [
            ("summer", 8), ("sundress", 7), ("lightweight", 6), ("linen", 5),
            ("cotton", 4), ("breathable", 5), ("sleeveless", 5), ("short sleeve", 4),
            ("flowy", 4), ("breezy", 5), ("tropical", 5), ("floral", 3),
            ("strappy", 4), ("backless", 3),
        ],
        "negative": [
            ("winter", -6), ("knit", -5), ("wool", -6), ("fleece", -6),
            ("thermal", -7), ("heavy", -4),
        ],
        "hard_rejects": ["winter thermal", "heavy wool dress"],
        "threshold": 0.40,
    },
    "winter": {
        "aliases": ["winter", "cold", "cozy"],
        "positive": [
            ("winter", 8), ("knit", 6), ("knit dress", 7), ("sweater dress", 8),
            ("wool", 7), ("fleece", 7), ("velvet", 5), ("long sleeve", 5),
            ("full sleeve", 5), ("ribbed", 6), ("warm", 6), ("thermal", 6),
            ("turtleneck", 7), ("cozy", 5), ("cold weather", 7),
        ],
        "negative": [
            ("summer", -6), ("sundress", -7), ("sleeveless", -5), ("beach", -5),
        ],
        "hard_rejects": ["beach cover-up", "ultra light summer"],
        "threshold": 0.40,
    },
    "spring": {
        "aliases": ["spring", "spring summer", "fresh"],
        "positive": [
            ("spring", 8), ("floral", 6), ("pastel", 6), ("lightweight", 4),
            ("midi", 3), ("cotton", 4), ("linen", 4), ("fresh", 4),
            ("bloom", 4), ("bright", 3),
        ],
        "negative": [("heavy winter", -5), ("thermal", -6), ("wool", -5)],
        "hard_rejects": [],
        "threshold": 0.35,
    },
    "autumn": {
        "aliases": ["autumn", "fall", "fall winter"],
        "positive": [
            ("autumn", 8), ("fall", 8), ("knit", 5), ("earthy", 6),
            ("rust", 5), ("burgundy", 5), ("long sleeve", 4), ("layered", 5),
            ("warm tones", 5), ("rich", 4), ("textured", 4),
        ],
        "negative": [("summer beach", -5)],
        "hard_rejects": [],
        "threshold": 0.35,
    },
    "all": {
        "aliases": ["all season", "all-season", "year round", "all year", "all"],
        "positive": [("all season", 8), ("year round", 8), ("versatile", 3)],
        "negative": [],
        "hard_rejects": [],
        "threshold": 0.20,
    },
}

_SEASON_ALIAS_MAP = {}
for _s_key, _s_data in SEASON_TAXONOMY.items():
    for _alias in _s_data.get("aliases", []):
        _SEASON_ALIAS_MAP[_alias.lower()] = _s_key
    _SEASON_ALIAS_MAP[_s_key] = _s_key


def _safe_print(msg):
    try:
        print(msg)
    except Exception:
        pass


def normalize_occasion(raw):
    """Convert any occasion alias/raw input to canonical occasion key."""
    if not raw:
        return "casual"
    r = str(raw).strip().lower()
    return _ALIAS_MAP.get(r, r)


def normalize_season(raw):
    """Convert any season alias to canonical season key."""
    if not raw:
        return "all"
    r = str(raw).strip().lower()
    return _SEASON_ALIAS_MAP.get(r, r)


def build_normalized_product_text(product):
    """Section 61: Concatenate all product fields into normalized lowercase text."""
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

    raw_desc = str(p.get("description") or p.get("snippet") or "")
    clean_desc = re.sub(r'curated\s+live\s+from\s+[a-z0-9\s\-&]+\.?', ' ', raw_desc, flags=re.I)
    clean_desc = re.sub(r'live\s+[a-z0-9\s\-&]+\s+in\s+authentic\s+collection\.?', ' ', clean_desc, flags=re.I)
    clean_desc = re.sub(r'live\s+[a-z0-9\s\-&]+\s+curated\s+for\s+[a-z0-9\s\-&]+\s+wear\.?', ' ', clean_desc, flags=re.I)
    clean_desc = re.sub(r'curated\s+for\s+[a-z0-9\s\-&]+\s+wear\.?', ' ', clean_desc, flags=re.I)

    fields = [
        p.get("title") or p.get("name") or "",
        clean_desc.strip(),
        p.get("brand") or "",
        p.get("category") or "",
        p.get("product_type") or "",
        p.get("breadcrumbs") or "",
        p.get("merchant_category") or "",
        p.get("attributes") or "",
        p.get("department") or "",
        p.get("retailer") or p.get("store") or p.get("source") or "",
        p.get("link") or p.get("product_url") or "",
    ]
    combined = " ".join(str(f) for f in fields if f)
    t = combined.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


class OccasionClassifier:
    """
    Classify a product occasion suitability.
    Usage: result = OccasionClassifier.classify(product, requested_occasion="party")
    """
    ACCEPT_THRESHOLD = 0.50
    SECONDARY_THRESHOLD = 0.30

    @classmethod
    def classify_occasion_decision(cls, product, requested_occasion, debug=False) -> ThreeStateOccasionResult:
        """
        Phase 3: Authoritative 3-state occasion classification decision.
        Evaluates intrinsic product title, description, brand, and category.
        Returns:
          - SUITABLE: sufficient positive evidence for the selected occasion.
          - UNSUITABLE: clear evidence that the product belongs to a different occasion.
          - UNCERTAIN: insufficient evidence to make a reliable decision.
        """
        norm_occ = normalize_occasion(requested_occasion)
        norm_text = build_normalized_product_text(product)
        if not norm_text:
            return ThreeStateOccasionResult(
                status=OccasionDecision.UNCERTAIN,
                occasion=norm_occ,
                confidence=0.0,
                evidence_strength=0.0,
                primary_occasion="unknown",
                positive_signals=[],
                negative_signals=["empty_text"],
                reason="Product has missing or empty metadata (insufficient evidence)."
            )

        if norm_occ == "formal":
            return cls._classify_formal_decision(norm_text, debug=debug)

        return cls._classify_general_decision(norm_text, norm_occ, debug=debug)

    @classmethod
    def _classify_formal_decision(cls, norm_text: str, debug=False) -> ThreeStateOccasionResult:
        # 1. Clear evidence that the product belongs to a different occasion -> UNSUITABLE
        unsuitable_patterns = [
            (r'\b(casual|casual\s+wear|daily\s+wear|everyday|cotton\s+casual|t-shirt\s+dress|tshirt\s+dress|tee\s+dress|denim\s+dress|shirt\s+dress\s+casual)\b', "casual daywear"),
            (r'\b(beach|beachwear|beach\s+dress|resort\s*wear|vacation\s*wear|holiday\s+wear|sundress|boho|bohemian|kaftan|caftan)\b', "beach/resort wear"),
            (r'\b(clubwear|nightclub|club\s+dress|bachelorette|partywear|party\s+wear|rave|disco|prom\s+dress)\b', "clubwear/partywear"),
            (r'\b(loungewear|lounge\s+wear|sleepwear|nightwear|nighty|nightdress|pajamas?|pyjamas?|bathrobe|towel)\b', "loungewear/sleepwear"),
            (r'\b(anarkali|kurti|kurtis|kurta|saree|sari|lehenga|salwar|ethnic\s+wear|indo\s+western)\b', "traditional/ethnic wear"),
            (r'\b(gymwear|activewear|sportswear|tennis\s+dress|workout\s+dress)\b', "activewear"),
            (r'\b(micro\s+mini|strappy\s+mini|backless\s+sexy|cutout\s+mini)\b', "revealing party mini"),
        ]

        negative_found = []
        for pat, desc in unsuitable_patterns:
            m = re.search(pat, norm_text)
            if m:
                negative_found.append(f"{desc} ('{m.group(0)}')")

        if negative_found:
            return ThreeStateOccasionResult(
                status=OccasionDecision.UNSUITABLE,
                occasion="formal",
                confidence=0.95,
                evidence_strength=0.0,
                primary_occasion="casual" if any("casual" in n for n in negative_found) else "other",
                positive_signals=[],
                negative_signals=negative_found,
                reason=f"Clear evidence of incompatible occasion: {', '.join(negative_found[:3])}"
            )

        # Intrinsic primary occasion check (Phase 4: judge product strictly by its own attributes)
        primary, best_score = cls.detect_primary_occasion_with_score(norm_text)
        if primary not in ("formal", "evening", "ambiguous", "unknown") and best_score >= 8.0:
            return ThreeStateOccasionResult(
                status=OccasionDecision.UNSUITABLE,
                occasion="formal",
                confidence=0.90,
                evidence_strength=0.0,
                primary_occasion=primary,
                positive_signals=[],
                negative_signals=[f"primary_occasion_is_{primary}"],
                reason=f"Product belongs to a different occasion: primary intrinsic occasion is {primary} (score={best_score:.1f})"
            )

        # 2. Check for SUITABLE positive formal evidence
        positive_formal_patterns = [
            (r'\b(business\s+formal|corporate\s+formal|executive\s+formal|professional\s+formalwear|tailored\s+formalwear)\b', 16, "business formal"),
            (r'\b(tailored\s+formal\s+dress|structured\s+formal\s+dress|formal\s+midi\s+dress|formal\s+sheath\s+dress)\b', 15, "tailored formal dress"),
            (r'\b(formal\s+blazer\s+dress|tailored\s+blazer\s+sheath|blazer\s+sheath\s+dress|tailored\s+blazer\s+dress)\b', 15, "formal blazer dress"),
            (r'\b(crepe\s+formal\s+sheath|ponte\s+formal\s+sheath|tailored\s+crepe\s+sheath|structured\s+sheath\s+dress\s+for\s+formal)\b', 14, "formal crepe sheath"),
            (r'\b(black\s+tie\s+evening\s+gown|black\s+tie\s+gown|black\s+tie\s+dress|black\s+tie)\b', 16, "black tie"),
            (r'\b(gala\s+gown|formal\s+gala\s+gown|floor\s+length\s+formal\s+gown|floor\s+length\s+gala)\b', 15, "gala gown"),
            (r'\b(formal\s+gown|evening\s+gown|floor\s+length\s+gown)\b', 13, "formal gown"),
            (r'\b(tailored\s+formal|structured\s+formal|formal\s+occasion\s+dress|formalwear\s+dress)\b', 12, "tailored formal"),
            (r'\b(formal\s+dress|formal\s+wear|formalwear|formal\s+event|formal\s+banquet)\b', 10, "formal wear"),
            (r'\b(structured\s+sheath\s+dress|tailored\s+sheath\s+dress|tailored\s+pencil\s+dress)\b', 10, "structured/tailored sheath"),
        ]

        pos_signals = []
        total_pos_score = 0.0
        for pat, weight, label in positive_formal_patterns:
            m = re.search(pat, norm_text)
            if m:
                pos_signals.append(f"{label} ('{m.group(0)}') (+{weight})")
                total_pos_score += weight

        # Strong combination bonuses
        if re.search(r'\b(tailored|structured)\b', norm_text) and re.search(r'\b(formal|corporate|business|executive)\b', norm_text):
            pos_signals.append("COMBO(tailored/structured + formal/corporate) (+10)")
            total_pos_score += 10.0

        if re.search(r'\b(sheath|midi|pencil)\b', norm_text) and re.search(r'\b(formal|tailored)\b', norm_text):
            pos_signals.append("COMBO(sheath/midi/pencil + formal/tailored) (+10)")
            total_pos_score += 10.0

        if total_pos_score >= 10.0:
            confidence = min(0.98, max(0.80, total_pos_score / 25.0))
            return ThreeStateOccasionResult(
                status=OccasionDecision.SUITABLE,
                occasion="formal",
                confidence=confidence,
                evidence_strength=total_pos_score,
                primary_occasion="formal",
                positive_signals=pos_signals,
                negative_signals=[],
                reason=f"Sufficient positive formal evidence: {', '.join(pos_signals[:4])} (score={total_pos_score:.1f})"
            )

        # 3. UNCERTAIN (Phase 3: generic silhouette words alone without supporting formal evidence)
        generic_markers = []
        for word in ["dress", "sheath", "midi", "maxi", "elegant", "women", "fitted", "knee length"]:
            if re.search(rf'\b{word}\b', norm_text):
                generic_markers.append(word)

        uncertain_reason = (
            f"Insufficient formal evidence: Generic terms ({', '.join(generic_markers[:4])}) "
            f"without supporting business-formal, tailored construction, or black-tie/gala details."
        ) if generic_markers else "Insufficient formal evidence: No supporting formal or tailored details found."

        return ThreeStateOccasionResult(
            status=OccasionDecision.UNCERTAIN,
            occasion="formal",
            confidence=0.30,
            evidence_strength=total_pos_score,
            primary_occasion="ambiguous",
            positive_signals=pos_signals,
            negative_signals=["lacks_sufficient_positive_formal_evidence"],
            reason=uncertain_reason
        )

    @classmethod
    def _classify_general_decision(cls, norm_text: str, norm_occ: str, debug=False) -> ThreeStateOccasionResult:
        profile = OCCASION_TAXONOMY.get(norm_occ)
        if not profile:
            return ThreeStateOccasionResult(
                status=OccasionDecision.SUITABLE, occasion=norm_occ, confidence=0.70,
                evidence_strength=10.0, primary_occasion=norm_occ, positive_signals=["no taxonomy"],
                negative_signals=[], reason="Occasion not in taxonomy -- lenient pass"
            )

        # Check hard rejects
        for hr in profile.get("hard_rejects", []):
            if hr.lower() in norm_text:
                return ThreeStateOccasionResult(
                    status=OccasionDecision.UNSUITABLE, occasion=norm_occ, confidence=0.0,
                    evidence_strength=0.0, primary_occasion="unknown", positive_signals=[],
                    negative_signals=[hr], reason=f"Hard reject keyword matched: {hr}"
                )

        raw_score = sum(w for kw, w in profile.get("positive", []) if kw.lower() in norm_text)
        raw_ded = sum(abs(w) for kw, w in profile.get("negative", []) if kw.lower() in norm_text)
        for kw1, kw2 in profile.get("strong_combos", []):
            if kw1.lower() in norm_text and kw2.lower() in norm_text:
                raw_score += 15.0

        net = max(0.0, raw_score - raw_ded)
        threshold = profile.get("threshold", cls.ACCEPT_THRESHOLD) * 16.0
        primary, best_score = cls.detect_primary_occasion_with_score(norm_text)

        if primary != norm_occ and best_score > (net * 1.25) and best_score >= 10.0:
            return ThreeStateOccasionResult(
                status=OccasionDecision.UNSUITABLE, occasion=norm_occ, confidence=0.1,
                evidence_strength=net, primary_occasion=primary, positive_signals=[],
                negative_signals=[f"primary_is_{primary}"],
                reason=f"Primary intrinsic occasion is {primary} (score={best_score:.1f} vs requested {norm_occ}={net:.1f})"
            )

        if net >= threshold and raw_score >= 8.0:
            return ThreeStateOccasionResult(
                status=OccasionDecision.SUITABLE, occasion=norm_occ, confidence=min(1.0, net / 16.0),
                evidence_strength=net, primary_occasion=norm_occ,
                positive_signals=[f"net_score_{net:.1f}"], negative_signals=[],
                reason=f"Sufficient {norm_occ} evidence (score={net:.1f})"
            )
        elif net > 0:
            return ThreeStateOccasionResult(
                status=OccasionDecision.UNCERTAIN, occasion=norm_occ, confidence=min(0.5, net / 16.0),
                evidence_strength=net, primary_occasion="ambiguous",
                positive_signals=[f"marginal_score_{net:.1f}"], negative_signals=[],
                reason=f"Marginal/uncertain {norm_occ} evidence (score={net:.1f}, need>={threshold:.1f})"
            )
        else:
            return ThreeStateOccasionResult(
                status=OccasionDecision.UNSUITABLE, occasion=norm_occ, confidence=0.0,
                evidence_strength=0.0, primary_occasion="unknown",
                positive_signals=[], negative_signals=["zero_evidence"],
                reason=f"No positive {norm_occ} evidence found"
            )

    @classmethod
    def classify(cls, product, requested_occasion, debug=True):
        norm_occ = normalize_occasion(requested_occasion)
        three_state = cls.classify_occasion_decision(product, norm_occ, debug=False)

        # For strict Formal, ONLY SUITABLE products pass (Phase 3 requirement)
        if norm_occ == "formal":
            if three_state.status == OccasionDecision.SUITABLE:
                decision = "ACCEPT"
                confidence = three_state.confidence
                reason = three_state.reason
            elif three_state.status == OccasionDecision.UNSUITABLE:
                decision = "REJECT"
                confidence = 0.0
                reason = f"Unsuitable for Formal: {three_state.reason}"
            else:  # UNCERTAIN
                decision = "REJECT"
                confidence = 0.20
                reason = f"Uncertain formal evidence: {three_state.reason}"

            evidence_lines = [f"Three-state decision: {three_state.status} (score={three_state.evidence_strength:.1f})"]
            if three_state.positive_signals:
                evidence_lines.append("Positive: " + ", ".join(three_state.positive_signals[:8]))
            if three_state.negative_signals:
                evidence_lines.append("Negative: " + ", ".join(three_state.negative_signals[:5]))

            if debug:
                _safe_print(
                    f"\n[OCCASION FILTER (FORMAL)]\n"
                    f"Product: {(product.get('title') or product.get('name') or 'Unknown')[:80]}\n"
                    f"Decision: {decision} ({three_state.status}) | Confidence: {confidence:.2f}\n"
                    f"Reason: {reason}"
                )

            return OccasionResult(
                occasion=norm_occ, confidence=confidence, primary_occasion=three_state.primary_occasion,
                compatible_occasions=[norm_occ] if decision == "ACCEPT" else [],
                positive_signals=three_state.positive_signals,
                negative_signals=three_state.negative_signals,
                evidence=evidence_lines,
                decision=decision, reason=reason,
                three_state_decision=three_state.status
            )

        # General pipeline for non-formal occasions
        if three_state.status == OccasionDecision.SUITABLE:
            decision = "ACCEPT"
        elif three_state.status == OccasionDecision.UNCERTAIN:
            decision = "SECONDARY"
        else:
            decision = "REJECT"

        evidence_lines = [f"Three-state decision: {three_state.status} (score={three_state.evidence_strength:.1f})"]
        if three_state.positive_signals:
            evidence_lines.append("Positive: " + ", ".join(three_state.positive_signals[:8]))
        if three_state.negative_signals:
            evidence_lines.append("Negative: " + ", ".join(three_state.negative_signals[:5]))

        return OccasionResult(
            occasion=norm_occ, confidence=three_state.confidence, primary_occasion=three_state.primary_occasion,
            compatible_occasions=cls._detect_all_occasions(build_normalized_product_text(product), norm_occ),
            positive_signals=three_state.positive_signals,
            negative_signals=three_state.negative_signals,
            evidence=evidence_lines,
            decision=decision, reason=three_state.reason,
            three_state_decision=three_state.status
        )

    @classmethod
    def _detect_all_occasions(cls, norm_text, requested):
        compatible = []
        for occ_key, profile in OCCASION_TAXONOMY.items():
            raw_score = sum(w for kw, w in profile.get("positive", []) if kw.lower() in norm_text)
            threshold = profile.get("threshold", cls.ACCEPT_THRESHOLD)
            if raw_score / 16.0 >= threshold * 0.7:
                compatible.append(occ_key)
        return compatible or [requested]

    @classmethod
    def detect_primary_occasion_with_score(cls, product_or_text):
        if isinstance(product_or_text, dict):
            norm_text = build_normalized_product_text(product_or_text)
        else:
            norm_text = str(product_or_text).lower()
        best_occ = "ambiguous"
        best_score = 0.0
        for occ_key, profile in OCCASION_TAXONOMY.items():
            score = sum(w for kw, w in profile.get("positive", []) if kw.lower() in norm_text)
            ded = sum(abs(w) for kw, w in profile.get("negative", []) if kw.lower() in norm_text)
            for kw1, kw2 in profile.get("strong_combos", []):
                if kw1.lower() in norm_text and kw2.lower() in norm_text:
                    score += 15.0
            net = max(0.0, score - ded)
            if net > best_score:
                best_score = net
                best_occ = occ_key
        if best_score < 4.0:
            return "ambiguous", 0.0
        return best_occ, best_score

    @classmethod
    def detect_primary_occasion(cls, product_or_text):
        best_occ, _ = cls.detect_primary_occasion_with_score(product_or_text)
        return best_occ



class SeasonClassifier:
    """Classify product season suitability."""

    @classmethod
    def classify(cls, product, requested_season, debug=True):
        norm_season = normalize_season(requested_season)
        profile = SEASON_TAXONOMY.get(norm_season)
        if not profile or norm_season == "all":
            return SeasonResult(
                season=norm_season, confidence=0.80, detected_season="all",
                compatible_seasons=["all", "summer", "winter", "spring", "autumn"],
                positive_signals=["all-season"], negative_signals=[],
                decision="ACCEPT", reason="All-season request"
            )
        norm_text = build_normalized_product_text(product)
        for hr in profile.get("hard_rejects", []):
            if hr.lower() in norm_text:
                return SeasonResult(
                    season=norm_season, confidence=0.0, detected_season="unknown",
                    compatible_seasons=[], positive_signals=[], negative_signals=[hr],
                    decision="REJECT", reason=f"Hard reject: {hr}"
                )
        pos_score = sum(w for kw, w in profile.get("positive", []) if kw.lower() in norm_text)
        neg_score = sum(abs(w) for kw, w in profile.get("negative", []) if kw.lower() in norm_text)
        pos_matched = [kw for kw, _ in profile.get("positive", []) if kw.lower() in norm_text]
        neg_matched = [kw for kw, _ in profile.get("negative", []) if kw.lower() in norm_text]
        net = max(0.0, pos_score - neg_score)
        confidence = min(1.0, net / 30.0)
        threshold = profile.get("threshold", 0.35)
        detected = cls._detect_primary_season(norm_text)
        compatible = cls._detect_compatible_seasons(norm_text)
        if confidence < threshold and neg_matched:
            decision = "REJECT"
            reason = f"Negative season evidence for {norm_season}: {neg_matched[:3]}"
        elif confidence >= threshold:
            decision = "ACCEPT"
            reason = f"Season match: {norm_season} (confidence={confidence:.2f})"
        else:
            if not pos_matched and not neg_matched:
                decision = "ACCEPT"
                reason = "No season-specific signals -- treating as compatible"
                confidence = 0.5
            else:
                decision = "REJECT"
                reason = f"Insufficient season signals (confidence={confidence:.2f})"
        if debug:
            _safe_print(
                f"\n[SEASON FILTER]\n"
                f"Product: {(product.get('title') or product.get('name') or 'Unknown')[:80]}\n"
                f"Requested Season: {norm_season} | Confidence: {confidence:.2f} | Decision: {decision}"
            )
        return SeasonResult(
            season=norm_season, confidence=confidence, detected_season=detected,
            compatible_seasons=compatible, positive_signals=pos_matched,
            negative_signals=neg_matched, decision=decision, reason=reason
        )

    @classmethod
    def detect_primary_season(cls, product_or_text):
        if isinstance(product_or_text, dict):
            norm_text = build_normalized_product_text(product_or_text)
        else:
            norm_text = str(product_or_text).lower()
        return cls._detect_primary_season(norm_text)

    @classmethod
    def _detect_primary_season(cls, norm_text):
        best = "all"
        best_score = 0.0
        for s_key, profile in SEASON_TAXONOMY.items():
            if s_key == "all":
                continue
            score = sum(w for kw, w in profile.get("positive", []) if kw.lower() in norm_text)
            if score > best_score:
                best_score = score
                best = s_key
        return best

    @classmethod
    def _detect_compatible_seasons(cls, norm_text):
        compatible = []
        for s_key, profile in SEASON_TAXONOMY.items():
            score = sum(w for kw, w in profile.get("positive", []) if kw.lower() in norm_text)
            threshold = profile.get("threshold", 0.35)
            if s_key == "all" or score / 30.0 >= threshold * 0.5:
                compatible.append(s_key)
        return compatible or ["all"]


OCCASION_QUERY_FAMILIES = {
    "party": [
        "women party dress", "women partywear dress", "women cocktail dress",
        "women evening party dress", "women sequin party dress",
        "women satin party dress", "women bodycon party dress",
        "women mini party dress", "women midi party dress",
        "women glitter party dress", "women glamorous party dress",
    ],
    "casual": [
        "women casual dress", "women everyday dress", "women cotton casual dress",
        "women casual midi dress", "women day dress", "women simple dress",
        "women comfortable dress", "women relaxed dress", "women t-shirt dress",
        "women shirt dress casual",
    ],
    "date": [
        "women date night dress", "women romantic dress", "women dinner dress",
        "women satin dress", "women slip dress", "women wrap dress date night",
        "women bodycon date dress", "women off shoulder date dress",
        "women elegant date dress",
    ],
    "wedding": [
        "women wedding guest dress", "women wedding occasion dress",
        "women elegant wedding maxi dress", "women formal wedding guest dress",
        "women bridesmaid dress", "women embellished wedding dress",
        "women silk wedding guest dress", "women chiffon wedding dress",
    ],
    "formal": [
        "women's formal dress",
        "women's business formal dress",
        "women's tailored formal midi dress",
        "women's structured sheath dress for formal occasions",
        "women's elegant formal occasion dress",
        "women's professional formalwear dress",
        "women's black tie evening gown",
        "women's floor length formal gala gown",
    ],
    "office": [
        "women office dress", "women workwear dress", "women formal office midi dress",
        "women business casual dress", "women sheath dress office",
        "women tailored dress office", "women professional dress",
        "women shirt dress office",
    ],
    "college": [
        "women college casual dress", "women campus dress", "women t-shirt dress",
        "women denim dress casual", "women everyday college dress",
        "women casual cotton dress",
    ],
    "vacation": [
        "women vacation dress", "women resort dress", "women summer holiday dress",
        "women flowy vacation maxi dress", "women holiday floral dress",
        "women linen vacation dress", "women travel dress",
    ],
    "beach": [
        "women beach dress", "women beach cover-up dress", "women resort beach dress",
        "women tropical beach maxi dress", "women sundress beach",
        "women crochet beach dress", "women beach flowy dress",
    ],
    "brunch": [
        "women brunch dress", "women day dress brunch", "women floral brunch dress",
        "women midi brunch dress", "women casual chic dress", "women wrap dress brunch",
    ],
    "evening": [
        "women evening dress", "women evening gown", "women cocktail evening dress",
        "women dinner evening dress", "women satin evening dress",
        "women velvet evening dress", "women elegant evening dress",
    ],
    "festive": [
        "women festive dress", "women festive wear dress", "women embellished festive dress",
        "women ethnic festive dress", "women occasion wear festive dress",
        "women shimmer festive dress",
    ],
    "traditional": [
        "women traditional dress", "women ethnic dress", "women anarkali dress",
        "women kurti dress", "women embroidered ethnic dress",
        "women indo western dress", "women indian ethnic dress",
    ],
    "sports": [
        "women sports dress", "women athletic dress", "women tennis dress",
        "women gym dress", "women activewear dress", "women workout dress",
        "women performance dress",
    ],
    "summer_casual": [
        "women summer dress", "women sundress", "women summer casual dress",
        "women cotton summer dress", "women linen summer dress",
        "women floral summer dress", "women lightweight dress summer",
    ],
    "winter": [
        "women winter dress", "women knit dress", "women sweater dress",
        "women wool dress winter", "women velvet winter dress",
        "women long sleeve dress winter", "women warm dress winter",
    ],
    "dinner": [
        "women dinner dress", "women dinner date dress", "women elegant dinner dress",
        "women satin dinner dress", "women midi dinner dress",
    ],
    "cocktail": [
        "women cocktail dress", "women cocktail party dress", "women midi cocktail dress",
        "women satin cocktail dress", "women sequin cocktail dress",
        "women fitted cocktail dress",
    ],
}


def get_occasion_search_queries(requested_occasion, season="", colors=None,
                                retailer=None, price_cue="", max_queries=10):
    """Generate occasion-specific search queries for SerpApi."""
    norm_occ = normalize_occasion(requested_occasion)
    base_queries = OCCASION_QUERY_FAMILIES.get(norm_occ, [f"women's {norm_occ} dress" if norm_occ == "formal" else f"women {norm_occ} dress"])
    season_term = (season or "").lower().strip()
    if season_term in ("all", ""):
        season_term = ""
    queries = []

    # Priority 1: Base focused occasion queries
    for base in base_queries:
        q = base
        if retailer and retailer.lower() not in ("all", "all retailers", ""):
            q = f"{retailer} {q}"
        if season_term:
            q += f" {season_term}"
        if price_cue:
            q += f" {price_cue}"
        queries.append(q.strip())

    # Priority 2: Color combinations
    if colors:
        for color in colors[:3]:
            if norm_occ == "formal":
                q = f"women's {color} business formal dress"
            else:
                q = f"women {color} {norm_occ} dress"
            if retailer and retailer.lower() not in ("all", "all retailers", ""):
                q = f"{retailer} {q}"
            if season_term:
                q += f" {season_term}"
            if price_cue:
                q += f" {price_cue}"
            queries.append(q.strip())

    if season_term and norm_occ != "formal":
        season_dress_types = {
            "summer": ["sundress", "cotton dress", "linen dress", "floral dress"],
            "winter": ["knit dress", "sweater dress", "velvet dress"],
            "spring": ["floral dress", "pastel dress", "light dress"],
            "autumn": ["midi dress", "long sleeve dress", "wrap dress"],
        }.get(season_term, [])
        for sdt in season_dress_types[:2]:
            q = f"women {sdt} {norm_occ}"
            if price_cue:
                q += f" {price_cue}"
            queries.append(q.strip())

    seen = set()
    deduped = []
    for q in queries:
        cleaned = " ".join(q.split()).lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            deduped.append(" ".join(q.split()))
    return deduped[:max_queries]


def get_occasion_db_value(occasion_key):
    """Convert classifier occasion key to DB-storable occasion value."""
    return OCCASION_KEY_TO_DB.get(occasion_key, occasion_key)


def get_classifier_key_from_db(db_occasion):
    """Convert DB occasion value to classifier occasion key."""
    return DB_OCCASION_TO_KEY.get((db_occasion or "").lower(), "casual")
