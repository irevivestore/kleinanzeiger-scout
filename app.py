# app.py

import streamlit as st
from scraper import scrape_ads
from db import (
    init_db, save_advert, get_existing_advert,
    load_config, save_config
)

# Standardwerte
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
    "defekt": 0
}

VERKAUFSPREIS_DEFAULT = 500
WUNSCH_MARGE_DEFAULT = 120

# Initialisierung
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")
st.markdown("Durchsuche Angebote und bewerte sie nach Reparaturbedarf")
init_db()

if "anzeigen" not in st.session_state:
    st.session_state.anzeigen = []
if "config" not in st.session_state:
    st.session_state.config = {}

# Formular für die Suche
with st.form("filters"):
    col1, col2, col3 = st.columns(3)
    modell = col1.text_input("🔍 Gerätemodell", value="iPhone 14 Pro")
    min_preis = col2.number_input("💶 Mindestpreis", min_value=0, value=0)
    max_preis = col3.number_input("💶 Maximalpreis", min_value=0, value=1000)
    nur_versand = st.checkbox("📦 Nur mit Versand")
    konfig_anzeigen = st.checkbox("⚙️ Erweiterte Bewertungsparameter anzeigen")
    submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

# Lade Konfiguration
config = load_config(modell)
if config is None:
    config = {
        "verkaufspreis": VERKAUFSPREIS_DEFAULT,
        "wunsch_marge": WUNSCH_MARGE_DEFAULT,
        "reparaturkosten": REPARATURKOSTEN_DEFAULT.copy()
    }
    save_config(modell, config["verkaufspreis"], config["wunsch_marge"], config["reparaturkosten"])

st.session_state.config = config

# Konfiguration anzeigen
if konfig_anzeigen:
    with st.expander("🛠 Bewertungsparameter anpassen", expanded=True):
        st.session_state.config["verkaufspreis"] = st.number_input("💵 Verkaufspreis", min_value=0, value=config["verkaufspreis"])
        st.session_state.config["wunsch_marge"] = st.number_input("🎯 Wunschmarge", min_value=0, value=config["wunsch_marge"])

        st.markdown("**🧾 Reparaturkosten je Defekt**")
        for i, (defekt, kosten) in enumerate(config["reparaturkosten"].items()):
            neue_kosten = st.number_input(f"🔧 {defekt.capitalize()}", min_value=0, value=kosten, key=f"cost_{i}")
            st.session_state.config["reparaturkosten"][defekt] = neue_kosten

        save_config(modell, st.session_state.config["verkaufspreis"], st.session_state.config["wunsch_marge"], st.session_state.config["reparaturkosten"])

if submit:
    with st.spinner("Suche läuft..."):
        st.session_state.anzeigen = scrape_ads(
            modell, min_preis, max_preis, nur_versand,
            config["verkaufspreis"], config["wunsch_marge"], config["reparaturkosten"]
        )

anzeigen = st.session_state.anzeigen

if not anzeigen:
    st.warning("Keine Anzeigen gefunden.")
else:
    st.success(f"{len(anzeigen)} Anzeigen gefunden")

    for idx, anzeige in enumerate(anzeigen):
        farbe = {"gruen": "#d4edda", "blau": "#d1ecf1", "rot": "#f8d7da"}.get(anzeige["bewertung"], "#ffffff")
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
                    <b>Max. Einkaufspreis:</b> {anzeige['max_ek']:.2f} €<br>
                    <b>Versand:</b> {'✅ Ja' if anzeige['versand'] else '❌ Nein'}<br>
                    <b>Reparaturkosten:</b> {anzeige['reparaturkosten']} €<br>
                    <b>Erfasst:</b> {anzeige.get('erstellt_am', '?')}<br>
                    <b>Zuletzt geprüft:</b> {anzeige.get('aktualisiert_am', '?')}<br>
                    <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Beschreibung anzeigen"):
                st.write(anzeige["beschreibung"])

            st.markdown("**Defekte manuell auswählen (optional):**")
            manuelle_defekte = st.multiselect(
                label="Defekte", options=list(config["reparaturkosten"].keys()),
                key=f"defekt_{idx}"
            )

            if manuelle_defekte:
                neue_reparatur = sum(config["reparaturkosten"][d] for d in manuelle_defekte)
                neue_max_ek = config["verkaufspreis"] - neue_reparatur - config["wunsch_marge"]
                neue_bewertung = (
                    "gruen" if anzeige['price'] <= neue_max_ek else
                    "blau" if anzeige['price'] <= config["verkaufspreis"] - neue_reparatur - (config["wunsch_marge"] * 0.9) else
                    "rot"
                )

                st.markdown(f"🧾 Neue Reparaturkosten: **{neue_reparatur} €**")
                st.markdown(f"💰 Neuer max. Einkaufspreis: **{neue_max_ek:.2f} €**")
                st.markdown(f"🎯 Neue Bewertung: **{neue_bewertung.upper()}**")

            st.divider()

st.caption("🔧 Hinweis: Die Daten stammen von öffentlich zugänglichen Anzeigen auf kleinanzeigen.de")