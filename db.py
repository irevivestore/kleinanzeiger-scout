# db.py
import sqlite3
import json
from datetime import datetime

DB_PATH = "config.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS configs (
            modell TEXT PRIMARY KEY,
            verkaufspreis INTEGER,
            wunsch_marge INTEGER,
            reparaturkosten TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id TEXT PRIMARY KEY,
            modell TEXT,
            title TEXT,
            price REAL,
            link TEXT,
            image TEXT,
            beschreibung TEXT,
            versand BOOLEAN,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO configs (modell, verkaufspreis, wunsch_marge, reparaturkosten) VALUES (?, ?, ?, ?)",
              (modell, verkaufspreis, wunsch_marge, json.dumps(reparaturkosten_dict)))
    conn.commit()
    conn.close()


def load_config(modell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT verkaufspreis, wunsch_marge, reparaturkosten FROM configs WHERE modell = ?", (modell,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "verkaufspreis": row[0],
            "wunsch_marge": row[1],
            "reparaturkosten": json.loads(row[2])
        }
    return None


def save_advert(ad):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Prüfen, ob bereits vorhanden
    c.execute("SELECT updated_at, price FROM ads WHERE id = ?", (ad['id'],))
    row = c.fetchone()
    now = datetime.now().isoformat()

    if row:
        old_price = row[1]
        if old_price != ad['price']:
            c.execute("""
                UPDATE ads SET price=?, updated_at=? WHERE id=?
            """, (ad['price'], now, ad['id']))
    else:
        c.execute("""
            INSERT INTO ads (id, modell, title, price, link, image, beschreibung, versand, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ad['id'], ad['modell'], ad['title'], ad['price'], ad['link'], ad['image'],
            ad['beschreibung'], ad['versand'], now, now
        ))

    conn.commit()
    conn.close()


def get_existing_advert(modell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, price, link, image, beschreibung, versand, created_at, updated_at FROM ads WHERE modell = ? ORDER BY updated_at DESC", (modell,))
    rows = c.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "title": row[1],
            "price": row[2],
            "link": row[3],
            "image": row[4],
            "beschreibung": row[5],
            "versand": bool(row[6]),
            "created_at": row[7],
            "updated_at": row[8],
        })
    return result
