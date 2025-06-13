import streamlit as st
import json
import base64
from datetime import datetime
from db import (
    get_all_active_adverts,
    get_archived_adverts_for_model,
    load_config,
    update_manual_defekt_keys,
    archive_advert,
)

# ----- DESIGN KONFIG -----
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")

PRIMARY_COLOR = "#4B6FFF"
SECONDARY_COLOR = "#00D1B2"
BG_COLOR = "#F4F4F4"
CARD_COLOR = "white"
TEXT_COLOR = "#333"

st.markdown(
    f"""
    <style>
    body {{
        background-color: {BG_COLOR};
        color: {TEXT_COLOR};
    }}
    .card {{
        background-color: {CARD_COLOR};
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 0 10px rgba(0,0,0,0.05);
    }}
    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border: none;
        border-radius: 4px;
    }}
    .stButton>button:hover {{
        background-color: {SECONDARY_COLOR};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ----- HILFSFUNKTIONEN -----
def bewertung_berechnen(ad, config, defekt_keys):
    rep_kosten = sum(config["reparaturkosten"].get(key, 0) for key in defekt_keys)
    zielpreis = config["verkaufspreis"] - config["wunsch_marge"] - rep_kosten
    differenz = ad["price"] - zielpreis
    status = "✅" if ad["price"] <= zielpreis else "❌"
    return zielpreis, status, rep_kosten, differenz

def lade_bild_als_base64(url):
    try:
        import requests
        r = requests.get(url)
        return base64.b64encode(r.content).decode()
    except:
        return None

# ----- SEITENAUSWAHL -----
seite = st.sidebar.radio("Ansicht", ["Aktive Anzeigen", "Archivierte Anzeigen"])

# ----- MODELLAUSWAHL -----
alle_anzeigen = get_all_active_adverts()
alle_modelle = sorted(set(ad["modell"] for ad in alle_anzeigen))
modell = st.sidebar.selectbox("Modell auswählen", alle_modelle)

config = load_config(modell)
if not config:
    st.warning("Für dieses Modell wurde noch keine Konfiguration gespeichert.")
    st.stop()

if seite == "Aktive Anzeigen":
    anzeigen = [ad for ad in alle_anzeigen if ad["modell"] == modell and ad["title"]]
else:
    anzeigen = get_archived_adverts_for_model(modell)

# ----- ANZEIGEN -----
st.title(f"{'Archivierte' if seite == 'Archivierte Anzeigen' else 'Aktive'} Anzeigen für {modell}")
for ad in anzeigen:
    with st.container():
        col1, col2 = st.columns([1, 3])

        with col1:
            if ad["image"]:
                st.image(ad["image"], width=120)
            st.markdown(f"**{ad['price']} €**")
            zielpreis, status, rep_kosten, diff = bewertung_berechnen(
                ad, config, json.loads(ad["man_defekt_keys"] or "[]")
            )
            st.markdown(f"{status} Ziel: {zielpreis} €")
            st.markdown(f"↯ Differenz: {diff:+} €")
            st.markdown(f"🔧 Rep.: {rep_kosten} €")

        with col2:
            st.markdown(f"### {ad['title']}")
            st.markdown(f"[🔗 Zum Angebot]({ad['link']})")
            st.markdown(f"✉️ Versand: {'Ja' if ad['versand'] else 'Nein'}")
            st.markdown(f"📅 Erstellt: {ad.get('created_at', '')[:10]} — Aktualisiert: {ad.get('updated_at', '')[:10]}")
            with st.expander("📄 Beschreibung anzeigen"):
                st.markdown(ad["beschreibung"])

            # Manuelle Defektbewertung
            defektauswahl = st.multiselect(
                "Defekte auswählen:",
                options=list(config["reparaturkosten"].keys()),
                default=json.loads(ad["man_defekt_keys"] or "[]"),
                key=f"defekte_{ad['id']}"
            )
            update_manual_defekt_keys(ad["id"], json.dumps(defektauswahl))

            # Archivieren / Reaktivieren
            if seite == "Aktive Anzeigen":
                if st.button("🗃️ Archivieren", key=f"arch_{ad['id']}"):
                    archive_advert(ad["id"], archived=True)
                    st.experimental_rerun()
            else:
                if st.button("🔁 Wiederherstellen", key=f"restore_{ad['id']}"):
                    archive_advert(ad["id"], archived=False)
                    st.experimental_rerun()
