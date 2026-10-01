import urllib.parse
from typing import List, Dict, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User, UserProfile, StylePreference
    from models.outfit import Outfit

# ---------------------------------------------------------------------------
# Skin-tone â†’ compatible outfit color palette
# ---------------------------------------------------------------------------
SKIN_TONE_COMPATIBLE_COLORS = {
    # Enhances contrast and balances lighter skin tones
    # Spec primary: Navy, Emerald Green, Burgundy, Charcoal Grey, Royal Blue
    'fair': [
        'navy', 'emerald', 'burgundy', 'charcoal', 'royal blue',
        # variants / related
        'black', 'white', 'grey', 'gray', 'silver', 'dark blue', 'forest green',
    ],
    # Creates a balanced and vibrant appearance
    # Spec primary: Soft Blue, Lavender, Peach, Mint Green, Rose Pink
    'light': [
        'soft blue', 'lavender', 'peach', 'mint green', 'rose pink',
        # variants / related
        'blush', 'lilac', 'pastel', 'baby blue', 'dusty rose', 'mint', 'pink',
    ],
    # Highlights natural warm undertones
    # Spec primary: Olive Green, Beige, Mustard Yellow, Forest Green, Cream
    'medium': [
        'olive green', 'beige', 'mustard yellow', 'forest green', 'cream',
        # variants / related
        'olive', 'mustard', 'camel', 'khaki', 'tan', 'terracotta', 'rust',
    ],
    # Complements olive undertones
    # Spec primary: Rust, Coral, Cream, Charcoal, Deep Teal
    'olive': [
        'rust', 'coral', 'cream', 'charcoal', 'deep teal',
        # variants / related
        'teal', 'brick red', 'warm brown', 'gold', 'earth', 'brown', 'maroon',
    ],
    # Creates strong visual contrast and enhances darker skin tones
    # Spec primary: White, Gold, Royal Blue, Magenta, Bright Yellow
    'deep': [
        'white', 'gold', 'royal blue', 'magenta', 'bright yellow',
        # variants / related
        'yellow', 'electric blue', 'fuchsia', 'cobalt', 'hot pink', 'purple',
    ],
}

# ---------------------------------------------------------------------------
# Color Normalization
# ---------------------------------------------------------------------------
COLOR_NORMALIZATION = {
    'wine red': 'burgundy',
    'maroon': 'burgundy',
    'dark red': 'burgundy',
    'navy blue': 'navy',
    'dark blue': 'navy',
    'light blue': 'soft blue',
    'hot pink': 'magenta',
    'dark grey': 'charcoal',
    'dark gray': 'charcoal',
    'mustard': 'mustard yellow',
    'sandy tan': 'tan',
    'earth tones': 'brown',
}

def _normalize_color(color: str) -> str:
    """Normalize inconsistent product colors to standard base colors."""
    c = color.lower().strip()
    return COLOR_NORMALIZATION.get(c, c)

# ---------------------------------------------------------------------------
# Body type / shape â†’ compatible style_type keywords
# ---------------------------------------------------------------------------
FEMALE_BODY_TYPE_STYLES = {
    'hourglass':          ['fitted', 'wrap', 'belted', 'elegant', 'feminine', 'glam'],
    'pear':               ['a-line', 'bootcut', 'wide-leg', 'bohemian', 'minimalist'],
    'apple':              ['empire', 'v-neck', 'straight', 'minimalist', 'resort', 'smart-casual'],
    'rectangle':          ['peplum', 'ruffled', 'layered', 'feminine', 'glam', 'bohemian'],
    'inverted_triangle':  ['wide-leg', 'flared', 'bootcut', 'bohemian', 'casual', 'minimalist'],
}

MALE_BODY_TYPE_STYLES = {
    'athletic':  ['fitted', 'sporty', 'athletic', 'smart-casual', 'formal'],
    'slim':      ['layered', 'casual', 'minimalist', 'smart-casual', 'streetwear'],
    'average':   ['smart-casual', 'casual', 'formal', 'minimalist', 'streetwear'],
    'muscular':  ['structured', 'fitted', 'formal', 'smart-casual', 'athletic'],
    'heavy':     ['structured', 'smart-casual', 'formal', 'minimalist', 'casual'],
}


