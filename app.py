import streamlit as st
import sys
import json
from io import StringIO

from scraper import scrape_ads
from db import (
    get_all_active_adverts,
    get_archived_adverts_for_model,
    save_ads_to_db,
    update_ad_in_db,
    archive_ad
)
from config import (
    IPHONE_MODELLE,
    STANDARD_VERKAUFSPREIS,
    STANDARD_WUNSCH_MARGE,
    STANDARD_REPARATURKOSTEN
)

# Initiale App-Konfiguration
st.set_page_config(
    page_title="Kleinanzeigen Analyzer",
    page_icon="📱",
    layout="wide"
)

# Custom CSS für modernes Styling
st.markdown("""
    <style>
        .st-emotion-cache-zq5wmm, .st-emotion-cache-1avcm0n {
            padding-top: 2rem;
        }
        .ad-box {
            border: 1px solid #e0e0e0;
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #fafafa;
            margin-bottom: 1rem;
        }
        .ad-header {
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
        .ad-price {
            color: green;
            font-weight: bold;
            font-size: 1.1rem;
        }
        .archived-note {
            font-style: italic;
            color: gray;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("📱 Kleinanzeigen Analyzer")
seite = st.sidebar.radio("Navigation", ["Anzeigen", "Archiv"])

# Modell-Auswahl für beide Seiten
modell = st.sidebar.selectbox("Modell wählen", IPHONE_MODELLE)

# Session State initialisieren
if "ads" not in st.session_state:
    st.session_state.ads = get_all_active_adverts()

if seite == "Anzeigen":
    st.title("📋 Neue Anzeigen analysieren")

    # Formular zur Parameter-Eingabe
    with st.form("parameter_form", clear_on_submit=False):
        verkaufspreis = st.number_input("Ø Verkaufspreis (€)", value=STANDARD_VERKAUFSPREIS)
        wunsch_marge = st.number_input("Gewünschte Marge (€)", value=STANDARD_WUNSCH_MARGE)
        reparaturkosten = st.number_input("Ø Reparaturkosten (€)", value=STANDARD_REPARATURKOSTEN)
        debug = st.checkbox("Debug-Modus aktivieren", value=False)
        submitted = st.form_submit_button("🔍 Anzeigen analysieren")

    if submitted:
        try:
            neue_ads = scrape_ads(modell, verkaufspreis, wunsch_marge, reparaturkosten, debug)
            save_ads_to_db(neue_ads)
            st.session_state.ads = get_all_active_adverts()
            st.success(f"{len(neue_ads)} neue Anzeigen gespeichert.")
        except Exception as e:
            st.error(f"Fehler beim Scraping: {e}")

    st.subheader("🆕 Aktuelle Ergebnisse")

    if not st.session_state.ads:
        st.info("Keine Anzeigen gefunden. Bitte starte zuerst eine Analyse.")
    else:
        for ad in st.session_state.ads:
            if ad.get("archiviert") or ad.get("modell") != modell:
                continue

            with st.container():
                st.markdown(f"<div class='ad-box'>", unsafe_allow_html=True)

                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"<div class='ad-header'>{ad['titel']}</div>", unsafe_allow_html=True)
                    st.markdown(f"[🔗 Zur Anzeige]({ad['url']})")
                    with st.expander("📄 Beschreibung anzeigen"):
                        st.write(ad.get("beschreibung", "Keine Beschreibung verfügbar."))

                with cols[1]:
                    st.markdown(f"<div class='ad-price'>{ad['preis_anzeige']}</div>", unsafe_allow_html=True)
                    st.write(f"Gesamtbewertung: **{ad['bewertung']}**")
                    st.write(f"Erfasst am: {ad['erfasst_am']}")
                    st.write(f"Zuletzt geändert: {ad['geaendert_am']}")

                    # Bewertungskriterien
                    defektauswahl = {
                        "display_defekt": "Display defekt",
                        "akku_defekt": "Akku defekt",
                        "face_id_defekt": "Face ID defekt",
                        "gehäuse_beschädigt": "Gehäuse beschädigt"
                    }
                    for key, label in defektauswahl.items():
                        new_value = st.checkbox(label, value=ad.get(key, False), key=f"{ad['id']}_{key}")
                        if new_value != ad.get(key, False):
                            ad[key] = new_value
                            update_ad_in_db(ad)

                    if st.button("🗂️ Archivieren", key=f"archivieren_{ad['id']}"):
                        archive_ad(ad["id"])
                        st.session_state.ads = get_all_active_adverts()
                        st.experimental_rerun()

                st.markdown("</div>", unsafe_allow_html=True)

elif seite == "Archiv":
    st.title("📦 Archivierte Anzeigen")

    archivierte_ads = get_archived_adverts_for_model(modell)

    if not archivierte_ads:
        st.info("Es sind keine archivierten Anzeigen vorhanden.")
    else:
        for ad in archivierte_ads:
            st.markdown(f"<div class='ad-box'>", unsafe_allow_html=True)

            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"<div class='ad-header'>{ad['titel']}</div>", unsafe_allow_html=True)
                st.markdown(f"[🔗 Zur Anzeige]({ad['url']})")
                with st.expander("📄 Beschreibung anzeigen"):
                    st.write(ad.get("beschreibung", "Keine Beschreibung verfügbar."))

            with cols[1]:
                st.markdown(f"<div class='ad-price'>{ad['preis_anzeige']}</div>", unsafe_allow_html=True)
                st.write(f"Gesamtbewertung: **{ad['bewertung']}**")
                st.write(f"Erfasst am: {ad['erfasst_am']}")
                st.write(f"Archiviert: ✅")

            st.markdown("</div>", unsafe_allow_html=True)
