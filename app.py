# streamlit_app.py
import streamlit as st
from scraper import scrape_ads

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("🔎 Kleinanzeigen Scooooout")

modell = st.text_input("Gerätemodell eingeben", value="iPhone 14 Pro")

col1, col2 = st.columns(2)
with col1:
    min_preis = st.number_input("Mindestpreis", min_value=0, value=100)
with col2:
    max_preis = st.number_input("Maximalpreis", min_value=0, value=600)

nur_versand = st.checkbox("Nur mit Versandoption")

if st.button("Anzeigen abrufen"):
    with st.spinner("Daten werden geladen..."):
        ergebnisse = scrape_ads(modell, min_preis, max_preis, nur_versand)

    if not ergebnisse:
        st.warning("Keine passenden Anzeigen gefunden.")
    else:
        st.success(f"{len(ergebnisse)} Anzeigen gefunden")
        for eintrag in ergebnisse:
            with st.container():
                cols = st.columns([1, 4])
                with cols[0]:
                    if eintrag["image"]:
                        st.image(eintrag["image"], width=100)
                with cols[1]:
                    st.subheader(f"{eintrag['title']} – {eintrag['price']} €")
                    st.markdown(f"[🔗 Anzeige öffnen]({eintrag['link']})")
