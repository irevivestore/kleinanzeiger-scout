import sqlite3
import datetime
import json

DB_PATH = "/data/config.db"

def initDb():
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
    neueSpalten = {
        "beschreibung": "TEXT",
        "man_defekt_keys": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT",
        "archived": "INTEGER DEFAULT 0"
    }

    c.execute("PRAGMA table_info(anzeigen)")
    bestehendeSpalten = [row[1] for row in c.fetchall()]

    for spalte, typ in neueSpalten.items():
        if spalte not in bestehendeSpalten:
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

def saveAdvert(advert):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = datetime.datetime.now().isoformat()

    c.execute("SELECT man_defekt_keys FROM anzeigen WHERE id = ?", (advert["id"],))
    result = c.fetchone()

    if result:
        c.execute('''
            UPDATE anzeigen
            SET price = ?, title = ?, link = ?, image = ?, versand = ?, beschreibung = ?, updated_at = ?
            WHERE id = ?
        ''', (
            advert["price"],
            advert["title"],
            advert["link"],
            advert["image"],
            int(advert["versand"]),
            advert["beschreibung"],
            now,
            advert["id"]
        ))
    else:
        c.execute('''
            INSERT INTO anzeigen (
                id, modell, title, price, link, image, versand, beschreibung, man_defekt_keys, created_at, updated_at, archived
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            advert["id"],
            advert["modell"],
            advert["title"],
            advert["price"],
            advert["link"],
            advert["image"],
            int(advert["versand"]),
            advert["beschreibung"],
            json.dumps([]),
            now,
            now,
            0
        ))

    conn.commit()
    conn.close()

def getAllAdvertsForModel(model, includeArchived=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if includeArchived:
        cursor.execute("SELECT * FROM anzeigen WHERE modell = ?", (model,))
    else:
        cursor.execute("SELECT * FROM anzeigen WHERE modell = ? AND archived = 0", (model,))
    rows = cursor.fetchall()
    print(f"[DEBUG] Lade {len(rows)} Anzeigen aus DB für Modell {model} (includeArchived={includeArchived})")
    conn.close()

    # Keys nach camelCase umwandeln
    return [convertRowToCamelCase(dict(row)) for row in rows]

def getAllAdIdsForModel(model, includeArchived=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if includeArchived:
        cursor.execute("SELECT id FROM anzeigen WHERE modell = ?", (model,))
    else:
        cursor.execute("SELECT id FROM anzeigen WHERE modell = ? AND archived = 0", (model,))
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids

def getArchivedAdvertsForModel(model):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM anzeigen WHERE modell = ? AND archived = 1", (model,))
    rows = cursor.fetchall()
    conn.close()
    return [convertRowToCamelCase(dict(row)) for row in rows]

def getAllActiveAdverts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM anzeigen WHERE archived = 0")
    rows = cursor.fetchall()
    conn.close()
    return [convertRowToCamelCase(dict(row)) for row in rows]

def saveConfig(model, salePrice, targetMargin, repairCostsDict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    repString = repr(repairCostsDict)

    c.execute('''
        INSERT OR REPLACE INTO konfigurationen (modell, verkaufspreis, wunsch_marge, reparaturkosten)
        VALUES (?, ?, ?, ?)
    ''', (model, salePrice, targetMargin, repString))

    conn.commit()
    conn.close()

def loadConfig(model):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT verkaufspreis, wunsch_marge, reparaturkosten FROM konfigurationen WHERE modell = ?", (model,))
    row = c.fetchone()
    conn.close()

    if row:
        salePrice, targetMargin, repString = row
        try:
            repairCosts = eval(repString)
        except:
            repairCosts = {}
        return {
            "salePrice": salePrice,
            "targetMargin": targetMargin,
            "repairCosts": repairCosts
        }
    else:
        return None

def updateManualDefectKeys(adId, jsonStr):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE anzeigen SET man_defekt_keys = ? WHERE id = ?", (jsonStr, adId))
    conn.commit()
    conn.close()

def archiveAdvert(adId, archived: bool):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE anzeigen SET archived = ? WHERE id = ?", (1 if archived else 0, adId))
    print(f"[DB] Anzeige {adId} archiviert: {archived}")
    conn.commit()
    conn.close()

def isAdvertArchived(adId):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT archived FROM anzeigen WHERE id = ?", (adId,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0] == 1
    return False

# Hilfsfunktion: wandelt SQL-Row-Keys in camelCase um
def convertRowToCamelCase(row):
    mapping = {
        "id": "id",
        "modell": "model",
        "title": "title",
        "price": "price",
        "link": "link",
        "image": "image",
        "versand": "versand",
        "beschreibung": "description",
        "man_defekt_keys": "manualDefectKeys",
        "created_at": "createdAt",
        "updated_at": "updatedAt",
        "archived": "archived"
    }
    return {mapping.get(k, k): v for k, v in row.items()}
