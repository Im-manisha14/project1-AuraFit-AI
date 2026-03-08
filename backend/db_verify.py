import sqlite3
import os

db_path = 'aurafit.db'
print('CWD:', os.getcwd())
print('DB exists:', os.path.exists(db_path))
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print('Tables:', tables)
for (tname,) in tables:
    cur.execute(f"SELECT COUNT(*) FROM {tname}")
    print(f"  {tname}: {cur.fetchone()[0]} rows")
cur.execute("SELECT occasion, gender, COUNT(*) FROM outfits GROUP BY occasion, gender")
for r in cur.fetchall():
    print(' ', r)
conn.close()
