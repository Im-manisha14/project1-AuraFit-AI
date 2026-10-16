#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.dress_style_classifier import (
    classify_dress_style,
    is_style_compatible,
    validate_occasion_and_style
)

test_cases = [
    ('Aahwan Women Striped Bodycon Mini Dress', 'formal', False),
    ('Globus Women White Opaque Stretchable Floral Lace Midi Bodycon Party Dress', 'formal', False),
    ('Savana white draped bodycon dress (l), sexy, elegant, all seasons, off shoulder, draped, party', 'formal', False),
    ('Women Sexy Backless Clubwear Bodycon Mini Dress', 'formal', False),
    ('Women Casual Ribbed Cotton Bodycon T-shirt Dress', 'formal', False),
    ('Annabelle by Pantaloons Puff Sleeve Sheath Dress', 'formal', False),
    ('Annabelle by Pantaloons Puff Sleeve Sheath Dress', 'office', True),
    ('People Sheath Midi Dress (XS) by Myntra', 'formal', False),
    ('Women Black Structured Tailored Formal Sheath Dress', 'formal', True),
    ('Women Navy Blue Structured Crepe Sheath Bodycon Midi Formal Dress', 'formal', True),
    ('Ted Baker Women Luxury White Floral Print Shift Dress', 'formal', False),
    ('Shein Shein Women Notched Neck Extended Sleeve Maxi Sheath Dress For Women', 'formal', False),
    ('Marks & Spencer Women Navy Blue Structured Tailored Formal Sheath Dress', 'formal', True),
    ('Ted Baker London Women Black Tailored Sheath Formal Midi Dress', 'formal', True),
    ('Zara Women Black Structured Tailored Blazer Formal Dress', 'formal', True),
    ('Mango Women Burgundy Structured Pleated Formal Midi Dress', 'formal', True),
    ('Women Office Workwear Tailored Pencil Sheath Dress', 'office', True),
    ('Women Nightclub Sequin Glitter Party Mini Dress', 'office', False),
    ('Women Cotton Everyday Casual Shirt Dress', 'casual', True),
    ('Women Floor Length Black Tie Gala Formal Gown', 'casual', False),
    ('Women Floral Chiffon Wedding Guest Midi Dress', 'wedding', True),
    ('Women White Bridal Gown Wedding Dress for Bride', 'wedding', False),
    ('Women Sequin Shimmer Evening Party Dress', 'party', True),
    ('Women Daily Cotton Casual T-shirt Dress', 'party', False),
    ('Women Traditional Anarkali Kurta Ethnic Dress', 'traditional', True),
    ('Women Western Nightclub Party Mini Dress', 'traditional', False),
    ('Women Festive Embroidered Zari Ethnic Dress', 'festive', True),
    ('Women Plain Office Workwear Sheath Dress', 'festive', False),
    ('Women Tropical Vacation Resort Breezy Sundress', 'vacation', True),
    ('Women Formal Corporate Black Tie Sheath Dress', 'vacation', False),
    ('Women Floral Brunch Daytime Midi Chic Dress', 'brunch', True),
    ('Women Clubwear Nightclub Sequin Mini Dress', 'brunch', False),
    ('Women Satin Slip Romantic Date Night Dress', 'date', True),
    ('Women Corporate Office Sheath Workwear Dress', 'date', False),
]

all_passed = True
print("=== DRESS STYLE & OCCASION CLASSIFICATION AUDIT ===")
for title, occasion, expected in test_cases:
    item = {'title': title, 'description': title}
    style_info = classify_dress_style(item)
    valid, reason, details = validate_occasion_and_style(item, occasion)
    status = 'PASS' if valid == expected else 'FAIL'
    if valid != expected:
        all_passed = False
    print(f"[{status}] {title[:48]:<48} | Req: {occasion:<11} | Exp: {str(expected):<5} | Got: {str(valid):<5} | Style: {style_info['style']} ({style_info.get('bodycon_type')}) | Reason: {reason[:45]}")

print("\n" + "=" * 60)
print(f"TOTAL TEST CASES: {len(test_cases)}")
print(f"ALL TESTS PASSED: {all_passed}")
print("=" * 60)
if not all_passed:
    sys.exit(1)
