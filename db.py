import sqlite3
import json
from datetime import datetime

DB_PATH = "data.sqlite3"  # Passe den Pfad ggf. an

def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def get_all_active_adverts():
    conn = connect()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM anzeigen WHERE archived = 0 ORDER BY updated_at DESC")
    result = cur.fetchall()
    conn.close()
    return result

def get_archived_adverts_for_model(modell):
    conn = connect()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM anzeigen WHERE archived = 1 AND modell = ? ORDER BY updated_at DESC", (modell,))
    result = cur.fetchall()
    conn.close()
    return result

def load_config(modell):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT config_json FROM konfigurationen WHERE modell = ?", (modell,))
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def update_manual_defekt_keys(ad_id, defekt_keys_json):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE anzeigen SET man_defekt_keys = ?, updated_at = ? WHERE id = ?",
        (defekt_keys_json, datetime.now().isoformat(timespec='seconds'), ad_id)
    )
    conn.commit()
    conn.close()

def archive_advert(ad_id, archived: bool):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE anzeigen SET archived = ?, updated_at = ? WHERE id = ?",
        (int(archived), datetime.now().isoformat(timespec='seconds'), ad_id)
    )
    conn.commit()
    conn.close()
