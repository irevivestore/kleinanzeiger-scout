import streamlit as st
import json
import os
from datetime import datetime
from PIL import Image

# Page config
st.set_page_config(page_title="Kleinanzeigen-Scout", layout="wide")

# Farb- und Design-CSS
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            background-color: #F4F4F4 !important;
            font-family: 'Segoe UI', sans-serif;
        }
        .stButton>button {
            background-color: #4B6FFF;
            color: white;
            border-radius: 10px;
            padding: 0.5em 1em;
            border: none;
        }
        .stButton>button:hover {
            background-color: #00D1B2;
            color: white;
        }
        .card {
            background-color: white;
            border-radius: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            padding: 1rem;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# Datei-Pfade
DATEIPFAD = "anzeigen.json"
ARCHIV_PFAD = "archivierte_anzeigen.json"

# Hilfsfunktionen
def lade_anzeigen(dateipfad):
    if os.path.exists(dateipfad):
        with open(dateipfad, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def speichere_anzeigen(dateipfad, anzeigen):
    with open(dateipfad, "w", encoding="utf-8") as f:
        json.dump(anzeigen, f, indent=2, ensure_ascii=False)

def format_preis(preis):
    if isinstance(preis, list) and len(preis) == 2:
        return f"{preis[0]} € &nbsp;&nbsp;<s style='color:gray;'>{preis[1]} €</s>"
    return f"{preis} €"

def zeige_bilderkarussell(bilder_liste):
    if bilder_liste:
        index = st.slider("Bild auswählen", 0, len(bilder_liste)-1, 0, key=str(bilder_liste))
        st.image(bilder_liste[index], use_column_width=True)

# Seiten-Navigation
seite = st.sidebar.radio("Navigation", ["Aktive Anzeigen", "Archivierte Anzeigen"])

# Lade Daten
anzeigen = lade_anzeigen(DATEIPFAD)
archivierte = lade_anzeigen(ARCHIV_PFAD)

# Aktive Anzeigen anzeigen
if seite == "Aktive Anzeigen":
    st.title("📦 Aktive Anzeigen")

    if not anzeigen:
        st.info("Noch keine Anzeigen gefunden.")
    else:
        for i, anzeige in enumerate(anzeigen):
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)

                cols = st.columns([1, 3, 1])
                with cols[0]:
                    st.image(anzeige.get("vorschaubild"), use_column_width=True)

                with cols[1]:
                    st.subheader(anzeige.get("titel", "Unbekannter Titel"))
                    st.markdown(format_preis(anzeige.get("preis")), unsafe_allow_html=True)
                    st.markdown(f"📍 {anzeige.get('standort')}")
                    st.markdown(f"🕒 Zuletzt aktualisiert: {anzeige.get('zeitstempel_letzte_aenderung')}")
                    with st.expander("📄 Beschreibung"):
                        st.markdown(anzeige.get("beschreibung", "_Keine Beschreibung verfügbar._"))

                with cols[2]:
                    if st.button("📁 Archivieren", key=f"archivieren_{i}"):
                        archivierte.append(anzeige)
                        anzeigen.pop(i)
                        speichere_anzeigen(DATEIPFAD, anzeigen)
                        speichere_anzeigen(ARCHIV_PFAD, archivierte)
                        st.success("Anzeige archiviert.")
                        st.experimental_rerun()

                st.markdown('</div>', unsafe_allow_html=True)

# Archivierte Anzeigen anzeigen
elif seite == "Archivierte Anzeigen":
    st.title("🗃️ Archivierte Anzeigen")

    if not archivierte:
        st.info("Keine archivierten Anzeigen vorhanden.")
    else:
        for i, anzeige in enumerate(archivierte):
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)

                st.subheader(anzeige.get("titel", "Unbekannter Titel"))
                st.markdown(format_preis(anzeige.get("preis")), unsafe_allow_html=True)
                st.markdown(f"📍 {anzeige.get('standort')}")
                st.markdown(f"🕒 Archiviert am: {anzeige.get('zeitstempel_erfassung')}")
                if anzeige.get("bilder_liste"):
                    zeige_bilderkarussell(anzeige["bilder_liste"])
                with st.expander("📄 Beschreibung"):
                    st.markdown(anzeige.get("beschreibung", "_Keine Beschreibung verfügbar._"))

                st.markdown('</div>', unsafe_allow_html=True)