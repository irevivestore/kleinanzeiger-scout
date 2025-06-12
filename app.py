import streamlit as st
from scraper import scrape_ads
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
import sys
from io import StringIO
import json

# Initialize
init_db()
st.set_page_config(page_title="📱 Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")

# Setup enhanced logging
if 'log_buffer' not in st.session_state:
    st.session_state.log_buffer = StringIO()

if 'log_lines' not in st.session_state:
    st.session_state.log_lines = []

log_area = st.empty()

def log(message):
    print(message, file=sys.stderr)
    st.session_state.log_buffer.write(message + "\n")
    st.session_state.log_lines.append(message)
    log_area.text_area("🛠 Debug-Ausgaben", value="\n".join(st.session_state.log_lines[-50:]), height=300)

# Sidebar UI für Einstellungen
with st.sidebar:
    st.header("⚙️ Einstellungen")

    # Model selection
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
    modell = st.selectbox("Modell auswählen", IPHONE_MODELLE, index=IPHONE_MODELLE.index(st.session_state.modell))
    st.session_state.modell = modell

    # Config loading
    config = load_config(modell) or {
        "verkaufspreis": VERKAUFSPREIS_DEFAULT,
        "wunsch_marge": WUNSCH_MARGE_DEFAULT,
        "reparaturkosten": REPARATURKOSTEN_DEFAULT.copy()
    }

    verkaufspreis = st.number_input("🔼 Verkaufspreis (€)", min_value=0, value=config["verkaufspreis"], step=10)
    wunsch_marge = st.number_input("🎯 Wunschmarge (€)", min_value=0, value=config["wunsch_marge"], step=10)

    reparaturkosten_dict = {}
    for i, (defekt, kosten) in enumerate(config["reparaturkosten"].items()):
        reparaturkosten_dict[defekt] = st.number_input(
            f"🛠 {defekt.capitalize()} (€)", min_value=0, value=kosten, step=10, key=f"rk_{i}")

    if st.button("💾 Konfiguration speichern"):
        save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict)
        st.success("✅ Konfiguration gespeichert")

    # Search parameters
    with st.form("filters"):
        col1, col2 = st.columns(2)
        min_preis = col1.number_input("💶 Mindestpreis", min_value=0, value=0)
        max_preis = col2.number_input("💶 Maximalpreis", min_value=0, value=1500)
        nur_versand = st.checkbox("📦 Nur mit Versand")
        nur_angebote = st.checkbox("📢 Nur Angebote", value=True)
        submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

# Debug panel
with st.expander("📜 System Console Output"):
    st.code(st.session_state.log_buffer.getvalue())

# Suche durchführen
if submit:
    st.session_state.log_lines.clear()
    st.session_state.log_buffer.seek(0)
    st.session_state.log_buffer.truncate(0)

    with st.spinner("Suche läuft..."):
        neue_anzeigen = scrape_ads(
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

# Anzeigen darstellen
alle_anzeigen = get_all_adverts_for_model(modell)
archivierte_anzeigen = get_archived_adverts_for_model(modell)

st.subheader("📦 Gespeicherte Anzeigen")
if not alle_anzeigen:
    st.info("ℹ️ Keine gespeicherten Anzeigen verfügbar.")

for anzeige in alle_anzeigen:
    man_defekt_keys_raw = anzeige.get("man_defekt_keys")
    man_defekt_keys = []

    if man_defekt_keys_raw:
        if isinstance(man_defekt_keys_raw, list):
            man_defekt_keys = man_defekt_keys_raw
        elif isinstance(man_defekt_keys_raw, str):
            try:
                man_defekt_keys = json.loads(man_defekt_keys_raw)
                if not isinstance(man_defekt_keys, list):
                    log(f"⚠️ Unerwartetes Format: {man_defekt_keys}")
                    man_defekt_keys = []
            except Exception as e:
                log(f"❌ JSON Fehler: {e}")
                man_defekt_keys = []

    reparatur_summe = sum(reparaturkosten_dict.get(key, 0) for key in man_defekt_keys)
    max_ek = verkaufspreis - wunsch_marge - reparatur_summe

    with st.container():
        col1, col2, col3 = st.columns([1, 3, 2])
        with col1:
            st.image(anzeige['image'], width=120)
        with col2:
            st.markdown(f"### {anzeige['title']}")
            st.markdown(f"**💰 Preis:** {anzeige['price']} €")
            st.markdown(f"**🔍 Bewertung:** {anzeige.get('bewertung', '—')}")
            st.markdown(f"[🔗 Anzeige öffnen]({anzeige['link']})")
        with col3:
            st.markdown("**🛠 Berücksichtigte Defekte:**")
            st.markdown(", ".join(man_defekt_keys) if man_defekt_keys else "Keine")
            st.markdown(f"**🔧 Reparaturkosten:** {reparatur_summe} €")
            st.markdown(f"**💸 Max. Einkaufspreis:** {max_ek:.2f} €")

            alle_defekte = list(reparaturkosten_dict.keys())
            ausgewählte_defekte = st.multiselect(
                "🛠 Defekte wählen:",
                options=alle_defekte,
                default=man_defekt_keys,
                key=f"man_defekt_select_{anzeige['id']}"
            )

            if st.button(f"💾 Speichern", key=f"save_man_def_{anzeige['id']}"):
                update_manual_defekt_keys(anzeige["id"], json.dumps(ausgewählte_defekte))
                st.rerun()

            if st.button(f"🗃️ Archivieren", key=f"archive_{anzeige['id']}"):
                archive_advert(anzeige["id"])
                st.success("Anzeige archiviert.")
                st.rerun()

        with st.expander("📄 Beschreibung anzeigen"):
            st.write(anzeige['beschreibung'])

# Archivierte Anzeigen anzeigen
with st.expander("🗃️ Archivierte Anzeigen anzeigen"):
    for anzeige in archivierte_anzeigen:
        st.markdown(f"""
        <div style='background-color: #efefef; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
            <div style='display: flex; gap: 20px;'>
                <div><img src="{anzeige['image']}" width="100"/></div>
                <div>
                    <h5>{anzeige['title']}</h5>
                    <b>Preis:</b> {anzeige['price']} €<br>
                    <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
