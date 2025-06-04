# db.py

import sqlite3
from datetime import datetime
import os

DB_PATH = "data.sqlite"

# 🧱 Datenbank initialisieren
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS anzeigen (
            ad_id TEXT PRIMARY KEY,
            title TEXT,
            price REAL,
            image TEXT,
            link TEXT,
            beschreibung TEXT,
            versand INTEGER,
            modell TEXT,
            erfasst_am TEXT,
            zuletzt_aktualisiert TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS konfigurationen (
            modell TEXT PRIMARY KEY,
            verkaufspreis REAL,
            wunsch_marge REAL,
            reparaturkosten TEXT
        )
    """)
    conn.commit()
    conn.close()

# 💾 Anzeige speichern oder aktualisieren
def save_advert(ad, modell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    existing = get_existing_advert(ad["ad_id"])

    now = datetime.utcnow().isoformat()

    if existing:
        c.execute("""
            UPDATE anzeigen SET
                title = ?,
                price = ?,
                image = ?,
                link = ?,
                beschreibung = ?,
                versand = ?,
                modell = ?,
                zuletzt_aktualisiert = ?
            WHERE ad_id = ?
        """, (
            ad["title"], ad["price"], ad["image"], ad["link"], ad["beschreibung"],
            int(ad["versand"]), modell, now, ad["ad_id"]
        ))
    else:
        c.execute("""
            INSERT INTO anzeigen (
                ad_id, title, price, image, link, beschreibung, versand, modell, erfasst_am, zuletzt_aktualisiert
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ad["ad_id"], ad["title"], ad["price"], ad["image"], ad["link"], ad["beschreibung"],
            int(ad["versand"]), modell, now, now
        ))

    conn.commit()
    conn.close()

# 🔍 Anzeige anhand ID abrufen
def get_existing_advert(ad_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM anzeigen WHERE ad_id = ?", (ad_id,))
    result = c.fetchone()
    conn.close()
    return result

# 📦 Konfiguration speichern
def save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict):
    import json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO konfigurationen (modell, verkaufspreis, wunsch_marge, reparaturkosten)
        VALUES (?, ?, ?, ?)
    """, (modell, verkaufspreis, wunsch_marge, json.dumps(reparaturkosten_dict)))
    conn.commit()
    conn.close()

# 🧾 Konfiguration laden
def load_config(modell):
    import json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT verkaufspreis, wunsch_marge, reparaturkosten FROM konfigurationen WHERE modell = ?", (modell,))
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