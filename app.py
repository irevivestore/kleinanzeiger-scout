import streamlit as st
import sqlite3
import os
from scraper import scrape_ads
from datetime import datetime

# Datenbank initialisieren
DB_FILE = "anzeigen.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS anzeigen (
    id TEXT PRIMARY KEY,
    modell TEXT,
    title TEXT,
    price INTEGER,
    link TEXT,
    image TEXT,
    versand INTEGER,
    beschreibung TEXT,
    reparaturkosten INTEGER,
    bewertung TEXT,
    created_at TEXT,
    updated_at TEXT
)''')
conn.commit()

st.set_page_config(page_title="Kleinanzeigen Analyzer", layout="wide")

st.title("📱 Kleinanzeigen Analyzer")

# Seitenleiste – Einstellungen
with st.sidebar:
    st.header("🔧 Einstellungen")
    modell = st.text_input("Modell", "iPhone 14 Pro")
    verkaufspreis = st.number_input("Verkaufspreis (€)", 100, 2000, 600)
    wunsch_marge = st.number_input("Gewünschte Marge (€)", 10, 1000, 100)

    st.markdown("**Reparaturkosten (€)**")
    display_defekt = st.number_input("Displaybruch", 0, 500, 0)
    akku_defekt = st.number_input("Akku defekt", 0, 300, 0)
    faceid_defekt = st.number_input("FaceID defekt", 0, 300, 0)

    if st.button("🔄 Neue Anzeigen abrufen"):
        config = {
            "verkaufspreis": verkaufspreis,
            "wunsch_marge": wunsch_marge,
            "reparaturkosten": {
                "display": display_defekt,
                "akku": akku_defekt,
                "faceid": faceid_defekt
            }
        }

        neue_anzeigen = scrape_ads(
            modell=modell,
            min_price=100,
            max_price=verkaufspreis,
            nur_versand=True,
            nur_angebote=True,
            debug=False,
            config=config,
            log=lambda x: st.info(x)
        )

        inserted_count = 0
        for ad in neue_anzeigen:
            # Einfügen, falls id noch nicht existiert
            c.execute("SELECT COUNT(*) FROM anzeigen WHERE id = ?", (ad["id"],))
            if c.fetchone()[0] == 0:
                c.execute('''INSERT INTO anzeigen (
                    id, modell, title, price, link, image, versand,
                    beschreibung, reparaturkosten, bewertung,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    ad["id"], ad["modell"], ad["title"], ad["price"], ad["link"],
                    ad["image"], int(ad["versand"]), ad["beschreibung"],
                    ad["reparaturkosten"], ad["bewertung"],
                    ad["created_at"], ad["updated_at"]
                ))
                inserted_count += 1

        conn.commit()
        st.success(f"{inserted_count} neue Anzeige(n) gespeichert.")

# Anzeigen laden
c.execute("SELECT * FROM anzeigen WHERE modell = ? ORDER BY updated_at DESC", (modell,))
rows = c.fetchall()

farbe_map = {"grün": "#d4edda", "blau": "#cce5ff", "rot": "#f8d7da"}

st.subheader(f"📦 Ergebnisse für '{modell}' ({len(rows)} Einträge)")

for row in rows:
    ad_id, modell, title, price, link, image, versand, beschreibung, repkosten, bewertung, created, updated = row
    farbe = farbe_map.get(bewertung, "#ffffff")

    with st.container():
        st.markdown(
            f"""
            <div style="background-color:{farbe};padding:10px;border-radius:10px;margin-bottom:10px;">
                <h4 style="margin-bottom:5px;">{title}</h4>
                <p><strong>Preis:</strong> {price} €<br>
                <strong>Reparaturkosten:</strong> {repkosten} €<br>
                <strong>Bewertung:</strong> {bewertung}<br>
                <strong>Erfasst:</strong> {created}</p>
                <a href="{link}" target="_blank">🔗 Zur Anzeige</a>
                <details style="margin-top:10px;">
                    <summary>📄 Beschreibung anzeigen</summary>
                    <p>{beschreibung}</p>
                </details>
            </div>
            """,
            unsafe_allow_html=True
        )
