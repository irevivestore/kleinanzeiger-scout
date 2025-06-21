import sqlite3
import json
import datetime
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adverts (
        id TEXT PRIMARY KEY,
        modell TEXT,
        title TEXT,
        beschreibung TEXT,
        price INTEGER,
        link TEXT,
        image TEXT,
        bilder_liste TEXT,
        man_defekt_keys TEXT,
        archived INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # Migration für bestehende Tabellen
    try:
        cursor.execute("ALTER TABLE adverts ADD COLUMN created_at TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE adverts ADD COLUMN updated_at TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config (
        modell TEXT PRIMARY KEY,
        verkaufspreis INTEGER,
        wunsch_marge INTEGER,
        reparaturkosten TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_advert(advert):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.datetime.now().strftime("%Y-%m-%d")

    cursor.execute("SELECT id, created_at FROM adverts WHERE id = ?", (advert["id"],))
    row = cursor.fetchone()

    if row:
        created_at_existing = row[1] or now
        cursor.execute("""
            UPDATE adverts SET
                modell = ?,
                title = ?,
                beschreibung = ?,
                price = ?,
                link = ?,
                image = ?,
                bilder_liste = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            advert.get("modell"),
            advert.get("title"),
            advert.get("beschreibung"),
            advert.get("price"),
            advert.get("link"),
            advert.get("image"),
            json.dumps(advert.get("bilder_liste", [])),
            now,
            advert["id"]
        ))
    else:
        cursor.execute("""
            INSERT INTO adverts (
                id, modell, title, beschreibung, price, link, image,
                bilder_liste, man_defekt_keys, archived, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (
            advert["id"],
            advert.get("modell"),
            advert.get("title"),
            advert.get("beschreibung"),
            advert.get("price"),
            advert.get("link"),
            advert.get("image"),
            json.dumps(advert.get("bilder_liste", [])),
            json.dumps(advert.get("man_defekt_keys", [])),
            now,
            now
        ))

    conn.commit()
    conn.close()

def get_all_adverts_for_model(modell, include_archived=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM adverts WHERE modell = ?"
    params = [modell]
    if not include_archived:
        query += " AND archived = 0"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        row_dict = dict(row)

        bilder_raw = row_dict.get("bilder_liste") or "[]"
        row_dict["bilder_liste"] = json.loads(bilder_raw)

        man_defekt_raw = row_dict.get("man_defekt_keys") or "[]"
        row_dict["man_defekt_keys"] = json.loads(man_defekt_raw)

        result.append(row_dict)
    return result

def get_all_ad_ids_for_model(modell, include_archived=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT id FROM adverts WHERE modell = ?"
    params = [modell]
    if not include_archived:
        query += " AND archived = 0"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]

def get_archived_adverts_for_model(modell):
    return get_all_adverts_for_model(modell, include_archived=True)

def is_advert_archived(ad_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT archived FROM adverts WHERE id = ?", (ad_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0] == 1
    return False

def archive_advert(ad_id, archive=True):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE adverts SET archived = ? WHERE id = ?", (1 if archive else 0, ad_id))
    conn.commit()
    conn.close()

def load_config(modell):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT verkaufspreis, wunsch_marge, reparaturkosten FROM config WHERE modell = ?", (modell,))
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            reparaturkosten = json.loads(row[2]) if row[2] else {}
        except Exception:
            reparaturkosten = {}
        return {
            "verkaufspreis": row[0],
            "wunsch_marge": row[1],
            "reparaturkosten": reparaturkosten
        }
    return None

def save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO config (modell, verkaufspreis, wunsch_marge, reparaturkosten)
        VALUES (?, ?, ?, ?)
    """, (modell, verkaufspreis, wunsch_marge, json.dumps(reparaturkosten)))
    conn.commit()
    conn.close()

def update_manual_defekt_keys(ad_id, man_defekt_keys):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE adverts SET man_defekt_keys = ? WHERE id = ?",
        (json.dumps(man_defekt_keys), ad_id)
    )
    conn.commit()
    conn.close()