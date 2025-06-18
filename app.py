import streamlit as st
import db
import scraper
import asyncio
import json
from PIL import Image
import requests
from io import BytesIO

st.set_page_config(page_title="Kleinanzeigen Scout", page_icon="📱", layout="wide")

PRIMARY_COLOR = "#4B6FFF"
SECONDARY_COLOR = "#00D1B2"
BACKGROUND_COLOR = "#F4F4F4"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {BACKGROUND_COLOR};
    }}
    .stButton>button {{
        color: white;
        background-color: {PRIMARY_COLOR};
    }}
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("📱 Kleinanzeigen Scout")
page = st.sidebar.selectbox("Seite auswählen", ["Aktive Anzeigen", "Archivierte Anzeigen", "Neue Suche starten"])

db.init_db()

def show_image_carousel(bilder_liste, ad_id):
    if not bilder_liste:
        st.write("Keine Bilder vorhanden.")
        return

    # Session State für Bildindex initialisieren, falls noch nicht da
    if f"img_idx_{ad_id}" not in st.session_state:
        st.session_state[f"img_idx_{ad_id}"] = 0

    idx = st.session_state[f"img_idx_{ad_id}"]

    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        if st.button("←", key=f"prev_{ad_id}"):
            st.session_state[f"img_idx_{ad_id}"] = (idx - 1) % len(bilder_liste)
    with col2:
        img_url = bilder_liste[idx]
        try:
            response = requests.get(img_url)
            img = Image.open(BytesIO(response.content))
            st.image(img, use_column_width=True)
            st.caption(f"Bild {idx + 1} von {len(bilder_liste)}")
        except:
            st.write("Bild konnte nicht geladen werden.")
    with col3:
        if st.button("→", key=f"next_{ad_id}"):
            st.session_state[f"img_idx_{ad_id}"] = (idx + 1) % len(bilder_liste)

if page == "Neue Suche starten":
    st.header("🔎 Neue Suche starten")
    modell = st.text_input("iPhone Modell eingeben", "iPhone 11 Pro Max")
    verkaufspreis = st.number_input("Geplanter Verkaufspreis", min_value=0, value=500)
    wunsch_marge = st.number_input("Gewünschte Marge", min_value=0, value=100)

    st.write("Reparaturkosten (optional):")
    reparaturkosten = {}
    for defekt in ["Display", "Akku", "Backcover", "FaceID"]:
        kosten = st.number_input(f"{defekt}-Kosten", min_value=0, value=0, key=defekt)
        if kosten > 0:
            reparaturkosten[defekt.lower()] = kosten

    if st.button("Suche starten"):
        db.save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten)
        with st.spinner("Suche läuft..."):
            asyncio.run(scraper.scrape_kleinanzeigen(modell, verkaufspreis, wunsch_marge, reparaturkosten, debug=True))
        st.success("Suche abgeschlossen!")

if page == "Aktive Anzeigen":
    st.header("📄 Aktive Anzeigen")

    modelle = ["iPhone 11 Pro Max", "iPhone 12", "iPhone 13 Pro", "iPhone 14 Pro"]
    selected_modell = st.selectbox("Modell auswählen", modelle)

    anzeigen = db.get_all_adverts_for_model(selected_modell, include_archived=False)

    for ad in anzeigen:
        with st.expander(f"{ad['title']} - {ad['price']} €"):
            st.write(f"**Link:** [Anzeigenlink]({ad['link']})")
            st.write(f"**Versand:** {'Ja' if ad['versand'] else 'Nein'}")
            st.write(f"**Beschreibung:** {ad['beschreibung']}")

            bilder_liste = []
            if 'bilder_liste' in ad and ad['bilder_liste']:
                try:
                    bilder_liste = json.loads(ad['bilder_liste']) if isinstance(ad['bilder_liste'], str) else ad['bilder_liste']
                except:
                    bilder_liste = []
            if not bilder_liste and ad['image']:
                bilder_liste = [ad['image']]

            show_image_carousel(bilder_liste, ad['id'])

            if st.button("Archivieren", key="archive_" + ad['id']):
                db.archive_advert(ad['id'], True)
                st.experimental_rerun()

if page == "Archivierte Anzeigen":
    st.header("🗄️ Archivierte Anzeigen")

    modelle = ["iPhone 11 Pro Max", "iPhone 12", "iPhone 13 Pro", "iPhone 14 Pro"]
    selected_modell = st.selectbox("Modell auswählen", modelle, key="archiv_select")

    archivierte = db.get_archived_adverts_for_model(selected_modell)

    for ad in archivierte:
        with st.expander(f"{ad['title']} - {ad['price']} €"):
            st.write(f"**Link:** [Anzeigenlink]({ad['link']})")
            st.write(f"**Versand:** {'Ja' if ad['versand'] else 'Nein'}")
            st.write(f"**Beschreibung:** {ad['beschreibung']}")

            bilder_liste = []
            if 'bilder_liste' in ad and ad['bilder_liste']:
                try:
                    bilder_liste = json.loads(ad['bilder_liste']) if isinstance(ad['bilder_liste'], str) else ad['bilder_liste']
                except:
                    bilder_liste = []
            if not bilder_liste and ad['image']:
                bilder_liste = [ad['image']]

            show_image_carousel(bilder_liste, "archiv_" + ad['id'])

            if st.button("Zurückholen", key="restore_" + ad['id']):
                db.archive_advert(ad['id'], False)
                st.experimental_rerun()
