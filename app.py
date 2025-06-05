import streamlit as st
from scraper import scrape_ads
from db import (
    init_db, save_advert, get_all_adverts_for_model,
    load_config, save_config
)
from config import (
    REPARATURKOSTEN_DEFAULT,
    VERKAUFSPREIS_DEFAULT,
    WUNSCH_MARGE_DEFAULT
)

init_db()
st.set_page_config(page_title="📱 Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")

# 🧠 Modell-Einstellung
if "modell" not in st.session_state:
    st.session_state.modell = "iPhone 14 Pro"

modell = st.text_input("Modell auswählen", value=st.session_state.modell)
st.session_state.modell = modell

# 📦 Konfiguration laden oder neu anlegen
config = load_config(modell)
if config is None:
    config = {
        "verkaufspreis": VERKAUFSPREIS_DEFAULT,
        "wunsch_marge": WUNSCH_MARGE_DEFAULT,
        "reparaturkosten": REPARATURKOSTEN_DEFAULT.copy()
    }

# 🎛️ Erweiterte Einstellungen
with st.expander("⚙️ Erweiterte Bewertungsparameter"):
    verkaufspreis = st.number_input("🔼 Verkaufspreis (€)", min_value=0, value=config["verkaufspreis"], step=10)
    wunsch_marge = st.number_input("🎯 Wunschmarge (€)", min_value=0, value=config["wunsch_marge"], step=10)

    reparaturkosten_dict = {}
    for i, (defekt, kosten) in enumerate(config["reparaturkosten"].items()):
        neue_kosten = st.number_input(
            f"🛠 {defekt.capitalize()} (€)", min_value=0, value=kosten,
            step=10, key=f"rk_{i}"
        )
        reparaturkosten_dict[defekt] = neue_kosten

    if st.button("💾 Konfiguration speichern"):
        save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten_dict)
        st.success("✅ Konfiguration gespeichert")

# 📋 Suchparameter mit neuem Filter "Nur Angebote"
with st.form("filters"):
    col1, col2, col3, col4 = st.columns(4)
    min_preis = col1.number_input("💶 Mindestpreis", min_value=0, value=0)
    max_preis = col2.number_input("💶 Maximalpreis", min_value=0, value=1500)
    nur_versand = col3.checkbox("📦 Nur mit Versand")
    nur_angebote = col4.checkbox("📢 Nur Angebote", value=True)  # NEU
    submit = st.form_submit_button("🔎 Anzeigen durchsuchen")

# --- Debug-Log-Bereich vorbereiten ---
log_lines = []
log_area = st.empty()

def log(msg):
    log_lines.append(msg)
    log_area.text_area("🛠 Debug-Ausgaben", value="\n".join(log_lines[-50:]), height=300)

# 🔎 Suche starten mit Debug-Ausgabe
if submit:
    log_lines.clear()
    with st.spinner("Suche läuft..."):
        neue_anzeigen = scrape_ads(
            modell,
            min_price=min_preis,
            max_price=max_preis,
            nur_versand=nur_versand,
            nur_angebote=nur_angebote,  # NEU
            debug=True,
            config={
                "verkaufspreis": verkaufspreis,
                "wunsch_marge": wunsch_marge,
                "reparaturkosten": reparaturkosten_dict,
            },
            log=log
        )
    st.success(f"{len(neue_anzeigen)} Anzeigen geladen und gespeichert.")
    for anzeige in neue_anzeigen:
        save_advert(anzeige)

# 📄 Ergebnisse anzeigen
alle_anzeigen = get_all_adverts_for_model(modell)
if not alle_anzeigen:
    st.info("ℹ️ Noch keine Anzeigen gespeichert.")
else:
    st.success(f"📦 {len(alle_anzeigen)} gespeicherte Anzeigen")

    for idx, anzeige in enumerate(alle_anzeigen):
        reparatur_summe = anzeige.get("reparaturkosten", 0)
        max_ek = verkaufspreis - wunsch_marge - reparatur_summe

        farbe = (
            "#d4edda" if anzeige["price"] <= max_ek else
            "#d1ecf1" if anzeige["price"] <= max_ek + (wunsch_marge * 0.1) else
            "#f8d7da"
        )

        with st.container():
            st.markdown(f"""
            <div style='background-color: {farbe}; padding: 10px; border-radius: 5px;'>
            <div style='display: flex; gap: 20px;'>
                <div><img src="{anzeige['image']}" width="120"/></div>
                <div>
                    <h4>{anzeige['title']}</h4>
                    <b>Preis:</b> {anzeige['price']} €<br>
                    <b>Erfasst:</b> {anzeige['created_at']}<br>
                    <b>Letztes Update:</b> {anzeige['updated_at']}<br>
                    <b>Versand:</b> {'✅ Ja' if anzeige['versand'] else '❌ Nein'}<br>
                    <b>Reparaturkosten:</b> {reparatur_summe} €<br>
                    <b>Max. Einkaufspreis:</b> {max_ek:.2f} €<br>
                    <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Beschreibung anzeigen"):
                st.write(anzeige["beschreibung"])

            manuelle_defekte = st.multiselect(
                "⚠️ Manuelle Defekte markieren",
                options=list(reparaturkosten_dict.keys()),
                key=f"def_{idx}"
            )

            if manuelle_defekte:
                rep_summe = sum(reparaturkosten_dict[d] for d in manuelle_defekte)
                neuer_max_ek = verkaufspreis - wunsch_marge - rep_summe
                st.markdown(f"""
                    🧾 Reparaturkosten manuell: **{rep_summe} €**  
                    💰 Neuer max. Einkaufspreis: **{neuer_max_ek:.2f} €**
                """)

            st.divider()

st.caption("🔧 Hinweis: Kleinanzeigen werden lokal gespeichert. Konfiguration je Modell.")
