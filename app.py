import streamlit as st
from scraper import scrape_ads
from db import (
    init_db, save_advert, get_all_adverts_for_model,
    load_config, save_config, update_manual_defekt
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

def log(message):
    """Enhanced logging function"""
    print(message, file=sys.stderr)  # Goes to terminal
    st.session_state.log_buffer.write(message + "\n")
    st.session_state.log_lines.append(message)
    log_area.text_area("🛠 Debug-Ausgaben", 
                     value="\n".join(st.session_state.log_lines[-50:]), 
                     height=300)

# Session state setup
if 'log_lines' not in st.session_state:
    st.session_state.log_lines = []
log_area = st.empty()

# Model selection
if "modell" not in st.session_state:
    st.session_state.modell = "iPhone 14 Pro"
modell = st.text_input("Modell auswählen", value=st.session_state.modell)
st.session_state.modell = modell

# Config loading
config = load_config(modell) or {
    "verkaufspreis": VERKAUFSPREIS_DEFAULT,
    "wunsch_marge": WUNSCH_MARGE_DEFAULT,
    "reparaturkosten": REPARATURKOSTEN_DEFAULT.copy()
}

# Configuration UI
with st.expander("⚙️ Erweiterte Bewertungsparameter"):
    verkaufspreis = st.number_input("🔼 Verkaufspreis (€)", 
                                  min_value=0, 
                                  value=config["verkaufspreis"], 
                                  step=10)
    wunsch_marge = st.number_input("🎯 Wunschmarge (€)", 
                                  min_value=0, 
                                  value=config["wunsch_marge"], 
                                  step=10)

    reparaturkosten_dict = {}
    for i, (defekt, kosten) in enumerate(config["reparaturkosten"].items()):
        reparaturkosten_dict[defekt] = st.number_input(
            f"🛠 {defekt.capitalize()} (€)", 
            min_value=0, 
            value=kosten,
            step=10, 
            key=f"rk_{i}"
        )

    if st.button("💾 Konfiguration speichern"):
        save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict)
        st.success("✅ Konfiguration gespeichert")

# Search parameters
with st.form("filters"):
    col1, col2, col3, col4 = st.columns(4)
    min_preis = col1.number_input("💶 Mindestpreis", min_value=0, value=0)
    max_preis = col2.number_input("💶 Maximalpreis", min_value=0, value=1500)
    nur_versand = col3.checkbox("📦 Nur mit Versand")
    nur_angebote = col4.checkbox("📢 Nur Angebote", value=True)
    submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

# Debug panel
with st.expander("📜 System Console Output"):
    st.code(st.session_state.log_buffer.getvalue())

# Main search logic
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
        st.success(f"{len(neue_anzeigen)} Anzeigen geladen und gespeichert.")
        for anzeige in neue_anzeigen:
            save_advert(anzeige)
    else:
        st.warning("Keine Anzeigen gefunden oder gespeichert.")

# Display results
alle_anzeigen = get_all_adverts_for_model(modell)
if not alle_anzeigen:
    st.info("ℹ️ Noch keine Anzeigen gespeichert.")
else:
    st.success(f"📦 {len(alle_anzeigen)} gespeicherte Anzeigen")
    
    for idx, anzeige in enumerate(alle_anzeigen):
        reparatur_summe = anzeige.get("reparaturkosten", 0)
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

            with st.expander("📄 Beschreibung anzeigen"):
                st.write(anzeige['beschreibung'])

            with st.expander("🔍 Details anzeigen"):
                st.write(f"**Reparaturkosten:** {reparatur_summe} €")
                st.write(f"**Max. Einkaufspreis:** {max_ek:.2f} €")

                # Manuelle Defektparameter editierbar machen
                if anzeige.get("man_defekt"):
                    try:
                        man_defekt = json.loads(anzeige["man_defekt"])
                    except:
                        man_defekt = reparaturkosten_dict.copy()
                else:
                    man_defekt = reparaturkosten_dict.copy()

                st.markdown("### 🛠 Manuelle Defektparameter")
                for key, wert in man_defekt.items():
                    man_defekt[key] = st.number_input(
                        f"{key.capitalize()} (€)",
                        min_value=0,
                        value=wert,
                        step=10,
                        key=f"man_defekt_{anzeige['id']}_{key}"
                    )

                if st.button(f"💾 Speichern für Anzeige {anzeige['id']}", key=f"save_man_def_{anzeige['id']}"):
                    update_manual_defekt(anzeige["id"], json.dumps(man_defekt))
                    st.success("✅ Manuelle Defektparameter gespeichert!")