class RecommendationEngine:
    """
    Netflix-style hybrid recommendation engine.

    Scoring weights (per spec):
      Skin-tone color harmony   → 40 %   (key: 'style_match')
      Body type compatibility   → 25 %   (key: 'body_type')
      Occasion suitability      → 20 %   (key: 'comfort')
      Season suitability        → 10 %   (key: 'trend')
      Collaborative filtering   →  5 %   (key: 'feedback')

    The score keys intentionally match what the React frontend already
    renders (style_match / comfort / trend / body_type) so no UI change
    is needed.
    """

    def __init__(self):
        self.weights = {
            'style_match':    0.35,   # skin-tone color harmony
            'body_type':      0.20,   # body type / shape compatibility
            'comfort':        0.20,   # occasion suitability
            'purchasability': 0.10,   # penalize out of stock / no real URL
            'trend':          0.10,   # season suitability
            'feedback':       0.05,   # collaborative filtering signal
        }

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def generate_recommendations(
        self,
        user: 'User',
        profile: 'UserProfile',
        preferences: 'StylePreference',
        occasion: str,
        season: str,
        limit: int = 25,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        price_range: Optional[str] = None,
        retailer: Optional[str] = None,
    ) -> List[Dict]:
        """Generate personalized outfit recommendations using hybrid filtering."""
        from models.outfit import Outfit, Recommendation
        
        from services.shopping_service import SerpApiShoppingService, ProductValidator
        shopping_service = SerpApiShoppingService()
        
        compatible_colors = []
        skin_tone = getattr(profile, 'skin_tone', None) if profile else None
        if skin_tone:
            from services.recommendation_engine import SKIN_TONE_COMPATIBLE_COLORS
            compatible_colors = SKIN_TONE_COMPATIBLE_COLORS.get(skin_tone.lower(), [])

        raw_gender = (getattr(profile, 'gender', None) or '').lower() if profile else ''
        norm_gender = ProductValidator.normalize_gender(raw_gender)
        viewer_gender = norm_gender if norm_gender != 'unknown' else raw_gender
        target_category = 'dress' if norm_gender == 'female' else 'clothing'
        collab_map = self._build_collaborative_map(profile)

        # ── EXCLUSIVE LIVE SHOPPING MODE ─────────────────────────────────
        # When SERPAPI_KEY is configured, live products are the single source
        # of truth. Old SQLite mock products are never mixed into live recommendations.
        if shopping_service.is_configured():
            live_products = shopping_service.fetch_live_recommendations(
                profile=profile,
                preferences=preferences,
                occasion=occasion,
                season=season,
                compatible_colors=compatible_colors,
                target_category=target_category,
                limit=limit,
                min_price=min_price,
                max_price=max_price,
                price_range=price_range,
                retailer=retailer
            )
            if live_products:
                scored = []
                for p in live_products:
                    outfit_rec = Outfit.query.filter_by(external_id=p['external_id']).first()
                    if outfit_rec:
                        scores = self._calculate_scores(
                            outfit_rec, profile, preferences, occasion, season, collab_map
                        )
                        overall = self._calculate_overall_score(scores)
                        p['match_score'] = overall
                        p['shopping_links'] = self._generate_shopping_links(outfit_rec, viewer_gender)
                        scored.append({
                            'outfit': p,
                            'scores': scores,
                            'overall_score': overall
                        })
                scored.sort(key=lambda x: x['overall_score'], reverse=True)
                top = scored[:limit]

                # Fetch similar live recommendations from SerpApi with matching price & retailer filters
                if top:
                    self.last_similar_recommendations = shopping_service.fetch_similar_live_products(
                        top[0]['outfit'], profile, limit=4,
                        min_price=min_price, max_price=max_price, price_range=price_range, retailer=retailer
                    )
                else:
                    self.last_similar_recommendations = []

                return top
            else:
                # Live shopping is active but no live items returned: do not leak mock products!
                self.last_similar_recommendations = []
                return []

        # ── OFFLINE CATALOG FALLBACK (When SERPAPI_KEY is not configured) ─
        # Step 1 -- Query with DB-level gender + occasion filters.
        query = Outfit.query.filter(Outfit.in_stock == True, Outfit.purchasable == True)

        # Gender filter (STRICT -- male or female, never cross-gender)
        if norm_gender in ('female', 'male'):
            query = query.filter(Outfit.gender == norm_gender)
            if norm_gender == 'female':
                query = query.filter(Outfit.category == 'dress')
            elif norm_gender == 'male':
                query = query.filter(Outfit.category != 'dress')

        # Occasion filter
        if occasion and occasion.lower() not in ('all', ''):
            query = query.filter(Outfit.occasion == occasion.lower())

        outfits = query.all()

        # Step 2 – Skin-tone pre-filter
        if skin_tone:
            outfits = self._filter_by_skin_tone(outfits, skin_tone)

        # Step 4 – Score every outfit
        scored = []
        for outfit in outfits:
            scores = self._calculate_scores(
                outfit, profile, preferences, occasion, season, collab_map
            )
            overall = self._calculate_overall_score(scores)
            outfit_dict = outfit.to_dict()
            outfit_dict['shopping_links'] = self._generate_shopping_links(outfit, viewer_gender)
            outfit_dict['match_score'] = overall
            if outfit_dict.get('exact_product_link_available'):
                outfit_dict['shopping_url'] = outfit.product_url
            else:
                outfit_dict['shopping_url'] = None
            scored.append({
                'outfit':        outfit_dict,
                'scores':        scores,
                'overall_score': overall,
            })

        # Step 5 – Rank by overall score
        scored.sort(key=lambda x: x['overall_score'], reverse=True)
        available_scored = [
            s for s in scored
            if s['outfit'].get('exact_product_link_available') and s['outfit'].get('in_stock')
        ]
        top = available_scored[:limit] if available_scored else scored[:limit]
        self.last_similar_recommendations = []

        # Step 6 â€“ Persist recommendation records (best-effort)
        try:
            from extensions import db
            for rec_data in top:
                rec = Recommendation(
                    user_id=user.id,
                    outfit_id=rec_data['outfit']['id'],
                    overall_score=rec_data['overall_score'],
                    style_match_score=rec_data['scores']['style_match'],
                    comfort_score=rec_data['scores']['comfort'],
                    trend_score=rec_data['scores']['trend'],
                    body_type_score=rec_data['scores']['body_type'],
                    occasion=occasion,
                    season=season,
                )
                db.session.add(rec)
            db.session.commit()
        except Exception:
            from extensions import db
            db.session.rollback()

        return top

    # -----------------------------------------------------------------------
    # Collaborative filtering
    # -----------------------------------------------------------------------

    def _build_collaborative_map(self, profile) -> Dict[int, float]:
        """
        Build {outfit_id â†’ collaborative_signal (0.0â€“1.0)}.

        Finds users who share the same gender + body_type as the current user,
        then aggregates their interaction and feedback signals.

        Interaction weights:
          save   â†’ 3.0   (strongest signal: user explicitly bookmarked it)
          click  â†’ 2.0   (navigated to the detail page)
          view   â†’ 1.0   (appeared in their recommendations)
          liked  â†’ 4.0   (explicit positive feedback)
          rating â‰¥ 4 â†’ 4.0

        All counts are normalized to [0, 1] so they integrate cleanly into
        the overall scoring formula.
        """
        if not profile or not profile.gender or not profile.body_type:
            return {}

        try:
            from models.user import UserProfile
            from models.outfit import OutfitInteraction, UserFeedback

            # Find similar users (same gender + body_type, excluding self)
            similar_profiles = UserProfile.query.filter(
                UserProfile.gender    == profile.gender,
                UserProfile.body_type == profile.body_type,
                UserProfile.user_id   != profile.user_id,
            ).all()

            if not similar_profiles:
                return {}

            similar_ids = [p.user_id for p in similar_profiles]

            # Weight map for interaction types
            itype_weight = {'save': 3.0, 'click': 2.0, 'view': 1.0}

            # Aggregate implicit interactions
            signals: Dict[int, float] = {}

            for inter in OutfitInteraction.query.filter(
                OutfitInteraction.user_id.in_(similar_ids)
            ).all():
                w = itype_weight.get(inter.interaction_type, 1.0)
                signals[inter.outfit_id] = signals.get(inter.outfit_id, 0.0) + w

            # Aggregate explicit feedback (likes / high ratings)
            for fb in UserFeedback.query.filter(
                UserFeedback.user_id.in_(similar_ids)
            ).all():
                if fb.liked or (fb.rating and fb.rating >= 4):
                    signals[fb.outfit_id] = signals.get(fb.outfit_id, 0.0) + 4.0

            if not signals:
                return {}

            # Normalize to [0, 1]
            max_signal = max(signals.values())
            return {oid: round(v / max_signal, 3) for oid, v in signals.items()}

        except Exception as exc:
            print(f"[RecommendationEngine] Collaborative map error: {exc}")
            return {}

    # -----------------------------------------------------------------------
    # Skin-tone pre-filter
    # -----------------------------------------------------------------------

    def _filter_by_skin_tone(self, outfits: list, skin_tone: str) -> list:
        """
        Remove outfits whose color palette is incompatible with the user's
        skin tone.

        Filtering rules:
          - Outfits that have no colors defined are kept (cannot be judged).
          - An outfit is compatible when at least one of its colors (substring)
            appears in the skin tone's compatible color list.
          - Safety net: if fewer than 3 outfits survive the filter the original
            unfiltered list is returned so the user always sees results.

        This implements the "Skin Tone Compatibility Filtering Layer" described
        in the product spec: outfits with no matching colors are dropped before
        scoring so they never appear in the ranked results.
        """
        tone_key = skin_tone.lower()
        compatible = SKIN_TONE_COMPATIBLE_COLORS.get(tone_key, [])
        if not compatible:
            return outfits

        filtered = []
        for outfit in outfits:
            if not outfit.colors:
                # Keep: no color info available, cannot disqualify
                filtered.append(outfit)
                continue
            outfit_colors_normalized = [_normalize_color(c) for c in outfit.colors]
            is_compatible = any(
                any(comp in oc or oc in comp for comp in compatible)
                for oc in outfit_colors_normalized
            )
            if is_compatible:
                filtered.append(outfit)

        # Safety net: always return at least 3 outfits
        return filtered if len(filtered) >= 3 else outfits

    # -----------------------------------------------------------------------
    # Scoring helpers
    # -----------------------------------------------------------------------

    def _calculate_scores(
        self, outfit, profile, preferences,
        occasion: str, season: str,
        collab_map: Dict[int, float],
    ) -> Dict[str, float]:
        skin_tone = getattr(profile, 'skin_tone', None) if profile else None
        return {
            'style_match': self._calculate_style_match_score(outfit, preferences, skin_tone),
            'body_type':   self._calculate_body_type_score(outfit, profile),
            'comfort':     self._calculate_occasion_score(outfit, occasion),
            'trend':          self._calculate_season_score(outfit, season),
            'purchasability': self._calculate_purchasability_score(outfit),
            'feedback':       collab_map.get(outfit.id, 0.5),
        }

    def _calculate_style_match_score(self, outfit, preferences, skin_tone: str = None) -> float:
        """
        Skin-tone Ã— outfit color harmony (primary driver, 35 % weight).
        Also factors in the user's manually saved preferred colors and styles.
        """
        scores = []

        # 1. Skin tone â†’ outfit color compatibility
        if skin_tone and outfit.colors:
            tone_key = skin_tone.lower()
            compatible = SKIN_TONE_COMPATIBLE_COLORS.get(tone_key, [])
            if compatible:
                outfit_colors_normalized = [_normalize_color(c) for c in outfit.colors]
                match = any(
                    any(comp in oc or oc in comp for comp in compatible)
                    for oc in outfit_colors_normalized
                )
                # Strong signal: match=1.0, mismatch=0.10
                scores.append(1.0 if match else 0.10)

        # 2. User's preferred color list
        if preferences and preferences.preferred_colors and outfit.colors:
            color_match = any(c in outfit.colors for c in preferences.preferred_colors)
            scores.append(1.0 if color_match else 0.40)

        # 3. User's preferred style categories
        if preferences and preferences.preferred_styles and outfit.style_type:
            style_match = outfit.style_type in preferences.preferred_styles
            scores.append(1.0 if style_match else 0.40)

        return round(sum(scores) / len(scores), 2) if scores else 0.55

    def _calculate_body_type_score(self, outfit, profile) -> float:
        """Body type / shape compatibility (25 % weight).

        Priority:
          1. outfit.body_type_compatibility field (explicit list, most accurate)
          2. style_type keyword lookup (legacy fallback)
        """
        if not profile or not profile.body_type:
            return 0.5

        body_type = profile.body_type.lower()

        # Check the explicit body_type_compatibility list first
        if outfit.body_type_compatibility:
            compat = [bt.lower() for bt in outfit.body_type_compatibility]
            if 'all' in compat:
                return 0.85
            if body_type in compat:
                return 1.0
            return 0.30  # explicitly incompatible

        # Fallback: style_type keyword lookup
        gender  = (profile.gender or '').lower()
        mapping = MALE_BODY_TYPE_STYLES if gender == 'male' else FEMALE_BODY_TYPE_STYLES
        suitable = mapping.get(body_type, [])
        if outfit.style_type and any(s in outfit.style_type.lower() for s in suitable):
            return 0.90
        return 0.50

    def _calculate_occasion_score(self, outfit, occasion: str) -> float:
        """
        Occasion suitability (20 % weight).
          1.0  exact match
          0.70 user selected 'all' (any occasion accepted)
          0.10 mismatch
        """
        if not occasion or occasion == 'all':
            return 0.70
        if outfit.occasion and outfit.occasion.lower() == occasion.lower():
            return 1.0
        return 0.10

    def _calculate_season_score(self, outfit, season: str) -> float:
        """
        Season suitability (10 % weight).
          1.0  exact match
          0.80 outfit is tagged 'all' seasons
          0.50 user selected 'all seasons'
          0.10 mismatch
        """
        if not season or season == 'all':
            return 0.50
        outfit_season = (outfit.season or '').lower()
        if outfit_season == season.lower():
            return 1.0
        if outfit_season in ('all', ''):
            return 0.80
        return 0.10

    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        total = sum(scores[k] * self.weights.get(k, 0.0) for k in scores)
        return round(total, 2)

    def _calculate_purchasability_score(self, outfit) -> float:
        """
        Purchasability (10 % weight).
          1.0  Real product_url and in_stock == True
          0.30 No product URL or placeholder URL (can't be bought)
          0.00 Out of stock
        """
        if not outfit.in_stock:
            return 0.0
            
        url = outfit.product_url
        if not url:
            return 0.30
        
        url_lower = url.lower()
        if 'aurafit.store' in url_lower or 'example.com' in url_lower or 'placeholder' in url_lower:
            return 0.30
            
        # Heavy bonus for real purchasable items
        if getattr(outfit, 'purchasable', False):
            return 1.0
            
        return 0.50

    def _generate_shopping_links(self, outfit, viewer_gender: str = '') -> Dict[str, str]:
        """Return exact, verified direct product links for the outfit.
        NEVER generates search query URLs (e.g. /s?k= or /search?q=).
        Preserves exact product identity and direct retailer destinations."""
        url = getattr(outfit, 'product_url', None) or ''
        from models.outfit import Outfit
        if not Outfit.is_exact_product_url(url):
            return {}

        url_lower = url.lower()
        store_lower = (getattr(outfit, 'store', None) or getattr(outfit, 'brand', None) or '').lower()

        # Route to exact platform if identified, preserving exact direct URL
        if 'amazon.' in url_lower or 'amazon' in store_lower:
            return {'amazon': url}
        elif 'myntra.' in url_lower or 'myntra' in store_lower:
            return {'myntra': url}
        elif 'flipkart.' in url_lower or 'flipkart' in store_lower:
            return {'flipkart': url}
        elif 'ajio.' in url_lower or 'ajio' in store_lower:
            return {'ajio': url}
        elif 'zara.' in url_lower or 'zara' in store_lower:
            return {'zara': url}
        elif 'hm.com' in url_lower or 'h&m' in store_lower:
            return {'hm': url}
        elif 'nykaa' in url_lower or 'nykaa' in store_lower:
            return {'nykaa': url}
        elif 'meesho' in url_lower or 'meesho' in store_lower:
            return {'meesho': url}
        else:
            return {'direct': url}
