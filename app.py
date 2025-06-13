import streamlit as st
import json
import os
from datetime import datetime
from PIL import Image

# ---------- Seiteneinstellungen ----------
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")

# ---------- Modernes UI-Design einbinden ----------
st.markdown("""
    <style>
        /* Hintergrund */
        .main {
            background-color: #F4F4F4;
        }

        /* Karten-Design */
        div[data-testid="stVerticalBlock"] > div:has(div[data-testid="column"]) {
            background-color: white;
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
        }

        /* Buttons */
        .stButton > button {
            background-color: #4B6FFF;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
        }
        .stButton > button:hover {
            background-color: #3757f5;
            color: white;
        }

        /* Inputs */
        .stNumberInput input {
            border-radius: 8px;
        }

        /* Schrift */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Segoe UI', sans-serif;
        }
        body {
            font-family: 'Segoe UI', sans-serif;
        }

        /* Expander Style */
        details > summary {
            font-weight: bold;
        }

        /* MultiSelect */
        div[data-baseweb="select"] > div {
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Daten laden ----------
def lade_anzeigen(pfad):
    if os.path.exists(pfad):
        with open(pfad, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def speichere_anzeigen(pfad, daten):
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=2, ensure_ascii=False)

# ---------- Bildanzeige ----------
def zeige_bilder(bilder_liste):
    if bilder_liste:
        idx = st.session_state.get("bild_index", 0)
        col1, col2 = st.columns([4, 1])
        with col1:
            st.image(bilder_liste[idx], use_column_width=True)
        with col2:
            if st.button("◀", key=f"prev_{bilder_liste[0]}", help="Zurück"):
                idx = (idx - 1) % len(bilder_liste)
                st.session_state["bild_index"] = idx
            if st.button("▶", key=f"next_{bilder_liste[0]}", help="Weiter"):
                idx = (idx + 1) % len(bilder_liste)
                st.session_state["bild_index"] = idx

# ---------- Hauptinhalt ----------
st.title("📱 Kleinanzeigen Scout")

anzeigen_pfad = "daten/anzeigen.json"
archiv_pfad = "daten/archivierte_anzeigen.json"
anzeigen = lade_anzeigen(anzeigen_pfad)
archivierte = lade_anzeigen(archiv_pfad)

tab1, tab2 = st.tabs(["🔍 Aktuelle Anzeigen", "🗃️ Archivierte Anzeigen"])

with tab1:
    if not anzeigen:
        st.info("Keine aktuellen Anzeigen gefunden.")
    else:
        for i, eintrag in enumerate(anzeigen):
            with st.container():
                st.markdown(f"### {eintrag.get('titel', 'Unbekannter Titel')}")
                st.markdown(f"**Preis:** {eintrag.get('preis_anzeige', '')}")
                st.markdown(f"**Bewertung:** {eintrag.get('bewertung', '')}")
                st.markdown(f"**Link:** [Anzeigenlink]({eintrag.get('url', '')})")

                with st.expander("📄 Beschreibung"):
                    st.markdown(eintrag.get("beschreibung", ""))

                if "bilder_liste" in eintrag and eintrag["bilder_liste"]:
                    zeige_bilder(eintrag["bilder_liste"])

                st.markdown(f"*Erfasst: {eintrag.get('zeit_erfasst', '')} | Zuletzt geändert: {eintrag.get('zeit_aktualisiert', '')}*")

                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("Archivieren", key=f"archiv_{i}"):
                        archivierte.append(eintrag)
                        del anzeigen[i]
                        speichere_anzeigen(anzeigen_pfad, anzeigen)
                        speichere_anzeigen(archiv_pfad, archivierte)
                        st.success("Anzeige archiviert.")
                        st.experimental_rerun()

with tab2:
    if not archivierte:
        st.info("Keine archivierten Anzeigen.")
    else:
        for eintrag in archivierte:
            with st.container():
                st.markdown(f"### {eintrag.get('titel', 'Unbekannter Titel')}")
                st.markdown(f"**Preis:** {eintrag.get('preis_anzeige', '')}")
                st.markdown(f"**Bewertung:** {eintrag.get('bewertung', '')}")
                st.markdown(f"**Link:** [Anzeigenlink]({eintrag.get('url', '')})")

                with st.expander("📄 Beschreibung"):
                    st.markdown(eintrag.get("beschreibung", ""))

                if "bilder_liste" in eintrag and eintrag["bilder_liste"]:
                    zeige_bilder(eintrag["bilder_liste"])

                st.markdown(f"*Erfasst: {eintrag.get('zeit_erfasst', '')} | Zuletzt geändert: {eintrag.get('zeit_aktualisiert', '')}*")
