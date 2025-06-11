# app.py

import streamlit as st
import json
import os
from datetime import datetime
from scraper import scrape_ads, lade_anzeigen

# === Hilfsfunktionen ===
def log(msg):
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    st.session_state.debug_log += f"[{timestamp}] {msg}\n"

def save_config():
    config = {
        "verkaufspreis": st.session_state.verkaufspreis,
        "wunsch_marge": st.session_state.wunsch_marge,
        "reparaturkosten": {
            "display": st.session_state.reparatur_display,
            "backcover": st.session_state.reparatur_backcover,
            "akku": st.session_state.reparatur_akku,
            "kamera": st.session_state.reparatur_kamera,
        }
    }
    with open("config.json", "w") as f:
        json.dump(config, f)
    log("Konfiguration gespeichert.")

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)
            st.session_state.verkaufspreis = config.get("verkaufspreis", 500)
            st.session_state.wunsch_marge = config.get("wunsch_marge", 100)
            st.session_state.reparatur_display = config.get("reparaturkosten", {}).get("display", 100)
            st.session_state.reparatur_backcover = config.get("reparaturkosten", {}).get("backcover", 60)
            st.session_state.reparatur_akku = config.get("reparaturkosten", {}).get("akku", 40)
            st.session_state.reparatur_kamera = config.get("reparaturkosten", {}).get("kamera", 80)
            log("Konfiguration geladen.")
    else:
        log("Keine gespeicherte Konfiguration gefunden.")

def berechne_max_preis(verkaufspreis, wunsch_marge, defekte, reparaturkosten):
    kosten = sum(reparaturkosten[d] for d in defekte)
    return verkaufspreis - wunsch_marge - kosten

def parse_defekte_dropdown(text):
    return [d for d in text if d != "Keiner"]

# === Initialisierung ===
st.set_page_config("Kleinanzeigen Analyzer", layout="wide")
if "debug_log" not in st.session_state:
    st.session_state.debug_log = ""

# === Sidebar Konfiguration ===
st.sidebar.header("⚙️ Bewertungs-Konfiguration")
load_config()

with st.sidebar.form("config_form"):
    st.number_input("💰 Geplanter Verkaufspreis (€)", min_value=0, step=10, key="verkaufspreis")
    st.number_input("📈 Wunschmarge (€)", min_value=0, step=10, key="wunsch_marge")
    st.number_input("💥 Displayreparatur (€)", min_value=0, step=10, key="reparatur_display")
    st.number_input("🔋 Akkutausch (€)", min_value=0, step=10, key="reparatur_akku")
    st.number_input("📷 Kameratausch (€)", min_value=0, step=10, key="reparatur_kamera")
    st.number_input("📦 Backcover (€)", min_value=0, step=10, key="reparatur_backcover")
    speichern = st.form_submit_button("💾 Konfiguration speichern", on_click=save_config)

# === Formular: Filterparameter ===
st.header("📋 Anzeige-Filter und Scraping")
with st.form("filter_form"):
    modell = st.selectbox("📱 iPhone Modell", ["iPhone 14 Pro", "iPhone 13", "iPhone 12", "iPhone 11"])
    min_price = st.number_input("💶 Mindestpreis", value=100, step=10)
    max_price = st.number_input("💶 Maximalpreis", value=350, step=10)
    nur_angebote = st.checkbox("Nur Angebote (keine Gesuche)", value=True)
    nur_versand = st.checkbox("Nur mit Versandoption", value=True)
    debug = st.checkbox("🔧 Debug-Modus aktivieren", value=False)
    scrape_button = st.form_submit_button("🔍 Jetzt Anzeigen suchen")

# === Scrape starten ===
if scrape_button:
    log("Starte Scraping ...")
    scrape_ads(modell, min_price, max_price, nur_angebote, nur_versand, debug)
    log("Scraping abgeschlossen.")

# === Anzeigen laden und anzeigen ===
st.header("📦 Ergebnisse")
anzeigen = lade_anzeigen()
reparaturkosten = {
    "display": st.session_state.reparatur_display,
    "akku": st.session_state.reparatur_akku,
    "kamera": st.session_state.reparatur_kamera,
    "backcover": st.session_state.reparatur_backcover,
}

defekte_optionen = ["Keiner", "display", "akku", "kamera", "backcover"]

for i, anzeige in enumerate(anzeigen):
    with st.expander(f"{anzeige['title']} – {anzeige['price']} €", expanded=False):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Link:** [{anzeige['url']}]({anzeige['url']})")
            st.markdown(f"**Beschreibung:** {anzeige['description']}")
            st.markdown(f"**Preis:** {anzeige['price']} €")
            st.markdown(f"**Stand:** {anzeige['timestamp_erfasst']} – {anzeige['timestamp_geändert']}")
        with col2:
            def_key = f"defekte_{i}"
            if def_key not in st.session_state:
                st.session_state[def_key] = ["Keiner"]
            selected_defekte = st.multiselect(
                "🛠 Manuelle Defekte wählen", defekte_optionen, default=st.session_state[def_key], key=def_key
            )
            st.session_state[def_key] = selected_defekte

            defekte = parse_defekte_dropdown(selected_defekte)
            max_preis = berechne_max_preis(
                st.session_state.verkaufspreis,
                st.session_state.wunsch_marge,
                defekte,
                reparaturkosten
            )
            st.metric("📉 Max. Einkaufspreis", f"{max_preis:.2f} €")

# === Debug-Log ===
if debug:
    st.header("📝 Debug Log")
    st.text_area("Protokoll", value=st.session_state.debug_log, height=300)
