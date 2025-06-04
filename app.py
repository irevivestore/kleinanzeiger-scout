# app.py

import streamlit as st
from scraper import scrape_ads
from db import init_db, save_advert, get_existing_advert, load_config, save_config
from config import REPARATURKOSTEN, VERKAUFSPREIS, WUNSCH_MARGE
import os

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")
st.markdown("Durchsuche Angebote und bewerte sie nach Reparaturbedarf")

# Datenbank initialisieren
init_db()

# Konfigurationswerte laden oder Standard setzen
if "config" not in st.session_state:
    st.session_state.config = load_config()

# Konfiguration bearbeiten
with st.expander("⚙️ Bewertungsparameter einstellen"):
    col1, col2 = st.columns(2)
    st.session_state.config["verkaufspreis"] = col1.number_input("💵 Verkaufspreis", value=st.session_state.config.get("verkaufspreis", VERKAUFSPREIS))
    st.session_state.config["wunsch_marge"] = col2.number_input("🎯 Wunschmarge", value=st.session_state.config.get("wunsch_marge", WUNSCH_MARGE))

    for defekt, kosten in REPARATURKOSTEN.items():
        st.session_state.config[defekt] = st.number_input(f"🔧 {defekt.capitalize()} Reparaturkosten (€)", value=st.session_state.config.get(defekt, kosten))

    if st.button("💾 Konfiguration speichern"):
        save_config(st.session_state.config)
        st.success("Konfiguration gespeichert ✅")

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
        neue_anzeigen = scrape_ads(modell, min_preis, max_preis, nur_versand)

        # Filter: Nur neue oder geänderte Anzeigen speichern
        gefiltert = []
        for anzeige in neue_anzeigen:
            alt = get_existing_advert(anzeige["id"])
            if not alt or alt["preis"] != anzeige["price"]:
                save_advert(anzeige)
                gefiltert.append(anzeige)

        st.session_state.anzeigen = gefiltert

anzeigen = st.session_state.get("anzeigen", [])

if not anzeigen:
    st.warning("Keine neuen oder geänderten Anzeigen gefunden.")
else:
    st.success(f"{len(anzeigen)} neue oder aktualisierte Anzeigen gefunden")

    for idx, anzeige in enumerate(anzeigen):
        kosten_map = st.session_state.config
        reparaturkosten = anzeige.get("reparaturkosten", 0)
        max_ek = kosten_map["verkaufspreis"] - kosten_map["wunsch_marge"] - reparaturkosten

        farbe = (
            "#d4edda" if anzeige["price"] <= max_ek else
            "#d1ecf1" if anzeige["price"] <= kosten_map["verkaufspreis"] - kosten_map["wunsch_marge"] * 0.9 else
            "#f8d7da"
        )

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
                    <b>Reparaturkosten:</b> {reparaturkosten} €<br>
                    <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Beschreibung anzeigen"):
                st.write(anzeige["beschreibung"])

            st.markdown("**Defekte manuell auswählen (optional):**")
            manuelle_defekte = st.multiselect(
                label="Defekte", options=list(REPARATURKOSTEN.keys()),
                key=f"defekt_{idx}"
            )

            if manuelle_defekte:
                neue_reparatur = sum(kosten_map[d] for d in manuelle_defekte)
                neue_max_ek = kosten_map["verkaufspreis"] - neue_reparatur - kosten_map["wunsch_marge"]
                neue_bewertung = (
                    "gruen" if anzeige['price'] <= neue_max_ek else
                    "blau" if anzeige['price'] <= kosten_map["verkaufspreis"] - neue_reparatur - (kosten_map["wunsch_marge"] * 0.9) else
                    "rot"
                )

                st.markdown(f"🧾 Neue Reparaturkosten: **{neue_reparatur} €**")
                st.markdown(f"💰 Neuer max. Einkaufspreis: **{neue_max_ek:.2f} €**")
                st.markdown(f"🎯 Neue Bewertung: **{neue_bewertung.upper()}**")

            st.divider()

st.caption("🔧 Hinweis: Die Daten stammen von öffentlich zugänglichen Anzeigen auf kleinanzeigen.de")
