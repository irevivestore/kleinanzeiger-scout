import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
from PIL import Image

# Design- und Farbdefinitionen
PRIMARY_COLOR = "#4B6FFF"      # Indigo
SECONDARY_COLOR = "#00D1B2"    # Türkis
BG_COLOR = "#F4F4F4"
CARD_BG_COLOR = "#FFFFFF"

st.set_page_config(page_title="Kleinanzeigen-Scout", layout="wide")
st.markdown(f"""
    <style>
        body {{ background-color: {BG_COLOR}; }}
        .card {{
            background-color: {CARD_BG_COLOR};
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
        }}
        .img-thumb {{
            border-radius: 0.5rem;
            max-height: 200px;
        }}
        .stButton>button {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-weight: bold;
        }}
        .stButton>button:hover {{
            background-color: {SECONDARY_COLOR};
        }}
    </style>
""", unsafe_allow_html=True)

# Sidebar mit Einstellungen
st.sidebar.header("🔧 Einstellungen")
verkaufspreis = st.sidebar.number_input("Ø Verkaufspreis (€)", min_value=0, value=400)
wunsch_marge = st.sidebar.number_input("Zielmarge (€)", min_value=0, value=80)
reparaturkosten = st.sidebar.number_input("Ø Reparaturkosten (€)", min_value=0, value=40)

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("📥 Gespeicherte Anzeigen laden (JSON)", type="json")

if uploaded_file:
    daten = json.load(uploaded_file)
    df = pd.DataFrame(daten)
    st.session_state.df = df
    st.sidebar.success("Anzeigen geladen!")

if st.sidebar.button("💾 Daten exportieren"):
    if "df" in st.session_state:
        st.sidebar.download_button("📤 Jetzt herunterladen", data=json.dumps(st.session_state.df.to_dict(orient="records")), file_name="anzeigen.json")
    else:
        st.sidebar.warning("Keine Daten zum Exportieren.")

if st.sidebar.button("🔄 Filter zurücksetzen"):
    for key in ["defekt_display", "bewertungen", "archiv"]:
        if key in st.session_state:
            del st.session_state[key]
    st.sidebar.success("Filter zurückgesetzt")

st.title("📱 Kleinanzeigen-Scout")

# Anzeigen laden
if "df" not in st.session_state:
    st.info("Bitte lade zunächst eine JSON-Datei mit Anzeigen hoch.")
    st.stop()

# Hilfsfunktionen

def bewertung_berechnen(row):
    abschlag = 0
    if row.get("defekt_display") == "Defekt":
        abschlag += reparaturkosten
    einkaufspreis = verkaufspreis - wunsch_marge - abschlag
    return max(0, einkaufspreis)

# Bewertung anwenden
st.session_state.df["einkaufspreis"] = st.session_state.df.apply(bewertung_berechnen, axis=1)

# Filterung archivierter Anzeigen
archivierte_ids = st.session_state.get("archiv", [])
df_aktiv = st.session_state.df[~st.session_state.df["id"].isin(archivierte_ids)]

# Anzeige der Ergebnisse
for idx, row in df_aktiv.iterrows():
    with st.container():
        cols = st.columns([1, 2])

        # Bild
        with cols[0]:
            if row.get("bilder_liste"):
                bild_url = row["bilder_liste"][0]
                st.image(bild_url, use_column_width=True)

        # Anzeige-Infos
        with cols[1]:
            st.markdown(f"### {row.get('titel', 'Unbekannter Titel')}")
            st.markdown(f"**Preis:** {row.get('preis_anzeige', 'k.A.')}  ")
            st.markdown(f"**Berechneter Einkaufspreis:** {row['einkaufspreis']} €")
            st.markdown(f"**Ort:** {row.get('ort', 'k.A.')}  ")
            st.markdown(f"**Erfasst:** {row.get('erfasst_am', '')}  ")
            st.markdown(f"**Zuletzt aktualisiert:** {row.get('geaendert_am', '')}")

            # Beschreibung einklappbar
            with st.expander("📄 Beschreibung anzeigen"):
                st.markdown(row.get("beschreibung", "Keine Beschreibung vorhanden."))

            # Manuelle Bewertung
            defekt_status = st.selectbox(
                f"Defekt-Status für Anzeige {row['id']}",
                ["Unbekannt", "Defekt", "In Ordnung"],
                key=f"defekt_{row['id']}"
            )
            st.session_state.df.loc[idx, "defekt_display"] = defekt_status
            st.session_state.df.loc[idx, "einkaufspreis"] = bewertung_berechnen(row)

            # Archivieren
            if st.button("📦 Archivieren", key=f"archiv_{row['id']}"):
                archiv = st.session_state.get("archiv", [])
                archiv.append(row['id'])
                st.session_state["archiv"] = archiv
                st.experimental_rerun()

st.markdown("---")
st.subheader("📂 Archivierte Anzeigen")

archiv_df = st.session_state.df[st.session_state.df["id"].isin(archivierte_ids)]

if archiv_df.empty:
    st.info("Noch keine Anzeigen archiviert.")
else:
    for idx, row in archiv_df.iterrows():
        with st.container():
            cols = st.columns([1, 2])
            with cols[0]:
                if row.get("bilder_liste"):
                    st.image(row["bilder_liste"][0], use_column_width=True)
            with cols[1]:
                st.markdown(f"**{row.get('titel', 'Unbekannt')}**  ")
                st.markdown(f"Preis: {row.get('preis_anzeige', 'k.A.')}  ")
                st.markdown(f"Berechneter Einkaufspreis: {row['einkaufspreis']} €")
                st.markdown(f"Erfasst: {row.get('erfasst_am', '')} | Aktualisiert: {row.get('geaendert_am', '')}")
