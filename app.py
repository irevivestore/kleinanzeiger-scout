import streamlit as st
import json
import sys
from io import StringIO
from PIL import Image
import requests
from datetime import datetime
from scraper import scrape_kleinanzeigen
from db import (
    init_db, save_advert, get_all_adverts_for_model,
    load_config, save_config, update_manual_defekt_keys,
    archive_advert, get_archived_adverts_for_model, is_advert_archived
)
from config import (
    REPARATURKOSTEN_DEFAULT,
    VERKAUFSPREIS_DEFAULT,
    WUNSCH_MARGE_DEFAULT
)

# Farben
PRIMARY_COLOR = "#4B6FFF"    # Indigo
SECONDARY_COLOR = "#00D1B2"  # Türkis
BACKGROUND_COLOR = "#252850" # Dunkler Hintergrund
SIDEBAR_COLOR = "#003D46"    # Neue Sidebar Farbe

# Styles setzen
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {BACKGROUND_COLOR};
    }}
    .st-emotion-cache-6qob1r {{
        background-color: {SIDEBAR_COLOR} !important;
    }}
    .stButton>button {{
        color: white;
        background-color: {PRIMARY_COLOR};
    }}
    .stTextInput>div>div>input, .stNumberInput>div>input, .stSelectbox>div>div>div {{
        background-color: white;
        color: black;
    }}
    .stCheckbox>label, .stNumberInput>label, .stSelectbox>label {{
        color: white !important;
    }}
    .stFormSubmitButton>button {{
        background-color: white !important;
        color: black !important;
    }}
    </style>
