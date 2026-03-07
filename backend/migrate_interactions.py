"""
Migration: create outfit_interactions table
Run once: python migrate_interactions.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'aurafit.db')


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS outfit_interactions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            outfit_id        INTEGER NOT NULL REFERENCES outfits(id) ON DELETE CASCADE,
            interaction_type TEXT    NOT NULL DEFAULT 'view',
            created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_outfit_interactions_user_id
        ON outfit_interactions (user_id)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_outfit_interactions_outfit_id
        ON outfit_interactions (outfit_id)
    """)

    conn.commit()
    conn.close()
    print("✅ outfit_interactions table created (or already existed).")


if __name__ == '__main__':
    run()
