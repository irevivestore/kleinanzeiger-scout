import streamlit as st
from scraper import scrape_ads
from db import init_db, save_advert, get_existing_advert, load_config, save_config
from config import REPARATURKOSTEN_DEFAULT, VERKAUFSPREIS_DEFAULT, WUNSCH_MARGE_DEFAULT
from datetime import datetime

st.set_page_config(page_title="📱 Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")
st.markdown("Durchsuche und bewerte Anzeigen nach individuellen Kriterien")

# Initialisiere Datenbank
init_db()

# Modell definieren (wird gebraucht für configs)
if "modell" not in st.session_state:
    st.session_state.modell = "iPhone 14 Pro"

modell = st.text_input("Gerätemodell", value=st.session_state.modell)
st.session_state.modell = modell

# Lade Konfiguration für Modell
if "config" not in st.session_state:
    config = load_config(modell)
    if config is None:
        config = {
            "verkaufspreis": VERKAUFSPREIS_DEFAULT,
            "wunsch_marge": WUNSCH_MARGE_DEFAULT,
            "reparaturkosten": REPARATURKOSTEN_DEFAULT.copy()
        }
    st.session_state.config = config

config = st.session_state.config

# Konfiguration anzeigen (optional ausklappbar)
with st.expander("⚙️ Konfiguration anpassen", expanded=False):
    config["verkaufspreis"] = st.number_input("📦 Verkaufspreis (€)", value=config["verkaufspreis"], min_value=0)
    config["wunsch_marge"] = st.number_input("💰 Wunsch-Marge (€)", value=config["wunsch_marge"], min_value=0)

    st.markdown("### 🔧 Reparaturkosten je Defekt")
    for i, (defekt, kosten) in enumerate(config["reparaturkosten"].items()):
        neue_kosten = st.number_input(f"{defekt.capitalize()} (€)", value=kosten, key=f"defekt_input_{i}")
        config["reparaturkosten"][defekt] = neue_kosten

    if st.button("💾 Konfiguration speichern"):
        save_config(modell, config["verkaufspreis"], config["wunsch_marge"], config["reparaturkosten"])
        st.success("Konfiguration gespeichert.")

# Suchfilter
with st.form("filters"):
    col1, col2 = st.columns(2)
    min_preis = col1.number_input("💶 Mindestpreis", min_value=0, value=0)
    max_preis = col2.number_input("💶 Maximalpreis", min_value=0, value=1000)
    nur_versand = st.checkbox("📦 Nur mit Versand")
    debug = st.checkbox("🐞 Debug-Modus")
    submit = st.form_submit_button("🔍 Anzeigen durchsuchen")

if submit:
    with st.spinner("🔍 Suche läuft..."):
        neue_anzeigen = scrape_ads(modell, min_preis, max_preis, nur_versand, debug, config)
        st.session_state.anzeigen = []

        for anzeige in neue_anzeigen:
            gespeicherte = get_existing_advert(anzeige["id"])
            jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if gespeicherte:
                anzeige["erstellt"] = gespeicherte["erstellt"]
                anzeige["aktualisiert"] = jetzt if anzeige["price"] != gespeicherte["price"] else gespeicherte["aktualisiert"]
            else:
                anzeige["erstellt"] = jetzt
                anzeige["aktualisiert"] = jetzt

            save_advert(anzeige)
            st.session_state.anzeigen.append(anzeige)

# Ergebnisanzeige
if "anzeigen" in st.session_state and st.session_state.anzeigen:
    for idx, anzeige in enumerate(st.session_state.anzeigen):
        farbe = {"gruen": "#d4edda", "blau": "#d1ecf1", "rot": "#f8d7da"}.get(anzeige["bewertung"], "#ffffff")

        with st.container():
            st.markdown(f"""
                <div style='background-color: {farbe}; padding: 10px; border-radius: 5px;'>
                    <div style='display: flex; gap: 20px;'>
                        <div><img src="{anzeige['image']}" width="120"/></div>
                        <div>
                            <h4>{anzeige['title']}</h4>
                            <b>Preis:</b> {anzeige['price']} €<br>
                            <b>Max. Einkaufspreis:</b> {anzeige['max_ek']:.2f} €<br>
                            <b>Reparaturkosten:</b> {anzeige['reparaturkosten']} €<br>
                            <b>Versand:</b> {'✅ Ja' if anzeige['versand'] else '❌ Nein'}<br>
                            <b>Erstellt:</b> {anzeige['erstellt']}<br>
                            <b>Letztes Update:</b> {anzeige['aktualisiert']}<br>
                            <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Beschreibung anzeigen"):
                st.write(anzeige["beschreibung"])

            manuelle_defekte = st.multiselect("🛠️ Manuelle Defekte", options=list(config["reparaturkosten"].keys()), key=f"def_{idx}")
            if manuelle_defekte:
                neue_reparatur = sum(config["reparaturkosten"][d] for d in manuelle_defekte)
                neue_max_ek = config["verkaufspreis"] - neue_reparatur - config["wunsch_marge"]
                neue_bewertung = (
                    "gruen" if anzeige['price'] <= neue_max_ek else
                    "blau" if anzeige['price'] <= config["verkaufspreis"] - neue_reparatur - (config["wunsch_marge"] * 0.9) else
                    "rot"
                )
                st.markdown(f"🧾 Neue Reparaturkosten: **{neue_reparatur} €**")
                st.markdown(f"💰 Neuer max. Einkaufspreis: **{neue_max_ek:.2f} €**")
                st.markdown(f"🎯 Neue Bewertung: **{neue_bewertung.upper()}**")

            st.divider()

st.caption("ℹ️ Alle Daten stammen aus öffentlich verfügbaren Anzeigen auf kleinanzeigen.de")
