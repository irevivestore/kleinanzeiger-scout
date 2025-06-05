# config.py

import sqlite3  # <- wichtig für save_config / load_config

# Standard-Werte, wenn keine Konfiguration für das Modell gespeichert ist
REPARATURKOSTEN_DEFAULT = {
    "display": 80,
    "akku": 30,
    "backcover": 60,
    "kamera": 100,
    "lautsprecher": 60,
    "mikrofon": 50,
    "face id": 80,
    "wasserschaden": 250,
    "kein bild": 80,
    "defekt": 0  # allgemeiner Hinweis
}

VERKAUFSPREIS_DEFAULT = 500  # Standard-Wert für Verkaufspreis
WUNSCH_MARGE_DEFAULT = 120   # Standard-Wert für Marge in €

DB_PATH = "config.db"

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
