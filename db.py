import sqlite3
import json
from datetime import datetime

DB_PATH = "datenbank.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tabelle für Anzeigen
    c.execute("""
    CREATE TABLE IF NOT EXISTS anzeigen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modell TEXT,
        title TEXT,
        price INTEGER,
        link TEXT UNIQUE,
        image TEXT,
        versand BOOLEAN,
        beschreibung TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # Tabelle für Konfiguration
    c.execute("""
    CREATE TABLE IF NOT EXISTS config (
        modell TEXT PRIMARY KEY,
        verkaufspreis INTEGER,
        wunsch_marge INTEGER,
        reparaturkosten TEXT -- JSON
    )
    """)

    conn.commit()
    conn.close()

def save_advert(ad):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id FROM anzeigen WHERE link = ?", (ad["link"],))
    existing = c.fetchone()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if existing:
        c.execute("""
            UPDATE anzeigen
            SET title = ?, price = ?, image = ?, versand = ?, beschreibung = ?, updated_at = ?
            WHERE link = ?
        """, (
            ad["title"], ad["price"], ad["image"], ad["versand"], ad["beschreibung"], now, ad["link"]
        ))
    else:
        c.execute("""
            INSERT INTO anzeigen (
                modell, title, price, link, image, versand, beschreibung, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ad["modell"], ad["title"], ad["price"], ad["link"],
            ad["image"], ad["versand"], ad["beschreibung"], now, now
        ))

    conn.commit()
    conn.close()

def get_existing_advert(modell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM anzeigen WHERE modell = ?", (modell,))
    rows = c.fetchall()
    conn.close()

    keys = ["id", "modell", "title", "price", "link", "image", "versand", "beschreibung", "created_at", "updated_at"]
    return [dict(zip(keys, row)) for row in rows]

def get_all_ads_for_model(modell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM anzeigen WHERE modell = ?", (modell,))
    rows = c.fetchall()
    conn.close()

    keys = ["id", "modell", "title", "price", "link", "image", "versand", "beschreibung", "created_at", "updated_at"]
    return [dict(zip(keys, row)) for row in rows]

def load_config(modell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT verkaufspreis, wunsch_marge, reparaturkosten FROM config WHERE modell = ?", (modell,))
    row = c.fetchone()
    conn.close()

    if row:
        verkaufspreis, wunsch_marge, reparaturkosten_json = row
        return {
            "verkaufspreis": verkaufspreis,
            "wunsch_marge": wunsch_marge,
            "reparaturkosten": json.loads(reparaturkosten_json)
        }
    else:
        return None

def save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    json_str = json.dumps(reparaturkosten_dict)

    c.execute("""
        INSERT INTO config (modell, verkaufspreis, wunsch_marge, reparaturkosten)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(modell) DO UPDATE SET
            verkaufspreis = excluded.verkaufspreis,
            wunsch_marge = excluded.wunsch_marge,
            reparaturkosten = excluded.reparaturkosten
    """, (modell, verkaufspreis, wunsch_marge, json_str))

    conn.commit()
    conn.close()
