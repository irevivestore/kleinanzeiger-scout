import streamlit as st
import json
from datetime import datetime
import os

# -------------------------------
# Design: Custom CSS
# -------------------------------
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")

st.markdown("""
    <style>
        body {
            background-color: #F4F4F4;
        }
        .main {
            background-color: #F4F4F4;
        }
        .stButton > button {
            background-color: #4B6FFF;
            color: white;
            border-radius: 10px;
            padding: 8px 16px;
            border: none;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        .stButton > button:hover {
            background-color: #3b5de8;
        }
        .card {
            background-color: white;
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            margin-bottom: 16px;
        }
        .tag {
            background-color: #00D1B2;
            color: white;
            font-size: 0.8rem;
            padding: 2px 10px;
            border-radius: 8px;
            display: inline-block;
            margin-right: 5px;
        }
        .price {
            font-weight: 700;
            color: #4B6FFF;
            font-size: 1.2rem;
        }
        .durchgestrichen {
            text-decoration: line-through;
            color: #999;
        }
        .image {
            border-radius: 12px;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Funktionen
# -------------------------------
def lade_anzeigen():
    if os.path.exists("anzeigen.json"):
        with open("anzeigen.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def lade_archiv():
    if os.path.exists("archiv.json"):
        with open("archiv.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def speichere_archivierte_ids(archiv):
    with open("archiv.json", "w", encoding="utf-8") as f:
        json.dump(archiv, f, ensure_ascii=False, indent=2)

# -------------------------------
# Seitenwahl
# -------------------------------
st.sidebar.title("📂 Navigation")
seite = st.sidebar.radio("Ansicht wählen:", ["📋 Aktive Anzeigen", "📦 Archiv"])

# -------------------------------
# Aktive Anzeigen
# -------------------------------
if seite == "📋 Aktive Anzeigen":
    st.title("📋 Aktive Anzeigen")
    daten = lade_anzeigen()
    archivierte_ids = [a["id"] for a in lade_archiv()]

    if not daten:
        st.info("Noch keine Anzeigen geladen.")
    else:
        for eintrag in daten:
            if eintrag["id"] in archivierte_ids:
                continue

            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                cols = st.columns([1, 2])

                # Bild
                with cols[0]:
                    if eintrag["bilder_liste"]:
                        st.image(eintrag["bilder_liste"][0], width=180, use_column_width="always")

                # Infos
                with cols[1]:
                    st.markdown(f"### {eintrag['titel']}")
                    st.markdown(f"<span class='price'>{eintrag['preis']}</span>", unsafe_allow_html=True)

                    if eintrag["beschreibung"]:
                        with st.expander("📄 Beschreibung anzeigen"):
                            st.markdown(eintrag["beschreibung"])

                    st.markdown(f"📍 {eintrag['ort']} &nbsp;&nbsp; 🕒 {eintrag['zeit_erfasst']}", unsafe_allow_html=True)
                    st.markdown(f"[🔗 Zur Anzeige]({eintrag['url']})", unsafe_allow_html=True)

                    if st.button(f"📦 Archivieren", key=f"archiv_{eintrag['id']}"):
                        archiv = lade_archiv()
                        archiv.append(eintrag)
                        speichere_archivierte_ids(archiv)
                        st.experimental_rerun()

                st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------
# Archivierte Anzeigen
# -------------------------------
if seite == "📦 Archiv":
    st.title("📦 Archivierte Anzeigen")
    archiv = lade_archiv()

    if not archiv:
        st.info("Keine Anzeigen archiviert.")
    else:
        for eintrag in archiv:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                cols = st.columns([1, 2])

                with cols[0]:
                    if eintrag["bilder_liste"]:
                        st.image(eintrag["bilder_liste"][0], width=180, use_column_width="always")

                with cols[1]:
                    st.markdown(f"### {eintrag['titel']}")
                    st.markdown(f"<span class='price'>{eintrag['preis']}</span>", unsafe_allow_html=True)

                    if eintrag["beschreibung"]:
                        with st.expander("📄 Beschreibung anzeigen"):
                            st.markdown(eintrag["beschreibung"])

                    st.markdown(f"📍 {eintrag['ort']} &nbsp;&nbsp; 🕒 {eintrag['zeit_erfasst']}", unsafe_allow_html=True)
                    st.markdown(f"[🔗 Zur Anzeige]({eintrag['url']})", unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)