""", unsafe_allow_html=True)

# Initialize
init_db()

# Navigation
seite = st.sidebar.radio("📂 Seiten", ["🔍 Aktive Anzeigen", "📁 Archivierte Anzeigen"])

# Modell-Auswahl
IPHONE_MODELLE = [
    "iPhone X", "iPhone XR", "iPhone XS", "iPhone XS Max",
    "iPhone 11", "iPhone 11 Pro", "iPhone 11 Pro Max",
    "iPhone 12", "iPhone 12 mini", "iPhone 12 Pro", "iPhone 12 Pro Max",
    "iPhone 13", "iPhone 13 mini", "iPhone 13 Pro", "iPhone 13 Pro Max",
    "iPhone 14", "iPhone 14 Plus", "iPhone 14 Pro", "iPhone 14 Pro Max",
    "iPhone 15", "iPhone 15 Plus", "iPhone 15 Pro", "iPhone 15 Pro Max"
]

if "modell" not in st.session_state:
    st.session_state.modell = "iPhone 14 Pro"
modell = st.sidebar.selectbox("Modell auswählen", IPHONE_MODELLE, index=IPHONE_MODELLE.index(st.session_state.modell))
st.session_state.modell = modell

config = load_config(modell) or {
    "verkaufspreis": VERKAUFSPREIS_DEFAULT,
    "wunsch_marge": WUNSCH_MARGE_DEFAULT,
    "reparaturkosten": REPARATURKOSTEN_DEFAULT.copy()
}

verkaufspreis = st.sidebar.number_input("📈 Verkaufspreis (€)", min_value=0, value=config["verkaufspreis"], step=10)
wunsch_marge = st.sidebar.number_input("🌟 Wunschmarge (€)", min_value=0, value=config["wunsch_marge"], step=10)

reparaturkosten_dict = {}
for i, (defekt, kosten) in enumerate(config["reparaturkosten"].items()):
    reparaturkosten_dict[defekt] = st.sidebar.number_input(
        f"🔧 {defekt.capitalize()} (€)", min_value=0, value=kosten, step=10, key=f"rk_{i}")

if st.sidebar.button("📂 Konfiguration speichern"):
    save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict)
    st.sidebar.success("✅ Konfiguration gespeichert")

# Debug Log
if 'log_buffer' not in st.session_state:
    st.session_state.log_buffer = StringIO()
    st.session_state.log_lines = []

log_area = st.empty()

def log(message):
    print(message, file=sys.stderr)
    st.session_state.log_buffer.write(message + "\n")
    st.session_state.log_lines.append(message)
    log_area.text_area("🛠 Debug-Ausgaben", value="\n".join(st.session_state.log_lines[-50:]), height=300)

# Bildanzeige
def show_image_carousel(bilder_liste, ad_id, created_at, updated_at):
    if not bilder_liste:
        st.write("Keine Bilder verfügbar.")
        return

    key_idx = f"img_idx_{ad_id}"
    if key_idx not in st.session_state:
        st.session_state[key_idx] = 0
    idx = st.session_state[key_idx]

    st.image(bilder_liste[idx], width=300)
    st.write(f"Erfasst am: {created_at}  |  Letzte Änderung: {updated_at}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("←", key=f"prev_{ad_id}"):
            st.session_state[key_idx] = (idx - 1) % len(bilder_liste)
    with col2:
        if st.button("→", key=f"next_{ad_id}"):
            st.session_state[key_idx] = (idx + 1) % len(bilder_liste)

    st.caption(f"Bild {idx + 1} von {len(bilder_liste)}")

# Seitenlogik
if seite == "🔍 Aktive Anzeigen":
    st.title("🔍 Aktive Kleinanzeigen")

    with st.form("filters"):
        col1, col2 = st.columns(2)
        min_preis = col1.number_input("💶 Mindestpreis", min_value=0, value=0)
        max_preis = col2.number_input("💶 Maximalpreis", min_value=0, value=1500)
        nur_versand = st.checkbox("📦 Nur mit Versand")
        nur_angebote = st.checkbox("📢 Nur Angebote", value=True)
        submit = st.form_submit_button("Anzeigen durchsuchen")

    if submit:
        st.session_state.log_lines.clear()
        st.session_state.log_buffer.seek(0)
        st.session_state.log_buffer.truncate(0)

        with st.spinner("Suche läuft..."):
            neue_anzeigen = scrape_kleinanzeigen(
                modell,
                min_price=min_preis,
                max_price=max_preis,
                nur_versand=nur_versand,
                nur_angebote=nur_angebote,
                debug=True,
                config={
                    "verkaufspreis": verkaufspreis,
                    "wunsch_marge": wunsch_marge,
                    "reparaturkosten": reparaturkosten_dict,
                },
                log=log
            )

        gespeicherte = 0
        for anzeige in neue_anzeigen:
            if not is_advert_archived(anzeige["id"]):
                save_advert(anzeige)
                gespeicherte += 1

        if gespeicherte:
            st.success(f"{gespeicherte} neue Anzeigen gespeichert.")
        else:
            st.warning("Keine neuen, relevanten Anzeigen gefunden.")

    alle_anzeigen = get_all_adverts_for_model(modell)
    if not alle_anzeigen:
        st.info("ℹ️ Keine gespeicherten Anzeigen verfügbar.")

    for anzeige in alle_anzeigen:
        bilder = anzeige.get("bilder_liste", [])
        if isinstance(bilder, str):
            try:
                bilder = json.loads(bilder or "[]")
            except:
                bilder = []
        if not bilder and anzeige.get("image"):
            bilder = [anzeige.get("image")]

        man_defekt_keys = anzeige.get("man_defekt_keys", [])
        reparatur_summe = sum(reparaturkosten_dict.get(key, 0) for key in man_defekt_keys)
        max_ek = verkaufspreis - wunsch_marge - reparatur_summe
        pot_gewinn = verkaufspreis - reparatur_summe - anzeige.get("price", 0)

        st.markdown("---")
        st.markdown(f"### [{anzeige['title']}]({anzeige['link']})")
        show_image_carousel(bilder, anzeige["id"], anzeige.get("created_at", ""), anzeige.get("updated_at", ""))

        st.markdown(
            f"💰 Preis: **{anzeige['price']} €**  \n"
            f"📉 Max. EK: **{max_ek:.2f} €**  \n"
            f"📈 Gewinn: **{pot_gewinn:.2f} €**"
        )
        st.markdown(f"🔧 Defekte: {', '.join(man_defekt_keys) if man_defekt_keys else 'Keine'}")
        st.markdown(f"🧾 Reparaturkosten: {reparatur_summe} €")

        defekte_select = st.multiselect(
            "Defekte wählen:",
            options=list(reparaturkosten_dict.keys()),
            default=man_defekt_keys,
            key=f"man_defekt_select_{anzeige['id']}"
        )

        if st.button("Speichern", key=f"save_{anzeige['id']}"):
            update_manual_defekt_keys(anzeige["id"], json.dumps(defekte_select))
            st.rerun()

        if st.button("Archivieren", key=f"archive_{anzeige['id']}"):
            archive_advert(anzeige["id"], True)
            st.success("Anzeige archiviert.")
            st.rerun()

        with st.expander("Beschreibung"):
            st.markdown(anzeige["beschreibung"], unsafe_allow_html=True)

elif seite == "📁 Archivierte Anzeigen":
    st.title("📁 Archivierte Anzeigen")

    archivierte = get_archived_adverts_for_model(modell)
    if not archivierte:
        st.info("ℹ️ Keine archivierten Anzeigen verfügbar.")

    for anzeige in archivierte:
        bilder = anzeige.get("bilder_liste", [])
        if isinstance(bilder, str):
            try:
                bilder = json.loads(bilder or "[]")
            except:
                bilder = []
        if not bilder and anzeige.get("image"):
            bilder = [anzeige.get("image")]

        man_defekt_keys = anzeige.get("man_defekt_keys", [])
        reparatur_summe = sum(reparaturkosten_dict.get(key, 0) for key in man_defekt_keys)
        max_ek = verkaufspreis - wunsch_marge - reparatur_summe
        pot_gewinn = verkaufspreis - reparatur_summe - anzeige.get("price", 0)

        st.markdown("---")
        st.markdown(f"### [{anzeige['title']}]({anzeige['link']})")
        show_image_carousel(bilder, anzeige["id"], anzeige.get("created_at", ""), anzeige.get("updated_at", ""))

        st.markdown(
            f"💰 Preis: **{anzeige['price']} €**  \n"
            f"📉 Max. EK: **{max_ek:.2f} €**  \n"
            f"📈 Gewinn: **{pot_gewinn:.2f} €**"
        )
        st.markdown(f"🔧 Defekte: {', '.join(man_defekt_keys) if man_defekt_keys else 'Keine'}")
        st.markdown(f"🧾 Reparaturkosten: {reparatur_summe} €")

        with st.expander("Beschreibung"):
            st.markdown(anzeige["beschreibung"], unsafe_allow_html=True)
