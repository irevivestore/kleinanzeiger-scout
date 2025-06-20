import streamlit as st
import scraper
import db
import sys
import json
import requests
from PIL import Image
from io import BytesIO, StringIO

# Page config muss als erstes
st.set_page_config(page_title="📱 Kleinanzeigen Scout", layout="wide")

# Farben definieren
PRIMARY_COLOR = "#4B6FFF"  # Indigo
SECONDARY_COLOR = "#00D1B2"  # Türkis
SIDEBAR_COLOR = "#3A3F80"  # Dunkleres Indigo
TEXT_COLOR = "#FFFFFF"
INPUT_TEXT_COLOR = "#E0E0E0"
HEADER_COLOR = "#1A1D40"

# CSS Styling anwenden
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {HEADER_COLOR};
    }}
    section[data-testid="stSidebar"] {{
        background-color: {SIDEBAR_COLOR};
        color: {TEXT_COLOR};
    }}
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {{
        color: {INPUT_TEXT_COLOR} !important;
        background-color: #1A1D40 !important;
    }}
    .stButton > button {{
        background-color: {PRIMARY_COLOR};
        color: white;
    }}
    .stCheckbox > label, label, p, div, span {{
        color: {TEXT_COLOR} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# Init DB
db.init_db()

# Navigation
seite = st.sidebar.radio("📂 Seiten", ["🔍 Aktive Anzeigen", "📁 Archivierte Anzeigen"])

# iPhone Modell Auswahl
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

# Konfiguration laden
config = db.load_config(modell) or {
    "verkaufspreis": 1000,
    "wunsch_marge": 200,
    "reparaturkosten": {"display": 150, "akku": 80, "kamera": 100}
}

verkaufspreis = st.sidebar.number_input("📈 Verkaufspreis (€)", min_value=0, value=config["verkaufspreis"], step=10)
wunsch_marge = st.sidebar.number_input("🌟 Wunschmarge (€)", min_value=0, value=config["wunsch_marge"], step=10)

reparaturkosten_dict = {}
for i, (defekt, kosten) in enumerate(config["reparaturkosten"].items()):
    reparaturkosten_dict[defekt] = st.sidebar.number_input(
        f"🔧 {defekt.capitalize()} (€)", min_value=0, value=kosten, step=10, key=f"rk_{i}")

if st.sidebar.button("📂 Konfiguration speichern"):
    db.save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict)
    st.sidebar.success("✅ Konfiguration gespeichert")

# Bildanzeige Funktion
def show_image_carousel(bilder_liste, ad_id, created_at, updated_at):
    if not bilder_liste:
        st.write("Keine Bilder verfügbar.")
        return

    key_idx = f"img_idx_{ad_id}"
    if key_idx not in st.session_state:
        st.session_state[key_idx] = 0
    idx = st.session_state[key_idx]

    st.markdown(f"**Erfasst am:** {created_at} | **Letzte Änderung:** {updated_at}")

    col_img, col_left, col_right = st.columns([6, 1, 1])
    with col_img:
        img_url = bilder_liste[idx]
        try:
            response = requests.get(img_url, timeout=5)
            img = Image.open(BytesIO(response.content))
            st.image(img, width=300)
        except Exception as e:
            st.warning(f"Bild konnte nicht geladen werden: {str(e)}")

    with col_left:
        if st.button("←", key=f"prev_{ad_id}"):
            st.session_state[key_idx] = (idx - 1) % len(bilder_liste)
    with col_right:
        if st.button("→", key=f"next_{ad_id}"):
            st.session_state[key_idx] = (idx + 1) % len(bilder_liste)

    st.caption(f"Bild {idx + 1} von {len(bilder_liste)}")

# Seitenlogik
if seite == "🔍 Aktive Anzeigen":
    st.header("🔍 Aktive Kleinanzeigen")

    with st.form("filters"):
        col1, col2 = st.columns(2)
        min_preis = col1.number_input("💶 Mindestpreis", min_value=0, value=0)
        max_preis = col2.number_input("💶 Maximalpreis", min_value=0, value=1500)
        nur_versand = st.checkbox("📦 Nur mit Versand", value=False)
        nur_angebote = st.checkbox("📢 Nur Angebote", value=True)
        submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

    if submit:
        st.write("👉 Hier würde der Scraper starten (nicht aktiviert in dieser Version).")

    alle_anzeigen = db.get_all_adverts_for_model(modell)
    if not alle_anzeigen:
        st.info("ℹ️ Keine gespeicherten Anzeigen verfügbar.")

    for anzeige in alle_anzeigen:
        bilder = anzeige.get("bilder_liste", [])
        if not bilder and anzeige.get("image"):
            bilder = [anzeige.get("image")]

        man_defekt_keys = anzeige.get("man_defekt_keys", [])
        reparatur_summe = sum(reparaturkosten_dict.get(key, 0) for key in man_defekt_keys)
        max_ek = verkaufspreis - wunsch_marge - reparatur_summe
        pot_gewinn = verkaufspreis - reparatur_summe - anzeige.get("price", 0)

        st.subheader(f"[{anzeige['title']}]({anzeige['link']})")

        show_image_carousel(bilder, anzeige["id"], anzeige.get("created_at", "-"), anzeige.get("updated_at", "-"))

        st.write(f"💰 Preis: **{anzeige['price']} €**")
        st.write(f"📉 Max. EK: **{max_ek:.2f} €**")
        st.write(f"📈 Gewinn: **{pot_gewinn:.2f} €**")
        st.write(f"🔧 Defekte: {', '.join(man_defekt_keys) if man_defekt_keys else 'Keine'}")
        st.write(f"🧾 Reparaturkosten: {reparatur_summe} €")

        defekte_select = st.multiselect(
            "🔧 Defekte wählen:", options=list(reparaturkosten_dict.keys()),
            default=man_defekt_keys, key=f"defekte_{anzeige['id']}"
        )

        if st.button("Speichern", key=f"save_{anzeige['id']}"):
            db.update_manual_defekt_keys(anzeige["id"], json.dumps(defekte_select))
            st.rerun()

        if st.button("Archivieren", key=f"archive_{anzeige['id']}"):
            db.archive_advert(anzeige["id"], True)
            st.success("Anzeige archiviert.")
            st.rerun()

        with st.expander("📄 Beschreibung"):
            st.markdown(anzeige["beschreibung"], unsafe_allow_html=True)

elif seite == "📁 Archivierte Anzeigen":
    st.header("📁 Archivierte Anzeigen")

    archivierte = db.get_archived_adverts_for_model(modell)
    if not archivierte:
        st.info("ℹ️ Keine archivierten Anzeigen.")

    for anzeige in archivierte:
        bilder = anzeige.get("bilder_liste", [])
        if not bilder and anzeige.get("image"):
            bilder = [anzeige.get("image")]

        man_defekt_keys = anzeige.get("man_defekt_keys", [])
        reparatur_summe = sum(reparaturkosten_dict.get(key, 0) for key in man_defekt_keys)
        max_ek = verkaufspreis - wunsch_marge - reparatur_summe
        pot_gewinn = verkaufspreis - reparatur_summe - anzeige.get("price", 0)

        st.subheader(f"[{anzeige['title']}]({anzeige['link']})")
        show_image_carousel(bilder, "archiv_" + anzeige["id"], anzeige.get("created_at", "-"), anzeige.get("updated_at", "-"))
        st.write(f"💰 Preis: **{anzeige['price']} €**")
        st.write(f"📉 Max. EK: **{max_ek:.2f} €**")
        st.write(f"📈 Gewinn: **{pot_gewinn:.2f} €**")
        st.write(f"🔧 Defekte: {', '.join(man_defekt_keys) if man_defekt_keys else 'Keine'}")
        st.write(f"🧾 Reparaturkosten: {reparatur_summe} €")

        with st.expander("📄 Beschreibung"):
            st.markdown(anzeige["beschreibung"], unsafe_allow_html=True)