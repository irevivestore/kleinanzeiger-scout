# app.py

import streamlit as st
from scraper import scrape_ads
from db import init_db, save_advert, get_existing_advert, load_config, save_config
from config import REPARATURKOSTEN_DEFAULT, VERKAUFSPREIS_DEFAULT, WUNSCH_MARGE_DEFAULT

init_db()

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")
st.markdown("Durchsuche Angebote und bewerte sie nach Reparaturbedarf")

if "anzeigen" not in st.session_state:
    st.session_state.anzeigen = []

if "modell" not in st.session_state:
    st.session_state.modell = "iPhone 14 Pro"

if "config" not in st.session_state:
    st.session_state.config = load_config(st.session_state.modell)

# Konfigurationsbereich
with st.expander("⚙️ Bewertungsparameter anpassen", expanded=False):
    col1, col2 = st.columns(2)
    st.session_state.config["verkaufspreis"] = col1.number_input("📈 Verkaufspreis (€)", value=st.session_state.config.get("verkaufspreis", VERKAUFSPREIS_DEFAULT))
    st.session_state.config["wunsch_marge"] = col2.number_input("💰 Wunschmarge (€)", value=st.session_state.config.get("wunsch_marge", WUNSCH_MARGE_DEFAULT))

    st.markdown("### Reparaturkosten pro Defekt")
    for defekt in REPARATURKOSTEN_DEFAULT:
        st.session_state.config["reparaturkosten"][defekt] = st.number_input(
            f"🔧 {defekt.capitalize()} (€)",
            min_value=0,
            value=st.session_state.config["reparaturkosten"].get(defekt, REPARATURKOSTEN_DEFAULT[defekt]),
            step=10
        )

    if st.button("💾 Konfiguration speichern"):
        save_config(st.session_state.modell, st.session_state.config)
        st.success("Konfiguration gespeichert.")

# Formular für die Suche
with st.form("filters"):
    col1, col2, col3 = st.columns(3)
    modell = col1.text_input("🔍 Gerätemodell", value=st.session_state.modell)
    min_preis = col2.number_input("💶 Mindestpreis", min_value=0, value=0)
    max_preis = col3.number_input("💶 Maximalpreis", min_value=0, value=1000)
    nur_versand = st.checkbox("📦 Nur mit Versand")
    submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

if submit:
    st.session_state.modell = modell
    st.session_state.config = load_config(modell)
    with st.spinner("Suche läuft..."):
        neue_anzeigen = scrape_ads(modell, min_preis, max_preis, nur_versand)

        # Vergleichen und speichern
        for anzeige in neue_anzeigen:
            existierende = get_existing_advert(anzeige["link"])
            if existierende:
                if existierende["price"] != anzeige["price"]:
                    save_advert(anzeige, updated=True)
            else:
                save_advert(anzeige)

        st.session_state.anzeigen = neue_anzeigen

anzeigen = st.session_state.anzeigen

if not anzeigen:
    st.warning("Keine Anzeigen gefunden.")
else:
    st.success(f"{len(anzeigen)} Anzeigen gefunden")

    for idx, anzeige in enumerate(anzeigen):
        defektauswahl = st.multiselect(f"Defekte für Anzeige {idx+1}", list(st.session_state.config["reparaturkosten"].keys()), key=f"defekte_{idx}")

        kosten = sum(st.session_state.config["reparaturkosten"][d] for d in defektauswahl)
        max_ek = st.session_state.config["verkaufspreis"] - st.session_state.config["wunsch_marge"] - kosten
        bewertung = (
            "gruen" if anzeige["price"] <= max_ek else
            "blau" if anzeige["price"] <= st.session_state.config["verkaufspreis"] - kosten - (st.session_state.config["wunsch_marge"] * 0.9) else
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
                    <b>Reparaturkosten:</b> {kosten} €<br>
                    <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Beschreibung anzeigen"):
                st.write(anzeige["beschreibung"])

            st.divider()

st.caption("🔧 Hinweis: Die Daten stammen von öffentlich zugänglichen Anzeigen auf kleinanzeigen.de")