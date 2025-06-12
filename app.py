import streamlit as st
from scraper import scrape_ads
from db import (
    init_db, save_advert, get_all_adverts_for_model,
    load_config, save_config, update_manual_defekt_keys
)
from config import (
    REPARATURKOSTEN_DEFAULT,
    VERKAUFSPREIS_DEFAULT,
    WUNSCH_MARGE_DEFAULT
)
import sys
from io import StringIO
import json

# Initialisierung
init_db()
st.set_page_config(page_title="📱 Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")

# Logging vorbereiten
if 'log_buffer' not in st.session_state:
    st.session_state.log_buffer = StringIO()

def log(message):
    """Logging mit Anzeige im Logbereich"""
    print(message, file=sys.stderr)
    st.session_state.log_buffer.write(message + "\n")
    st.session_state.log_lines.append(message)

# Session-State für Log-Zeilen
if 'log_lines' not in st.session_state:
    st.session_state.log_lines = []

# Seitenleiste
with st.sidebar:
    st.header("⚙️ Einstellungen")

    IPHONE_MODELLE = [
        "iPhone SE (2020)", "iPhone SE (2022)",
        "iPhone X", "iPhone XR", "iPhone XS", "iPhone XS Max",
        "iPhone 11", "iPhone 11 Pro", "iPhone 11 Pro Max",
        "iPhone 12", "iPhone 12 Mini", "iPhone 12 Pro", "iPhone 12 Pro Max",
        "iPhone 13", "iPhone 13 Mini", "iPhone 13 Pro", "iPhone 13 Pro Max",
        "iPhone 14", "iPhone 14 Plus", "iPhone 14 Pro", "iPhone 14 Pro Max",
        "iPhone 15", "iPhone 15 Plus", "iPhone 15 Pro", "iPhone 15 Pro Max"
    ]

    if "modell" not in st.session_state:
        st.session_state.modell = "iPhone 14 Pro"

    modell = st.selectbox("📱 Modell auswählen", options=IPHONE_MODELLE, index=IPHONE_MODELLE.index(st.session_state.modell))
    st.session_state.modell = modell

    config = load_config(modell) or {
        "verkaufspreis": VERKAUFSPREIS_DEFAULT,
        "wunsch_marge": WUNSCH_MARGE_DEFAULT,
        "reparaturkosten": REPARATURKOSTEN_DEFAULT.copy()
    }

    st.subheader("💶 Bewertungsparameter")
    verkaufspreis = st.number_input("Verkaufspreis (€)", min_value=0, value=config["verkaufspreis"], step=10)
    wunsch_marge = st.number_input("Wunschmarge (€)", min_value=0, value=config["wunsch_marge"], step=10)

    reparaturkosten_dict = {}
    for i, (defekt, kosten) in enumerate(config["reparaturkosten"].items()):
        reparaturkosten_dict[defekt] = st.number_input(
            f"🛠 {defekt.capitalize()} (€)", min_value=0, value=kosten, step=10, key=f"rk_{i}"
        )

    if st.button("💾 Konfiguration speichern"):
        save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict)
        st.success("✅ Konfiguration gespeichert")

    st.subheader("🔎 Filtersuche")
    with st.form("filters"):
        min_preis = st.number_input("Mindestpreis", min_value=0, value=0)
        max_preis = st.number_input("Maximalpreis", min_value=0, value=1500)
        nur_versand = st.checkbox("Nur mit Versand")
        nur_angebote = st.checkbox("Nur Angebote", value=True)
        submit = st.form_submit_button("🔍 Anzeigen durchsuchen")

# Suchvorgang starten
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

    if neue_anzeigen:
        st.success(f"{len(neue_anzeigen)} neue Anzeigen gefunden.")
        for anzeige in neue_anzeigen:
            save_advert(anzeige)
    else:
        st.warning("Keine neuen passenden Anzeigen gefunden.")

# Konfiguration erneut laden für Bewertung
config = load_config(modell) or {
    "verkaufspreis": VERKAUFSPREIS_DEFAULT,
    "wunsch_marge": WUNSCH_MARGE_DEFAULT,
    "reparaturkosten": REPARATURKOSTEN_DEFAULT.copy()
}
verkaufspreis = config["verkaufspreis"]
wunsch_marge = config["wunsch_marge"]
reparaturkosten_dict = config["reparaturkosten"]

# Anzeigen darstellen
alle_anzeigen = get_all_adverts_for_model(modell)
if not alle_anzeigen:
    st.info("ℹ️ Noch keine Anzeigen gespeichert.")
else:
    st.subheader(f"📦 {len(alle_anzeigen)} gespeicherte Anzeigen für {modell}")
    
    for anzeige in alle_anzeigen:
        # Fehlerrobuster Umgang mit gespeicherten Defekt-Daten
        man_defekt_keys_raw = anzeige.get("man_defekt_keys")
        man_defekt_keys = []

        if man_defekt_keys_raw:
            if isinstance(man_defekt_keys_raw, list):
                man_defekt_keys = man_defekt_keys_raw
            elif isinstance(man_defekt_keys_raw, str):
                try:
                    man_defekt_keys = json.loads(man_defekt_keys_raw)
                    if not isinstance(man_defekt_keys, list):
                        log(f"⚠️ Kein gültiges Defekt-Format (nicht Liste): {man_defekt_keys}")
                        man_defekt_keys = []
                except Exception as e:
                    log(f"❌ Fehler beim Parsen von man_defekt_keys: {e}")
                    man_defekt_keys = []

        # Bewertung berechnen
        reparatur_summe = sum(reparaturkosten_dict.get(key, 0) for key in man_defekt_keys)
        max_ek = verkaufspreis - wunsch_marge - reparatur_summe

        with st.container():
            st.markdown(f"""
            <div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                <div style='display: flex; gap: 20px;'>
                    <div><img src="{anzeige['image']}" width="120"/></div>
                    <div>
                        <h4>{anzeige['title']}</h4>
                        <b>Preis:</b> {anzeige['price']} €<br>
                        <b>Bewertung:</b> {anzeige.get("bewertung", "—")}<br>
                        <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Beschreibung"):
                st.write(anzeige['beschreibung'])

            with st.expander("🛠 Defekte & Bewertung"):
                st.write(f"**Ausgewählte Defekte:** {', '.join(man_defekt_keys) if man_defekt_keys else 'Keine'}")
                st.write(f"**Reparaturkosten:** {reparatur_summe} €")
                st.write(f"**Max. Einkaufspreis:** {max_ek:.2f} €")

                alle_defekte = list(reparaturkosten_dict.keys())
                ausgewählte_defekte = st.multiselect(
                    "Defekte auswählen:",
                    options=alle_defekte,
                    default=man_defekt_keys,
                    key=f"man_defekt_select_{anzeige['id']}"
                )

                if st.button(f"💾 Speichern für Anzeige {anzeige['id']}", key=f"save_man_def_{anzeige['id']}"):
                    update_manual_defekt_keys(anzeige["id"], json.dumps(ausgewählte_defekte))
                    st.rerun()

# Debug-Ausgaben anzeigen (in eigener Expander-Box)
with st.expander("🛠 Debug-Konsole"):
    st.text_area("Log-Ausgaben", value=st.session_state.log_buffer.getvalue(), height=300)
