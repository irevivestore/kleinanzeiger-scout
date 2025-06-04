# app.py

import streamlit as st
from scraper import scrape_ads
from db import init_db, save_advert, get_existing_advert, load_config, save_config
from config import REPARATURKOSTEN_DEFAULT, VERKAUFSPREIS_DEFAULT, WUNSCH_MARGE_DEFAULT

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")
st.markdown("Durchsuche Angebote und bewerte sie nach Reparaturbedarf")

# Datenbank initialisieren
init_db()

if "anzeigen" not in st.session_state:
    st.session_state.anzeigen = []

if "config" not in st.session_state:
    modell_init = "iPhone 14 Pro"
    config = load_config(modell_init)
    if config is None:
        config = {
            "reparaturkosten": REPARATURKOSTEN_DEFAULT.copy(),
            "verkaufspreis": VERKAUFSPREIS_DEFAULT,
            "wunsch_marge": WUNSCH_MARGE_DEFAULT,
        }
    st.session_state.config = config

# Formular für die Suche
with st.form("filters"):
    col1, col2, col3 = st.columns(3)
    modell = col1.text_input("🔍 Gerätemodell", value="iPhone 14 Pro")
    min_preis = col2.number_input("💶 Mindestpreis", min_value=0, value=0)
    max_preis = col3.number_input("💶 Maximalpreis", min_value=0, value=1000)
    nur_versand = st.checkbox("📦 Nur mit Versand")
    submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

# Konfiguration anpassen (optional ein-/ausblendbar)
with st.expander("⚙️ Bewertungsparameter anpassen"):
    st.markdown("### Reparaturkosten pro Defekt")
    for i, (defekt, kosten) in enumerate(st.session_state.config["reparaturkosten"].items()):
        neue_kosten = st.number_input(f"{defekt.capitalize()} (€)", min_value=0, max_value=1000, value=kosten, step=10, key=f"rk_{i}")
        st.session_state.config["reparaturkosten"][defekt] = neue_kosten

    st.session_state.config["verkaufspreis"] = st.number_input("📈 Verkaufspreis (€)", min_value=0, value=st.session_state.config["verkaufspreis"], step=10)
    st.session_state.config["wunsch_marge"] = st.number_input("💰 Wunschmarge (€)", min_value=0, value=st.session_state.config["wunsch_marge"], step=10)

    if st.button("💾 Konfiguration speichern"):
        save_config(modell, st.session_state.config)
        st.success("Konfiguration gespeichert")

if submit:
    with st.spinner("Suche läuft..."):
        st.session_state.anzeigen = scrape_ads(modell, min_preis, max_preis, nur_versand, st.session_state.config)

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
                    <b>Erfasst:</b> {anzeige.get('created_at', '-')}, <b>Update:</b> {anzeige.get('updated_at', '-')}
                    <br><a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Beschreibung anzeigen"):
                st.write(anzeige["beschreibung"])

            st.markdown("**Defekte manuell auswählen (optional):**")
            manuelle_defekte = st.multiselect(
                label="Defekte", options=list(st.session_state.config["reparaturkosten"].keys()),
                key=f"defekt_{idx}"
            )

            if manuelle_defekte:
                neue_reparatur = sum(st.session_state.config["reparaturkosten"][d] for d in manuelle_defekte)
                neue_max_ek = st.session_state.config["verkaufspreis"] - neue_reparatur - st.session_state.config["wunsch_marge"]
                neue_bewertung = (
                    "gruen" if anzeige['price'] <= neue_max_ek else
                    "blau" if anzeige['price'] <= st.session_state.config["verkaufspreis"] - neue_reparatur - (st.session_state.config["wunsch_marge"] * 0.9) else
                    "rot"
                )

                st.markdown(f"🧾 Neue Reparaturkosten: **{neue_reparatur} €**")
                st.markdown(f"💰 Neuer max. Einkaufspreis: **{neue_max_ek:.2f} €**")
                st.markdown(f"🎯 Neue Bewertung: **{neue_bewertung.upper()}**")

            st.divider()

st.caption("🔧 Hinweis: Die Daten stammen von öffentlich zugänglichen Anzeigen auf kleinanzeigen.de")