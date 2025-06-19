import streamlit as st
import sys
import json
from io import StringIO, BytesIO
import requests
from PIL import Image
from scraper import scrape_kleinanzeigen
from db import (
    init_db, save_advert, get_all_adverts_for_model,
    load_config, save_config, update_manual_defekt_keys,
    archive_advert, get_archived_adverts_for_model, is_advert_archived
)
from config import (
    REPARATURKOSTEN_DEFAULT, VERKAUFSPREIS_DEFAULT, WUNSCH_MARGE_DEFAULT
)

# Farben
PRIMARY_COLOR = "#4B6FFF"
SECONDARY_COLOR = "#00D1B2"
BACKGROUND_COLOR = "#252850"
CARD_COLOR = "#2E2E3A"

# Global CSS
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {BACKGROUND_COLOR};
        color: white;
    }}
    .card {{
        background-color: {CARD_COLOR};
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
        margin-bottom: 30px;
    }}
    .primary-button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
    }}
    .archive-button {{
        background-color: {SECONDARY_COLOR};
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
    }}
    </style>
""", unsafe_allow_html=True)

# Init DB
init_db()

# Sidebar
seite = st.sidebar.radio("📂 Seiten", ["🔍 Aktive Anzeigen", "📁 Archivierte Anzeigen"])

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

# Bilder anzeigen
def show_image(bilder_liste, idx):
    img_url = bilder_liste[idx]
    try:
        response = requests.get(img_url, timeout=5)
        img = Image.open(BytesIO(response.content))
        st.image(img, use_container_width=True)
    except:
        st.warning("Bild konnte nicht geladen werden.")

# Aktive Anzeigen
if seite == "🔍 Aktive Anzeigen":
    st.header("🔍 Aktive Kleinanzeigen")

    with st.form("filters"):
        col1, col2 = st.columns(2)
        min_preis = col1.number_input("💶 Mindestpreis", min_value=0, value=0)
        max_preis = col2.number_input("💶 Maximalpreis", min_value=0, value=1500)
        nur_versand = st.checkbox("📦 Nur mit Versand")
        nur_angebote = st.checkbox("📢 Nur Angebote", value=True)
        submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

    if submit:
        st.session_state.log_lines.clear()
        st.session_state.log_buffer.seek(0)
        st.session_state.log_buffer.truncate(0)

        with st.spinner("Suche läuft..."):
            neue_anzeigen = scrape_kleinanzeigen(
                modell, min_preis, max_preis, nur_versand, nur_angebote, True,
                {"verkaufspreis": verkaufspreis, "wunsch_marge": wunsch_marge, "reparaturkosten": reparaturkosten_dict}, log
            )
        gespeicherte = 0
        for anzeige in neue_anzeigen:
            if not is_advert_archived(anzeige["id"]):
                save_advert(anzeige)
                gespeicherte += 1
        st.success(f"{gespeicherte} neue Anzeigen gespeichert." if gespeicherte else "Keine neuen Anzeigen.")

    alle_anzeigen = [a for a in get_all_adverts_for_model(modell) if not is_advert_archived(a["id"])]
    if not alle_anzeigen:
        st.info("ℹ️ Keine gespeicherten Anzeigen verfügbar.")

    for anzeige in alle_anzeigen:
        bilder = json.loads(anzeige.get("bilder_liste") or "[]") if isinstance(anzeige.get("bilder_liste"), str) else anzeige.get("bilder_liste", [])
        if not bilder and anzeige.get("image"):
            bilder = [anzeige["image"]]
        man_defekt_keys = json.loads(anzeige.get("man_defekt_keys") or "[]")
        reparatur_summe = sum(reparaturkosten_dict.get(key, 0) for key in man_defekt_keys)
        max_ek = verkaufspreis - wunsch_marge - reparatur_summe
        pot_gewinn = verkaufspreis - reparatur_summe - anzeige["price"]

        # HTML Card bauen:
        st.markdown(f"""<div class="card">
            <h3>{anzeige['title']}</h3>
            <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a><br><br>
            <b>💰 Preis:</b> {anzeige['price']} €<br>
            <b>📉 Max. EK:</b> {max_ek:.2f} €<br>
            <b>📈 Gewinn:</b> {pot_gewinn:.2f} €<br>
            <b>🔧 Defekte:</b> {', '.join(man_defekt_keys) if man_defekt_keys else 'Keine'}<br>
            <b>🧾 Reparaturkosten:</b> {reparatur_summe} €
        </div>""", unsafe_allow_html=True)

        # Bildanzeige und Auswahlfelder trotzdem weiter in Streamlit
        if bilder:
            idx_key = f"img_idx_{anzeige['id']}"
            if idx_key not in st.session_state:
                st.session_state[idx_key] = 0
            col1, col2, col3 = st.columns([1, 6, 1])
            with col1:
                if st.button("←", key=f"prev_{anzeige['id']}"):
                    st.session_state[idx_key] = (st.session_state[idx_key] - 1) % len(bilder)
            with col2:
                show_image(bilder, st.session_state[idx_key])
                st.caption(f"Bild {st.session_state[idx_key]+1} von {len(bilder)}")
            with col3:
                if st.button("→", key=f"next_{anzeige['id']}"):
                    st.session_state[idx_key] = (st.session_state[idx_key] + 1) % len(bilder)

        defekte_select = st.multiselect(
            "🔧 Defekte wählen:", list(reparaturkosten_dict.keys()),
            default=man_defekt_keys, key=f"man_defekt_select_{anzeige['id']}"
        )

        col_save, col_archive = st.columns(2)
        with col_save:
            if st.button("📂 Speichern", key=f"save_{anzeige['id']}"):
                update_manual_defekt_keys(anzeige['id'], json.dumps(defekte_select))
                st.rerun()
        with col_archive:
            if st.button("🗃 Archivieren", key=f"archive_{anzeige['id']}"):
                archive_advert(anzeige['id'], True)
                st.success("Anzeige archiviert.")
                st.rerun()

        with st.expander("📄 Beschreibung"):
            st.markdown(anzeige["beschreibung"], unsafe_allow_html=True)

# Archiv-Seite (analog baubar)
elif seite == "📁 Archivierte Anzeigen":
    st.header("📁 Archivierte Anzeigen")
    st.info("Archivseite analog umbaubar – wir fokussieren uns erst auf die Live-Anzeigen.")
