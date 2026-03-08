"""One-shot script: add body_type_compatibility column to the SQLite DB."""
import sqlite3, glob, os

search_paths = [
    'instance/*.db', 'instance/*.sqlite',
    '*.db', '*.sqlite',
    'instance/stylesync.db', 'instance/app.db',
]

found = []
for pattern in search_paths:
    found.extend(glob.glob(pattern))

if not found:
    print("No SQLite DB found. Listing instance/ contents:")
    if os.path.exists('instance'):
        print(os.listdir('instance'))
    else:
        print("  instance/ folder not found")
else:
    for db_path in set(found):
        print(f"Found DB: {db_path}")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(outfits)")
        cols = [row[1] for row in cur.fetchall()]
        print(f"  Current columns: {cols}")
        if 'body_type_compatibility' not in cols:
            cur.execute('ALTER TABLE outfits ADD COLUMN body_type_compatibility JSON')
            conn.commit()
            print("  ✅ body_type_compatibility column added.")
        else:
            print("  ℹ️  Column already exists.")
        conn.close()
