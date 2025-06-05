import sqlite3
import datetime

DB_PATH = "config.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Anzeigen-Tabelle
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
    print("Datenbank initialisiert.")

def save_advert(ad):
    print(f"[DEBUG] Speichere Anzeige: {ad['title']} mit Preis {ad['price']} und ID {ad['id']}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = datetime.datetime.now().isoformat()

    # Prüfen, ob Anzeige bereits vorhanden
    c.execute("SELECT updated_at FROM anzeigen WHERE id = ?", (ad["id"],))
    result = c.fetchone()

    if result:
        # Aktualisieren
        c.execute('''
            UPDATE anzeigen
            SET price = ?, updated_at = ?
            WHERE id = ?
        ''', (ad["price"], now, ad["id"]))
        print(f"[DEBUG] Anzeige ID {ad['id']} aktualisiert.")
    else:
        # Neu einfügen
        c.execute('''
            INSERT INTO anzeigen (id, modell, title, price, link, image, versand, beschreibung, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            now
        ))
        print(f"[DEBUG] Neue Anzeige ID {ad['id']} eingefügt.")

    conn.commit()
    conn.close()

def get_all_adverts_for_model(modell):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM anzeigen WHERE modell = ?", (modell,))
    results = c.fetchall()

    columns = [desc[0] for desc in c.description]
    conn.close()

    ads = [dict(zip(columns, row)) for row in results]
    print(f"[DEBUG] Lade {len(ads)} Anzeigen für Modell '{modell}' aus der DB.")
    return ads

def save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict):
    print(f"[DEBUG] Speichere Konfiguration für Modell {modell}.")
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
        print(f"[DEBUG] Konfiguration für {modell} geladen.")
        return {
            "verkaufspreis": verkaufspreis,
            "wunsch_marge": wunsch_marge,
            "reparaturkosten": reparaturkosten
        }
    else:
        print(f"[DEBUG] Keine Konfiguration für {modell} gefunden.")
        return None
