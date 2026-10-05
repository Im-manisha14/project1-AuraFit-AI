import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from backend.services.occasion_classifier import OccasionClassifier

db_path = os.path.abspath('backend/aurafit.db')
print(f"Connecting to {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT id, name, category, description, occasion FROM outfits')
rows = cursor.fetchall()
print(f'Total outfits in db: {len(rows)}')

updated = 0
occasion_counts = {}
for oid, name, cat, desc, old_occ in rows:
    text = f"{name or ''} {cat or ''} {desc or ''}"
    primary_occ = OccasionClassifier.detect_primary_occasion(text)
    occasion_counts[primary_occ] = occasion_counts.get(primary_occ, 0) + 1
    if primary_occ != old_occ:
        cursor.execute('UPDATE outfits SET occasion = ? WHERE id = ?', (primary_occ, oid))
        updated += 1

conn.commit()
conn.close()
print(f'Updated {updated} outfits.')
print(f'New DB occasion distribution: {occasion_counts}')
