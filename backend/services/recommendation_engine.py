import urllib.parse
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User, UserProfile, StylePreference
    from models.outfit import Outfit

# ---------------------------------------------------------------------------
# Skin-tone â†’ compatible outfit color palette
# ---------------------------------------------------------------------------
SKIN_TONE_COMPATIBLE_COLORS = {
    'fair': [
        'lavender', 'pastel blue', 'soft pink', 'navy', 'emerald',
        'burgundy', 'black', 'white', 'gray', 'silver', 'mint', 'dusty rose',
    ],
    'light': [
        'peach', 'beige', 'mint', 'coral', 'olive', 'warm brown',
        'dusty rose', 'blush', 'camel', 'ivory', 'terracotta', 'rust',
    ],
    'medium': [
        'emerald', 'teal', 'mustard', 'purple', 'royal blue', 'terracotta',
        'deep purple', 'chocolate', 'rust', 'jewel tone', 'burnt orange', 'forest green',
        'olive', 'beige',
    ],
    'olive': [
        'earth tones', 'maroon', 'cream', 'gold', 'forest green', 'camel',
        'rust', 'chocolate brown', 'khaki', 'warm brown', 'brick red', 'mustard',
    ],
    'deep': [
        'royal blue', 'yellow', 'white', 'orange', 'electric blue', 'fuchsia',
        'gold', 'cobalt', 'bright red', 'hot pink', 'lime green',
    ],
}

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
            'style_match': 0.40,   # skin-tone color harmony
            'body_type':   0.25,   # body type / shape compatibility
            'comfort':     0.20,   # occasion suitability
            'trend':       0.10,   # season suitability
            'feedback':    0.05,   # collaborative filtering signal
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
        limit: int = 10,
    ) -> List[Dict]:
        """Generate personalized outfit recommendations using hybrid filtering."""
        from models.outfit import Outfit, Recommendation

        # Step 1 â€“ Load the full outfit catalogue
        outfits = Outfit.query.all()

        # Step 2 – Gender filtering (STRICT – never fall back to wrong gender)
        #   Male   → male  + unisex outfits only
        #   Female → female + unisex outfits only
        if profile and profile.gender:
            gender = profile.gender.lower()
            if gender in ('male', 'female'):
                outfits = [
                    o for o in outfits
                    if (o.gender or 'unisex').lower() in (gender, 'unisex')
                ]

        # Step 3 â€“ Collaborative signal map {outfit_id: 0.0â€“1.0}
        collab_map = self._build_collaborative_map(profile)

        # Step 4 â€“ Score every outfit
        scored = []
        for outfit in outfits:
            scores = self._calculate_scores(
                outfit, profile, preferences, occasion, season, collab_map
            )
            overall = self._calculate_overall_score(scores)
            outfit_dict = outfit.to_dict()
            viewer_gender = (profile.gender or '').lower() if profile else ''
            outfit_dict['shopping_links'] = self._generate_shopping_links(outfit, viewer_gender)
            scored.append({
                'outfit':        outfit_dict,
                'scores':        scores,
                'overall_score': overall,
            })

        # Step 5 â€“ Rank by overall score, trim to limit
        scored.sort(key=lambda x: x['overall_score'], reverse=True)
        top = scored[:limit]

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
            'trend':       self._calculate_season_score(outfit, season),
            'feedback':    collab_map.get(outfit.id, 0.5),
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
                outfit_colors_lower = [c.lower() for c in outfit.colors]
                match = any(
                    any(comp in oc or oc in comp for comp in compatible)
                    for oc in outfit_colors_lower
                )
                scores.append(0.90 if match else 0.40)

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
        """Body type / shape compatibility (25 % weight)."""
        if not profile or not profile.body_type:
            return 0.5

        body_type = profile.body_type.lower()
        gender    = (profile.gender or '').lower()
        mapping   = MALE_BODY_TYPE_STYLES if gender == 'male' else FEMALE_BODY_TYPE_STYLES

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

    # -----------------------------------------------------------------------
    # Shopping links
    # -----------------------------------------------------------------------

    def _generate_shopping_links(self, outfit, viewer_gender: str = '') -> Dict[str, str]:
        """Return gender-aware fashion-platform search URLs for the outfit.
        Prepends 'women's' or 'men's' so every platform returns the correct
        gender category. Skips prefix if the outfit name already contains it."""
        outfit_gender = (outfit.gender or '').lower()
        name_lower = (outfit.name or '').lower()

        # Resolve which gender label to use for the search prefix
        if outfit_gender == 'female':
            gender_label = "women's"
        elif outfit_gender == 'male':
            gender_label = "men's"
        elif viewer_gender == 'female':
            gender_label = "women's"
        elif viewer_gender == 'male':
            gender_label = "men's"
        else:
            gender_label = ''

        parts = []
        # Only add gender prefix if not already present in the outfit name
        if gender_label and gender_label.rstrip("'s") not in name_lower and "men" not in name_lower and "women" not in name_lower:
            parts.append(gender_label)

        # Outfit name is the primary anchor
        if outfit.name:
            parts.append(outfit.name)
        elif outfit.style_type:
            parts.append(outfit.style_type)

        # Add occasion/style context if not already in the name
        if outfit.occasion and outfit.occasion.lower() not in name_lower:
            parts.append(outfit.occasion)
        if outfit.style_type and outfit.style_type.lower() not in name_lower:
            parts.append(outfit.style_type)

        search_term = ' '.join(parts[:4]) if parts else 'fashion outfit'
        q = urllib.parse.quote_plus(search_term)
        slug = urllib.parse.quote_plus(search_term.replace(' ', '-'))

        return {
            'myntra':        f'https://www.myntra.com/{slug}',
            'flipkart':      f'https://www.flipkart.com/search?q={q}&otracker=search',
            'ajio':          f'https://www.ajio.com/search/?text={q}',
            'meesho':        f'https://www.meesho.com/search?q={q}',
            'nykaa_fashion': f'https://www.nykaafashion.com/search?q={q}',
            'amazon':        f'https://www.amazon.in/s?k={q}&i=apparel',
            'hm':            f'https://www2.hm.com/en_in/search-results.html?q={q}',
            'zara':          f'https://www.zara.com/in/en/search?searchTerm={q}',
        }
