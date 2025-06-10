import sqlite3
import datetime

DB_PATH = "config.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Anzeigen-Tabelle (ohne Spalte bewertung zuerst erstellen)
    c.execute('''
        CREATE TABLE IF NOT EXISTS anzeigen (
            id TEXT PRIMARY KEY,
            modell TEXT,
            title TEXT,
            price INTEGER,
            link TEXT,
            image TEXT,
            versand INTEGER,
            beschreibung TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # Prüfen, ob Spalte "bewertung" existiert, wenn nicht, hinzufügen
    c.execute("PRAGMA table_info(anzeigen)")
    columns = [row[1] for row in c.fetchall()]
    if "bewertung" not in columns:
        c.execute("ALTER TABLE anzeigen ADD COLUMN bewertung TEXT")

    # Konfigurationstabelle
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
    bewertung = ad.get("bewertung", None)

    # Prüfen, ob Anzeige bereits vorhanden
    c.execute("SELECT updated_at FROM anzeigen WHERE id = ?", (ad["id"],))
    result = c.fetchone()

    if result:
        # Aktualisieren
        c.execute('''
            UPDATE anzeigen
            SET price = ?, updated_at = ?, bewertung = ?
            WHERE id = ?
        ''', (ad["price"], now, bewertung, ad["id"]))
    else:
        # Neu einfügen
        c.execute('''
            INSERT INTO anzeigen (id, modell, title, price, link, image, versand, beschreibung, created_at, updated_at, bewertung)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ad["id"],
            ad["modell"],
            ad["title"],
            ad["price"],
            ad["link"],
            ad["image"],
            int(ad["versand"]),
            ad["beschreibung"],
            now,
            now,
            bewertung
        ))

    conn.commit()
    conn.close()

def get_all_adverts_for_model(modell):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM anzeigen WHERE modell = ?", (modell,))
    rows = cursor.fetchall()
    print(f"[DEBUG] Lade {len(rows)} Anzeigen aus DB für Modell {modell}")
    conn.close()
    return [dict(row) for row in rows]

def save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Dictionary als String speichern
    rep_string = repr(reparaturkosten_dict)

    c.execute('''
        INSERT OR REPLACE INTO konfigurationen (modell, verkaufspreis, wunsch_marge, reparaturkosten)
        VALUES (?, ?, ?, ?)
    ''', (modell, verkaufspreis, wunsch_marge, rep_string))

    conn.commit()
    conn.close()

def load_config(modell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT verkaufspreis, wunsch_marge, reparaturkosten FROM konfigurationen WHERE modell = ?", (modell,))
    row = c.fetchone()
    conn.close()

    if row:
        verkaufspreis, wunsch_marge, rep_string = row
        try:
            reparaturkosten = eval(rep_string)
        except:
            reparaturkosten = {}
        return {
            "verkaufspreis": verkaufspreis,
            "wunsch_marge": wunsch_marge,
            "reparaturkosten": reparaturkosten
        }
    else:
        return None