import os
import sqlite3

db_path = 'aurafit.db' if os.path.exists('aurafit.db') else os.path.join('backend', 'aurafit.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

broken_ids = [312, 314, 315, 316, 318, 338, 339, 370, 381]
cursor.execute(f"UPDATE outfits SET in_stock = 0, purchasable = 0 WHERE id IN ({','.join(map(str, broken_ids))})")

patterns = ["%1mO2P%", "%61J7K%", "%1V2w3%", "%dummy%", "%placeholder%", "%T67U1A%"]
for pat in patterns:
    cursor.execute("UPDATE outfits SET in_stock = 0, purchasable = 0 WHERE image_url LIKE ?", (pat,))

conn.commit()
print("Deactivated broken image items in database. Total changes:", conn.total_changes)

# Verify count of in_stock items with broken images
cursor.execute("SELECT id, name, image_url FROM outfits WHERE in_stock = 1 AND (image_url IS NULL OR image_url = '')")
empty_imgs = cursor.fetchall()
print("In-stock items with empty image:", len(empty_imgs))

conn.close()
