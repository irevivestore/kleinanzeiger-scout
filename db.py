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
        "archived": "INTEGER DEFAULT 0",
        "bilder_liste": "TEXT"
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

    c.execute("SELECT man_defekt_keys FROM anzeigen WHERE id = ?", (ad["id"],))
    result = c.fetchone()

    bilder_liste_json = json.dumps(ad.get("bilder_liste", []))

    if result:
        c.execute('''
            UPDATE anzeigen
            SET price = ?, title = ?, link = ?, image = ?, versand = ?, beschreibung = ?, bilder_liste = ?, updated_at = ?
            WHERE id = ?
        ''', (
            ad["price"],
            ad["title"],
            ad["link"],
            ad["image"],
            int(ad["versand"]),
            ad["beschreibung"],
            bilder_liste_json,
            now,
            ad["id"]
        ))
    else:
        c.execute('''
            INSERT INTO anzeigen (
                id, modell, title, price, link, image, versand, beschreibung, man_defekt_keys, created_at, updated_at, archived, bilder_liste
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ad["id"],
            ad["modell"],
            ad["title"],
            ad["price"],
            ad["link"],
            ad["image"],
            int(ad["versand"]),
            ad["beschreibung"],
            json.dumps([]),
            now,
            now,
            0,
            bilder_liste_json
        ))

    conn.commit()
    conn.close()

def get_all_adverts_for_model(modell, include_archived=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if include_archived:
        cursor.execute("SELECT * FROM anzeigen WHERE modell = ?", (modell,))
    else:
        cursor.execute("SELECT * FROM anzeigen WHERE modell = ? AND archived = 0", (modell,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        row_dict = dict(row)
        # bilder_liste aus JSON wiederherstellen
        row_dict["bilder_liste"] = json.loads(row_dict.get("bilder_liste", "[]"))
        result.append(row_dict)

    print(f"[DEBUG] Lade {len(result)} Anzeigen aus DB für Modell {modell} (include_archived={include_archived})")
    return result

def get_all_ad_ids_for_model(modell, include_archived=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if include_archived:
        cursor.execute("SELECT id FROM anzeigen WHERE modell = ?", (modell,))
    else:
        cursor.execute("SELECT id FROM anzeigen WHERE modell = ? AND archived = 0", (modell,))
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids

def get_archived_adverts_for_model(modell):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM anzeigen WHERE modell = ? AND archived = 1", (modell,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        row_dict = dict(row)
        row_dict["bilder_liste"] = json.loads(row_dict.get("bilder_liste", "[]"))
        result.append(row_dict)

    return result

def get_all_active_adverts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM anzeigen WHERE archived = 0")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        row_dict = dict(row)
        row_dict["bilder_liste"] = json.loads(row_dict.get("bilder_liste", "[]"))
        result.append(row_dict)

    return result

def save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

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

def update_manual_defekt_keys(ad_id, json_str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE anzeigen SET man_defekt_keys = ? WHERE id = ?", (json_str, ad_id))
    conn.commit()
    conn.close()

def archive_advert(ad_id, archived: bool):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE anzeigen SET archived = ? WHERE id = ?", (1 if archived else 0, ad_id))
    print(f"[DB] Anzeige {ad_id} archiviert: {archived}")
    conn.commit()
    conn.close()

def is_advert_archived(ad_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT archived FROM anzeigen WHERE id = ?", (ad_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0] == 1
    return False
