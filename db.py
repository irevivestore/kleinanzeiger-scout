# db.py
import sqlite3
import json
from datetime import datetime

DB_PATH = "anzeigen.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS anzeigen (
        link TEXT PRIMARY KEY,
        title TEXT,
        price INTEGER,
        image TEXT,
        beschreibung TEXT,
        versand INTEGER,
        erstellt_am TEXT,
        aktualisiert_am TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS konfigurationen (
        modell TEXT PRIMARY KEY,
        verkaufspreis INTEGER,
        wunschmarge INTEGER,
        defekte TEXT
    )
    """)

    conn.commit()
    conn.close()

def get_existing_advert(link):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM anzeigen WHERE link = ?", (link,))
    row = c.fetchone()
    conn.close()
    return row

def save_advert(ad):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    existing = get_existing_advert(ad["link"])
    jetzt = datetime.now().strftime("%Y-%m-%d")

    if existing:
        # Update nur, wenn sich Preis geändert hat
        if existing[2] != ad["price"]:
            c.execute("""
            UPDATE anzeigen SET
                title = ?, price = ?, image = ?, beschreibung = ?,
                versand = ?, aktualisiert_am = ?
            WHERE link = ?
            """, (
                ad["title"], ad["price"], ad["image"], ad["beschreibung"],
                int(ad["versand"]), jetzt, ad["link"]
            ))
    else:
        c.execute("""
        INSERT INTO anzeigen (link, title, price, image, beschreibung, versand, erstellt_am, aktualisiert_am)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ad["link"], ad["title"], ad["price"], ad["image"],
            ad["beschreibung"], int(ad["versand"]), jetzt, jetzt
        ))

    conn.commit()
    conn.close()

def save_config(modell, config):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT OR REPLACE INTO konfigurationen (modell, verkaufspreis, wunschmarge, defekte)
    VALUES (?, ?, ?, ?)
    """, (
        modell,
        config["verkaufspreis"],
        config["wunschmarge"],
        json.dumps(config["reparaturkosten"])
    ))
    conn.commit()
    conn.close()

def load_config(modell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT verkaufspreis, wunschmarge, defekte FROM konfigurationen WHERE modell = ?", (modell,))
    row = c.fetchone()
    conn.close()

    if row:
        return {
            "verkaufspreis": row[0],
            "wunschmarge": row[1],
            "reparaturkosten": json.loads(row[2])
        }
    return None