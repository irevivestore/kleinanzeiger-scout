# app.py

import streamlit as st
from scraper import scrape_ads, REPARATURKOSTEN_DEFAULT
import sqlite3
import json
import os

# 📦 Konfiguration DB Setup
def init_db():
    conn = sqlite3.connect("konfigurationen.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS konfigurationen (
            modell TEXT PRIMARY KEY,
            verkaufspreis INTEGER,
            wunsch_marge INTEGER,
            reparaturkosten TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 📂 Laden gespeicherter Konfiguration aus DB
def lade_konfiguration(modell):
    conn = sqlite3.connect("konfigurationen.db")
    c = conn.cursor()
    c.execute("SELECT verkaufspreis, wunsch_marge, reparaturkosten FROM konfigurationen WHERE modell = ?", (modell,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "verkaufspreis": row[0],
            "wunsch_marge": row[1],
            "reparaturkosten": json.loads(row[2])
        }
    return None

# 💾 Konfiguration speichern

def speichere_konfiguration(modell, verkaufspreis, wunsch_marge, reparaturkosten):
    conn = sqlite3.connect("konfigurationen.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO konfigurationen (modell, verkaufspreis, wunsch_marge, reparaturkosten)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(modell) DO UPDATE SET
            verkaufspreis = excluded.verkaufspreis,
            wunsch_marge = excluded.wunsch_marge,
            reparaturkosten = excluded.reparaturkosten
    """, (modell, verkaufspreis, wunsch_marge, json.dumps(reparaturkosten)))
    conn.commit()
    conn.close()

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")
st.markdown("Durchsuche Angebote und bewerte sie nach Reparaturbedarf")

if "anzeigen" not in st.session_state:
    st.session_state.anzeigen = []
if "reparaturkosten" not in st.session_state:
    st.session_state.reparaturkosten = REPARATURKOSTEN_DEFAULT.copy()
if "verkaufspreis" not in st.session_state:
    st.session_state.verkaufspreis = 500
if "wunsch_marge" not in st.session_state:
    st.session_state.wunsch_marge = 120

# Formular für Suche
with st.form("filters"):
    col1, col2, col3 = st.columns(3)
    modell = col1.text_input("🔍 Gerätemodell", value="iPhone 14 Pro")
    min_preis = col2.number_input("💶 Mindestpreis", min_value=0, value=0)
    max_preis = col3.number_input("💶 Maximalpreis", min_value=0, value=1000)
    nur_versand = st.checkbox("📦 Nur mit Versand")
    config_laden = st.form_submit_button("📂 Konfiguration laden")
    submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

if config_laden:
    konfig = lade_konfiguration(modell)
    if konfig:
        st.session_state.verkaufspreis = konfig["verkaufspreis"]
        st.session_state.wunsch_marge = konfig["wunsch_marge"]
        st.session_state.reparaturkosten = konfig["reparaturkosten"]
        st.success("Modell-Konfiguration geladen")
    else:
        st.info("Keine gespeicherte Konfiguration für dieses Modell gefunden")

# Einstellungsbereich
with st.expander("⚙️ Bewertungsparameter anpassen & speichern"):
    st.session_state.verkaufspreis = st.number_input("📦 Verkaufspreis (€)", min_value=0, value=st.session_state.verkaufspreis)
    st.session_state.wunsch_marge = st.number_input("🎯 Wunschmarge (€)", min_value=0, value=st.session_state.wunsch_marge)

    st.markdown("### 🔧 Reparaturkosten pro Defekt:")
    for defekt in st.session_state.reparaturkosten.keys():
        st.session_state.reparaturkosten[defekt] = st.number_input(
            defekt.capitalize(), min_value=0, max_value=1000,
            value=st.session_state.reparaturkosten[defekt], step=5, key=f"rep_{defekt}"
        )

    if st.button("💾 Konfiguration speichern"):
        speichere_konfiguration(modell, st.session_state.verkaufspreis, st.session_state.wunsch_marge, st.session_state.reparaturkosten)
        st.success("Konfiguration gespeichert")

if submit:
    with st.spinner("Suche läuft..."):
        st.session_state.anzeigen = scrape_ads(modell, min_preis, max_preis, nur_versand)

anzeigen = st.session_state.anzeigen

if not anzeigen:
    st.warning("Keine Anzeigen gefunden.")
else:
    st.success(f"{len(anzeigen)} Anzeigen gefunden")

    for idx, anzeige in enumerate(anzeigen):
        rep_kosten = anzeige.get("reparaturkosten", 0)
        max_ek = st.session_state.verkaufspreis - rep_kosten - st.session_state.wunsch_marge
        bewertung = (
            "gruen" if anzeige['price'] <= max_ek else
            "blau" if anzeige['price'] <= st.session_state.verkaufspreis - rep_kosten - (st.session_state.wunsch_marge * 0.9) else
            "rot"
        )

        farbe = {"gruen": "#d4edda", "blau": "#d1ecf1", "rot": "#f8d7da"}.get(bewertung, "#ffffff")
        with st.container():
            st.markdown(f"""
            <div style='background-color: {farbe}; padding: 10px; border-radius: 5px;'>
            <div style='display: flex; gap: 20px;'>
                <div>
                    <img src="{anzeige['image']}" width="120"/>
                </div>
                <div>
                    <h4>{anzeige['title']}</h4>
                    <b>Preis:</b> {anzeige['price']} €<br>
                    <b>Max. Einkaufspreis:</b> {max_ek:.2f} €<br>
                    <b>Versand:</b> {'✅ Ja' if anzeige['versand'] else '❌ Nein'}<br>
                    <b>Reparaturkosten:</b> {rep_kosten} €<br>
                    <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Beschreibung anzeigen"):
                st.write(anzeige["beschreibung"])

            manuelle_defekte = st.multiselect(
                label="🔧 Manuelle Defekte (optional)",
                options=list(st.session_state.reparaturkosten.keys()),
                key=f"defekt_{idx}"
            )

            if manuelle_defekte:
                neue_reparatur = sum(st.session_state.reparaturkosten[d] for d in manuelle_defekte)
                neue_max_ek = st.session_state.verkaufspreis - neue_reparatur - st.session_state.wunsch_marge
                neue_bewertung = (
                    "gruen" if anzeige['price'] <= neue_max_ek else
                    "blau" if anzeige['price'] <= st.session_state.verkaufspreis - neue_reparatur - (st.session_state.wunsch_marge * 0.9) else
                    "rot"
                )

                st.markdown(f"🧾 Neue Reparaturkosten: **{neue_reparatur} €**")
                st.markdown(f"💰 Neuer max. Einkaufspreis: **{neue_max_ek:.2f} €**")
                st.markdown(f"🎯 Neue Bewertung: **{neue_bewertung.upper()}**")

            st.divider()

st.caption("🔧 Hinweis: Die Daten stammen von öffentlich zugänglichen Anzeigen auf kleinanzeigen.de")
