# app.py

import streamlit as st
import json
import os
from scraper import scrape_ads, REPARATURKOSTEN

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")
st.markdown("Durchsuche Angebote und bewerte sie nach Reparaturbedarf")

# 🧮 Bewertungsparameter mit Defaults
if "verkaufspreis" not in st.session_state:
    st.session_state.verkaufspreis = 500
if "wunsch_marge" not in st.session_state:
    st.session_state.wunsch_marge = 120
if "reparaturkosten" not in st.session_state:
    st.session_state.reparaturkosten = REPARATURKOSTEN.copy()

# 📁 Konfigurationsverzeichnis
CONFIG_DIR = "configs"
os.makedirs(CONFIG_DIR, exist_ok=True)

def save_config(name):
    data = {
        "verkaufspreis": st.session_state.verkaufspreis,
        "wunsch_marge": st.session_state.wunsch_marge,
        "reparaturkosten": st.session_state.reparaturkosten,
    }
    with open(os.path.join(CONFIG_DIR, f"{name}.json"), "w") as f:
        json.dump(data, f)

def load_config(name):
    with open(os.path.join(CONFIG_DIR, f"{name}.json"), "r") as f:
        data = json.load(f)
        st.session_state.verkaufspreis = data["verkaufspreis"]
        st.session_state.wunsch_marge = data["wunsch_marge"]
        st.session_state.reparaturkosten = data["reparaturkosten"]

# ⚙️ Konfiguration anzeigen
if st.checkbox("⚙️ Bewertungsparameter anzeigen / bearbeiten"):
    with st.expander("🛠 Bewertungsparameter konfigurieren", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Verkaufspreis (€)", min_value=0, step=10, key="verkaufspreis")
            st.number_input("Wunschmarge (€)", min_value=0, step=10, key="wunsch_marge")
        with col2:
            config_files = [f[:-5] for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
            selected = st.selectbox("🔁 Konfiguration laden", options=["-"] + config_files)
            if selected != "-":
                load_config(selected)
                st.success(f"🔁 Konfiguration '{selected}' geladen")

        st.markdown("### 🔩 Reparaturkosten pro Defekt")
        for defekt in st.session_state.reparaturkosten:
            st.number_input(
                label=f"{defekt.capitalize()} (€)",
                min_value=0,
                step=10,
                key=f"rk_{defekt}"
            )
            st.session_state.reparaturkosten[defekt] = st.session_state[f"rk_{defekt}"]

        new_name = st.text_input("💾 Konfiguration speichern als")
        if new_name and st.button("💾 Speichern"):
            save_config(new_name)
            st.success(f"💾 '{new_name}' gespeichert")

# 🔍 Suchformular
with st.form("filters"):
    col1, col2, col3 = st.columns(3)
    modell = col1.text_input("🔍 Gerätemodell", value="iPhone 14 Pro")
    min_preis = col2.number_input("💶 Mindestpreis", min_value=0, value=0)
    max_preis = col3.number_input("💶 Maximalpreis", min_value=0, value=1000)
    nur_versand = st.checkbox("📦 Nur mit Versand")
    submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

# 📦 Ergebnisse holen
if submit:
    with st.spinner("Suche läuft..."):
        st.session_state.anzeigen = scrape_ads(modell, min_preis, max_preis, nur_versand)

anzeigen = st.session_state.get("anzeigen", [])

# 📋 Ergebnisse anzeigen
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
                label="Defekte", options=list(st.session_state.reparaturkosten.keys()),
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