# app.py

import streamlit as st
from scraper import scrape_ads, REPARATURKOSTEN

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")
st.markdown("Durchsuche Angebote und bewerte sie nach Reparaturbedarf")

# 🧮 Bewertungsparameter (anpassbar)
if "verkaufspreis" not in st.session_state:
    st.session_state.verkaufspreis = 500
if "wunsch_marge" not in st.session_state:
    st.session_state.wunsch_marge = 120
if "reparaturkosten" not in st.session_state:
    st.session_state.reparaturkosten = REPARATURKOSTEN.copy()

# 🔧 Optional: Bewertungsparameter einblenden
if st.checkbox("⚙️ Bewertungsparameter anzeigen / bearbeiten"):
    with st.expander("🛠 Bewertungsparameter konfigurieren", expanded=True):
        st.session_state.verkaufspreis = st.slider("Verkaufspreis (€)", 100, 2000, st.session_state.verkaufspreis, step=10)
        st.session_state.wunsch_marge = st.slider("Wunschmarge (€)", 0, 500, st.session_state.wunsch_marge, step=10)
        st.markdown("### 🔩 Reparaturkosten pro Defekt")
        for defekt in st.session_state.reparaturkosten:
            st.session_state.reparaturkosten[defekt] = st.slider(
                f"{defekt.capitalize()} (€)", 0, 300, st.session_state.reparaturkosten[defekt], step=10
            )

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