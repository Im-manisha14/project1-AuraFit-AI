import os
import sys
import json
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from extensions import db
from models.outfit import Outfit

def clean_title(name):
    # Remove retailer suffixes like "by Myntra", "by Nykaa", etc.
    s = re.sub(r'\s+by\s+[A-Za-z0-9\s]+$', '', name, flags=re.IGNORECASE)
    # Remove leading brand if duplicated
    return s.strip()

def derive_pieces(outfit):
    name = outfit.name or "Stylish Outfit"
    cleaned = clean_title(name)
    occasion = (outfit.occasion or 'casual').lower()
    style = (outfit.style_type or 'casual').lower()
    gender = (outfit.gender or 'female').lower()
    name_lower = name.lower()

    # Default values
    top = None
    bottom = None
    shoes = None
    accessories = ["Classic Watch", "Pendant Necklace"]

    # 1. Ethnic / Indian wear
    if any(k in name_lower for k in ['kurta', 'anarkali', 'saree', 'lehenga', 'chanderi', 'ethnic', 'salwar']):
        if 'anarkali' in name_lower:
            top = f"{cleaned.split('Dress')[0].strip()} Kurta"
            bottom = "Flared Anarkali & Churidar"
        elif 'kurta' in name_lower:
            top = cleaned
            bottom = "Matching Palazzo / Pants"
        else:
            top = cleaned
            bottom = "Traditional Flared Hem"
        shoes = "Embroidered Mojaris / Juttis"
        accessories = ["Kundan Jhumkas", "Embellished Potli"]

    # 2. Bodycon / Slip / Party / Glamorous
    elif any(k in name_lower for k in ['slip', 'bodycon', 'wrap', 'party', 'cocktail', 'metallic']) or style in ['party', 'glamorous']:
        if 'slip' in name_lower:
            top = "Satin Cowl-Neck Slip Dress"
            bottom = "Fluted Midi Hemline"
        elif 'bodycon' in name_lower:
            top = "Fitted Silhouette Bodycon Dress"
            bottom = "Sculpted Knee-Length Hem"
        elif 'wrap' in name_lower:
            top = "Pleated V-Neck Wrap Bodice"
            bottom = "Asymmetric Draped Hem"
        else:
            top = cleaned
            bottom = "Tailored Evening Hemline"
        shoes = "Strappy Stiletto Heels"
        accessories = ["Metallic Clutch", "Crystal Drop Earrings"]

    # 3. Work / Formal / Shirt Dress
    elif any(k in name_lower for k in ['shirt dress', 'belted', 'work', 'formal', 'peplum', 'blazer']) or occasion in ['work', 'formal']:
        if 'shirt dress' in name_lower:
            top = "Collared Button-Up Bodice"
            bottom = "Belted A-Line Midi Skirt"
        elif 'peplum' in name_lower:
            top = "Structured Peplum Bodice"
            bottom = "Tailored Pencil Hem"
        else:
            top = f"{cleaned} Bodice"
            bottom = "Tailored Straight Hem"
        shoes = "Pointed-Toe Leather Pumps"
        accessories = ["Structured Leather Tote", "Minimalist Watch"]

    # 4. Sporty / Gym / Athleisure
    elif any(k in name_lower for k in ['legging', 'sports', 'bra', 'gym', 'jogger', 'sweat', 'athletic']) or style in ['sporty', 'athleisure']:
        top = "Moisture-Wicking Athletic Top"
        bottom = "High-Waist Compression Leggings"
        shoes = "Running Sneakers"
        accessories = ["Sports Smartwatch", "Duffel Bag"]

    # 5. Casual / Tiered / Smocked / Maxi / Sweater dress
    elif any(k in name_lower for k in ['tiered', 'maxi', 'smocked', 'sweater dress', 'flare', 'floral', 'ribbed']) or style in ['chic', 'casual', 'bohemian']:
        if 'tiered' in name_lower:
            top = "Puff-Sleeve Tiered Bodice"
            bottom = "Tiered Flared Midi Hem"
        elif 'sweater dress' in name_lower:
            top = "Ribbed Knit Sweater Dress"
            bottom = "Fitted Ribbed Hem"
            shoes = "Ankle Chelsea Boots"
        elif 'smocked' in name_lower:
            top = "Smocked Elasticated Bodice"
            bottom = "Flowy Ruffle-Trim Hem"
        elif 'maxi' in name_lower:
            top = "Floral Georgette Bodice"
            bottom = "Flowy Tiered Maxi Hem"
        else:
            top = cleaned
            bottom = "A-Line Flared Silhouette"
        if not shoes:
            shoes = "Classic White Sneakers"
        accessories = ["Canvas Tote Bag", "Layered Gold Necklace"]

    # 6. Fallback
    else:
        top = cleaned
        bottom = "A-Line Complementary Hem"
        shoes = "Block Heel Slide Sandals"
        accessories = ["Structured Handbag", "Dainty Studs"]

    return {
        "top": top[:60],
        "bottom": bottom[:60],
        "shoes": shoes[:50],
        "accessories": accessories
    }

def main():
    with app.app_context():
        outfits = Outfit.query.all()
        updated_count = 0
        for o in outfits:
            if not o.top or not o.bottom or not o.shoes or not o.accessories:
                pieces = derive_pieces(o)
                if not o.top:
                    o.top = pieces["top"]
                if not o.bottom:
                    o.bottom = pieces["bottom"]
                if not o.shoes:
                    o.shoes = pieces["shoes"]
                if not o.accessories or len(o.accessories) == 0:
                    o.accessories = pieces["accessories"]
                updated_count += 1
        
        db.session.commit()
        print(f"Successfully updated pieces for {updated_count} outfits in aurafit.db!")

if __name__ == '__main__':
    main()
