import sqlite3, os

db_path = 'aurafit.db'
print("DB file exists:", os.path.exists(db_path))
print("DB size:", os.path.getsize(db_path), "bytes")

conn = sqlite3.connect(db_path)
c = conn.cursor()

tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])

for tbl in tables:
    cnt = c.execute(f"SELECT COUNT(*) FROM {tbl[0]}").fetchone()[0]
    print(f"  {tbl[0]}: {cnt} rows")

# Sample outfit check
print("\nSample outfits (top 5 by trend score):")
rows = c.execute("SELECT id, name, occasion, season, is_trending, image_url IS NOT NULL as has_img FROM outfits ORDER BY trend_score DESC LIMIT 5").fetchall()
for r in rows:
    print(f"  [{r[0]}] {r[1]} | {r[2]}/{r[3]} | trending={r[4]} | image={bool(r[5])}")

conn.close()
print("\nDatabase looks healthy!")
