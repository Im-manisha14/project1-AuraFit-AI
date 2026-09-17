import os
import csv
import sys
import argparse
from urllib.parse import urlparse

# Ensure we can import the app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from app import create_app
from extensions import db
from models.outfit import Outfit
from services.recommendation_engine import _normalize_color

def is_valid_url(url: str) -> bool:
    """Returns True if the URL is a real http/https URL and not an internal placeholder."""
    if not url:
        return False
    url = url.lower()
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    
    # Reject obvious placeholders
    parsed = urlparse(url)
    domain = parsed.netloc
    
    if any(p in domain for p in ['aurafit.store', 'example.com', 'localhost', '127.0.0']):
        return False
        
    return True

def import_csv(filepath: str):
    """Imports the given CSV file into the database safely."""
    
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
        
    app = create_app()
    with app.app_context():
        stats = {
            'inserted': 0,
            'updated': 0,
            'skipped_duplicate': 0,
            'errors': 0
        }
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            row_count = 0
            
            for row in reader:
                row_count += 1
                try:
                    # 1. Validation
                    ext_id = row.get('external_id', '').strip()
                    if not ext_id:
                        print(f"Row {row_count}: Skipped - Missing 'external_id'")
                        stats['errors'] += 1
                        continue
                        
                    # Skip placeholder examples
                    if 'PLACEHOLDER' in ext_id:
                        continue
                        
                    name = row.get('name', '').strip()
                    if not name:
                        print(f"Row {row_count} ({ext_id}): Skipped - Missing 'name'")
                        stats['errors'] += 1
                        continue
                        
                    price_str = row.get('price', '').strip()
                    try:
                        price = float(price_str)
                    except ValueError:
                        print(f"Row {row_count} ({ext_id}): Skipped - Invalid price '{price_str}'")
                        stats['errors'] += 1
                        continue
                        
                    product_url = row.get('product_url', '').strip()
                    if not is_valid_url(product_url):
                        print(f"Row {row_count} ({ext_id}): Skipped - Invalid product_url '{product_url}'")
                        stats['errors'] += 1
                        continue
                        
                    # Parse arrays
                    raw_colors = [c.strip() for c in row.get('colors', '').split(',') if c.strip()]
                    normalized_colors = list(set([_normalize_color(c) for c in raw_colors]))
                    
                    # 2. Check if product already exists
                    existing = Outfit.query.filter_by(external_id=ext_id).first()
                    
                    if existing:
                        # Additive update mode: we update pricing, availability, and URL
                        existing.price = price
                        existing.in_stock = str(row.get('in_stock', '')).strip().lower() == 'true'
                        existing.product_url = product_url
                        stats['updated'] += 1
                        # We intentionally do not overwrite the user's manual style categorization if it exists,
                        # but we update the critical purchasability data.
                    else:
                        # 3. Create new record
                        o = Outfit(
                            external_id=ext_id,
                            name=name,
                            brand=row.get('brand', '').strip(),
                            category=row.get('category', '').strip(),
                            gender=row.get('gender', 'unisex').strip().lower(),
                            colors=normalized_colors,
                            image_url=row.get('image_url', '').strip(),
                            price=price,
                            currency=row.get('currency', 'USD').strip().upper(),
                            store=row.get('retailer', '').strip(),
                            product_url=product_url,
                            in_stock=str(row.get('in_stock', '')).strip().lower() == 'true',
                            occasion=row.get('occasion', 'casual').strip().lower(),
                            season=row.get('season', 'all').strip().lower(),
                            style_type=row.get('style', '').strip().lower(),
                            # parse compatibility if provided, else None
                            body_type_compatibility=[b.strip().lower() for b in row.get('body_types', '').split(',') if b.strip()] or None
                        )
                        db.session.add(o)
                        stats['inserted'] += 1
                        
                except Exception as e:
                    print(f"Row {row_count} ({ext_id}): Failed to process due to error: {e}")
                    stats['errors'] += 1
                    
        try:
            db.session.commit()
            print("\nImport Complete!")
            print(f"  Inserted new: {stats['inserted']}")
            print(f"  Updated existing: {stats['updated']}")
            print(f"  Invalid rows: {stats['errors']}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nDatabase commit failed: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import real products from CSV into AuraFit database.')
    parser.add_argument('filepath', help='Path to the CSV file')
    args = parser.parse_args()
    import_csv(args.filepath)
