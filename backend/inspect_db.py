import sqlite3, os

db_path = 'aurafit.db'
if not os.path.exists(db_path):
    print('aurafit.db not found. Files in current dir:', os.listdir('.'))
else:
    print(f'Found: {db_path}')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cur.fetchall()]
    print('Tables:', tables)
    if 'outfits' in tables:
        cur.execute('PRAGMA table_info(outfits)')
        cols = [row[1] for row in cur.fetchall()]
        print('outfit columns:', cols)
        cur.execute('SELECT COUNT(*) FROM outfits')
        print('outfit count:', cur.fetchone()[0])
    conn.close()
