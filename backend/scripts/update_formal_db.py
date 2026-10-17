import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.outfit import Outfit

app = create_app()
with app.app_context():
    formal_updates = {
        418: {
            "name": "Symbol Premium Women's Black Structured Tailored Formal Sheath Dress",
            "image_url": "https://m.media-amazon.com/images/I/61aPtlDki1L._AC_UL600_.jpg",
            "product_url": "https://www.amazon.in/dp/B0DNM4YTWZ",
            "brand": "Symbol Premium",
            "store": "Amazon",
            "price": 2499.0,
            "original_price": 3999.0,
            "discount": "38% off",
            "description": "Tailored formal sheath dress with structured notched neckline and defined waist seam designed for corporate and formal wear.",
            "occasion": "formal",
            "style_type": "formal",
            "colors": ["black"],
            "gender": "female",
            "category": "dress",
            "source": "serpapi",
            "external_id": "serpapi_amz_formal_b0dnm4ytwz",
            "in_stock": True,
            "purchasable": True
        },
        419: {
            "name": "Life With Pockets Women's Black Tailored Formal Blazer Sheath Dress",
            "image_url": "https://m.media-amazon.com/images/I/61vM-8z8sbL._AC_UL600_.jpg",
            "product_url": "https://www.amazon.in/dp/B0CMCPJZVT",
            "brand": "Life With Pockets",
            "store": "Amazon",
            "price": 3299.0,
            "original_price": 4999.0,
            "discount": "34% off",
            "description": "Structured long-sleeve formal blazer sheath dress with lapel collar and tailored silhouette for business formal occasions.",
            "occasion": "formal",
            "style_type": "formal",
            "colors": ["black"],
            "gender": "female",
            "category": "dress",
            "source": "serpapi",
            "external_id": "serpapi_amz_formal_b0cmcpjzvt",
            "in_stock": True,
            "purchasable": True
        },
        426: {
            "name": "Symbol Premium Women's Camel Structured Formal Sheath Midi Dress",
            "image_url": "https://m.media-amazon.com/images/I/61QyERxxPiL._AC_UL600_.jpg",
            "product_url": "https://www.amazon.in/dp/B0FWBJRJW3",
            "brand": "Symbol Premium",
            "store": "Amazon",
            "price": 2199.0,
            "original_price": 3499.0,
            "discount": "37% off",
            "description": "Structured sleeveless formal sheath midi dress with contrast piping and clean tailored silhouette.",
            "occasion": "formal",
            "style_type": "formal",
            "colors": ["tan", "camel"],
            "gender": "female",
            "category": "dress",
            "source": "serpapi",
            "external_id": "serpapi_amz_formal_b0fwbjrjw3",
            "in_stock": True,
            "purchasable": True
        },
        427: {
            "name": "Aaryavar Women's Red Structured Formal Knee-Length Sheath Dress",
            "image_url": "https://m.media-amazon.com/images/I/4137aqbDcqL._AC_UL600_.jpg",
            "product_url": "https://www.amazon.in/dp/B07R9X9B4R",
            "brand": "Aaryavar",
            "store": "Amazon",
            "price": 1299.0,
            "original_price": 2499.0,
            "discount": "48% off",
            "description": "Red structured formal knee-length sheath dress with jewel neckline and clean tailored architectural lines.",
            "occasion": "formal",
            "style_type": "formal",
            "colors": ["red"],
            "gender": "female",
            "category": "dress",
            "source": "serpapi",
            "external_id": "serpapi_amz_formal_b07r9x9b4r",
            "in_stock": True,
            "purchasable": True
        }
    }

    for outfit_id, data in formal_updates.items():
        outfit = Outfit.query.get(outfit_id)
        if not outfit:
            outfit = Outfit(id=outfit_id)
            db.session.add(outfit)
        for k, v in data.items():
            setattr(outfit, k, v)
        print(f"Updated Outfit {outfit_id}: {outfit.name}")

    db.session.commit()
    print("Database committed successfully.")
