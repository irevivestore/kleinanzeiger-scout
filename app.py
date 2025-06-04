# app.py

import streamlit as st
import json
import os
from scraper import scrape_ads, REPARATURKOSTEN, VERKAUFSPREIS, WUNSCH_MARGE

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")
st.markdown("Durchsuche Angebote und bewerte sie nach Reparaturbedarf")

CONFIG_DIR = "configs"
os.makedirs(CONFIG_DIR, exist_ok=True)

if "anzeigen" not in st.session_state:
    st.session_state.anzeigen = []

if "konfig" not in st.session_state:
    st.session_state.konfig = REPARATURKOSTEN.copy()

# Konfiguration laden
st.markdown("### ⚙️ Modell-Konfigurationen")
with st.expander("🔧 Konfiguration anpassen oder laden"):
    konfig_files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
    col1, col2 = st.columns([3, 1])
    selected_file = col1.selectbox("Modell-Konfiguration laden", ["- Keine -"] + konfig_files)
    if col2.button("📂 Laden") and selected_file != "- Keine -":
        with open(os.path.join(CONFIG_DIR, selected_file), "r") as f:
            st.session_state.konfig = json.load(f)

    st.markdown("#### Reparaturkosten anpassen:")
    for defekt, kosten in st.session_state.konfig.items():
        st.session_state.konfig[defekt] = st.number_input(
            f"{defekt.capitalize()}", min_value=0, max_value=1000, step=5, value=kosten, key=f"kosten_{defekt}"
        )

    col3, col4 = st.columns([3, 1])
    save_as = col3.text_input("Speichern als (Modellname)", value="iPhone 14 Pro")
    if col4.button("💾 Speichern"):
        with open(os.path.join(CONFIG_DIR, f"{save_as}.json"), "w") as f:
            json.dump(st.session_state.konfig, f)
        st.success(f"Konfiguration gespeichert unter: {save_as}.json")

# Formular für die Suche
with st.form("filters"):
    col1, col2, col3 = st.columns(3)
    modell = col1.text_input("🔍 Gerätemodell", value="iPhone 14 Pro")
    min_preis = col2.number_input("💶 Mindestpreis", min_value=0, value=0)
    max_preis = col3.number_input("💶 Maximalpreis", min_value=0, value=1000)
    nur_versand = st.checkbox("📦 Nur mit Versand")
    submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

if submit:
    with st.spinner("Suche läuft..."):
        st.session_state.anzeigen = scrape_ads(modell, min_preis, max_preis, nur_versand)

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
                    <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Beschreibung anzeigen"):
                st.write(anzeige["beschreibung"])

            st.markdown("**Defekte manuell auswählen (optional):**")
            manuelle_defekte = st.multiselect(
                label="Defekte", options=list(st.session_state.konfig.keys()),
                key=f"defekt_{idx}"
            )

            if manuelle_defekte:
                neue_reparatur = sum(st.session_state.konfig[d] for d in manuelle_defekte)
                neue_max_ek = VERKAUFSPREIS - neue_reparatur - WUNSCH_MARGE
                neue_bewertung = (
                    "gruen" if anzeige['price'] <= neue_max_ek else
                    "blau" if anzeige['price'] <= VERKAUFSPREIS - neue_reparatur - (WUNSCH_MARGE * 0.9) else
                    "rot"
                )

                st.markdown(f"🧾 Neue Reparaturkosten: **{neue_reparatur} €**")
                st.markdown(f"💰 Neuer max. Einkaufspreis: **{neue_max_ek:.2f} €**")
                st.markdown(f"🎯 Neue Bewertung: **{neue_bewertung.upper()}**")

            st.divider()

st.caption("🔧 Hinweis: Die Daten stammen von öffentlich zugänglichen Anzeigen auf kleinanzeigen.de")