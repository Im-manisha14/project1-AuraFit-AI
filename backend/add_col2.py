"""Add body_type_compatibility column directly to aurafit.db."""
import sqlite3, os

db_path = 'aurafit.db'
if not os.path.exists(db_path):
    print(f'ERROR: {db_path} not found.')
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('PRAGMA table_info(outfits)')
    cols = [row[1] for row in cur.fetchall()]
    print('Current columns:', cols)
    if 'body_type_compatibility' not in cols:
        cur.execute('ALTER TABLE outfits ADD COLUMN body_type_compatibility JSON')
        conn.commit()
        print('column body_type_compatibility added.')
    else:
        print('Column already exists.')
    conn.close()
