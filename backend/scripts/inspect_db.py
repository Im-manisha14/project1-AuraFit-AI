import sqlite3

conn = sqlite3.connect('backend/aurafit.db')
c = conn.cursor()
c.execute("SELECT id, name, occasion, price FROM outfits WHERE category = 'dress'")
rows = c.fetchall()
print(f"Total dresses: {len(rows)}")
for r in rows:
    print(f"ID {r[0]}: {r[1][:50]} | Occ: {r[2]} | Price: {r[3]}")
conn.close()
