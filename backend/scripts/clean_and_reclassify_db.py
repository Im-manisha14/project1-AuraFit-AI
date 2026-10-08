#!/usr/bin/env python3
"""
AuraFit AI — Database Deduplication & Deterministic Occasion Reclassification
Step 2, 5, 6, 13:
1. Identifies and deactivates duplicate outfit rows sharing the same canonical product identity,
   canonical product URL, or image key.
2. Deterministically assigns every active outfit its genuine primary_occasion and primary_season
   using OccasionClassifier and SeasonClassifier (never search query mutations).
3. Standardizes external_ids by removing legacy 'serpapi_sim_' prefixes.
"""

import os
import sys
import sqlite3

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from extensions import db
from models.outfit import Outfit
from services.occasion_classifier import OccasionClassifier, SeasonClassifier
from services.product_validator import canonical_product_key, canonicalize_url, extract_image_key

def clean_and_reclassify():
    app = create_app()
    with app.app_context():
        outfits = Outfit.query.filter_by(in_stock=True, purchasable=True).all()
        print(f"[DB CLEAN] Found {len(outfits)} currently active outfits in database.")

        seen_keys = {}
        seen_urls = {}
        seen_imgs = {}

        deactivated_duplicates = 0
        reclassified_occasions = 0
        reclassified_seasons = 0
        standardized_ids = 0

        for o in outfits:
            o_dict = o.to_dict()
            canon_key = canonical_product_key(o_dict)
            canon_url = canonicalize_url(o.product_url)
            img_key = extract_image_key(o.image_url)

            # Check if this physical product has already been retained under another ID
            dupe_of = None
            if canon_key and canon_key in seen_keys:
                dupe_of = seen_keys[canon_key]
            elif canon_url and canon_url in seen_urls:
                dupe_of = seen_urls[canon_url]
            elif img_key and img_key in seen_imgs:
                dupe_of = seen_imgs[img_key]

            if dupe_of:
                # Mark as duplicate and deactivate
                o.in_stock = False
                o.purchasable = False
                deactivated_duplicates += 1
                print(f"  [DEACTIVATE DUPLICATE] ID {o.id} '{o.name[:40]}' (duplicate of ID {dupe_of.id})")
                continue

            # This is the primary unique record for this product
            if canon_key:
                seen_keys[canon_key] = o
            if canon_url:
                seen_urls[canon_url] = o
            if img_key:
                seen_imgs[img_key] = o

            # Standardize external_id if it contains serpapi_sim_
            if o.external_id and 'sim_' in o.external_id:
                clean_ext = o.external_id.replace('serpapi_sim_', 'serpapi_')
                o.external_id = clean_ext
                standardized_ids += 1

            # Deterministic classification based on product itself
            det_occ = OccasionClassifier.detect_primary_occasion(o_dict) or 'casual'
            det_seas = SeasonClassifier.detect_primary_season(o_dict) or 'all'

            if o.occasion != det_occ:
                old_occ = o.occasion
                o.occasion = det_occ
                reclassified_occasions += 1
                # print(f"  [RECLASSIFY OCCASION] ID {o.id} '{o.name[:35]}': {old_occ} -> {det_occ}")

            if o.season != det_seas:
                o.season = det_seas
                reclassified_seasons += 1

        db.session.commit()
        print("\n" + "=" * 60)
        print("DATABASE DEDUPLICATION & RECLASSIFICATION SUMMARY")
        print("=" * 60)
        print(f"Total active outfits evaluated  : {len(outfits)}")
        print(f"Duplicate outfits deactivated   : {deactivated_duplicates}")
        print(f"Occasions reclassified          : {reclassified_occasions}")
        print(f"Seasons reclassified            : {reclassified_seasons}")
        print(f"External IDs standardized       : {standardized_ids}")
        remaining = Outfit.query.filter_by(in_stock=True, purchasable=True).count()
        print(f"Remaining genuine active outfits: {remaining}")
        print("=" * 60)

if __name__ == '__main__':
    clean_and_reclassify()
