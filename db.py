import sqlite3
import datetime
import json

DB_PATH = "/data/config.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tabelle erstellen, falls sie nicht existiert
    c.execute('''
        CREATE TABLE IF NOT EXISTS anzeigen (
            id TEXT PRIMARY KEY,
            modell TEXT,
            title TEXT,
            price INTEGER,
            link TEXT,
            image TEXT,
            versand INTEGER
        )
    ''')

    # Neue Spalten prüfen und ggf. ergänzen
    neue_spalten = {
        "beschreibung": "TEXT",
        "man_defekt_keys": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT",
        "archived": "INTEGER DEFAULT 0"  # Neu: Archiv-Status (0 = aktiv, 1 = archiviert)
    }

    c.execute("PRAGMA table_info(anzeigen)")
    bestehende_spalten = [row[1] for row in c.fetchall()]

    for spalte, typ in neue_spalten.items():
        if spalte not in bestehende_spalten:
            c.execute(f"ALTER TABLE anzeigen ADD COLUMN {spalte} {typ}")

    # Konfigurationstabelle erstellen
    c.execute('''
        CREATE TABLE IF NOT EXISTS konfigurationen (
            modell TEXT PRIMARY KEY,
            verkaufspreis INTEGER,
            wunsch_marge INTEGER,
            reparaturkosten TEXT
        )
    ''')

    conn.commit()
    conn.close()

def save_advert(ad):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = datetime.datetime.now().isoformat()

    # Prüfen, ob Anzeige bereits vorhanden (egal ob archiviert oder nicht)
    c.execute("SELECT man_defekt_keys FROM anzeigen WHERE id = ?", (ad["id"],))
    result = c.fetch
