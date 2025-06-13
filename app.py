import streamlit as st
from datetime import datetime

# App-Konfiguration
st.set_page_config(
    page_title="Kleinanzeigen-Scout",
    page_icon="📱",
    layout="wide"
)

# Navigation
st.sidebar.title("📱 Kleinanzeigen-Scout")
seite = st.sidebar.radio("Navigation", ["Aktive Anzeigen", "Archivierte Anzeigen"])

# Demo-Daten
anzeigen = [
    {
        "id": "1",
        "titel": "iPhone 14 Pro - Top Zustand",
        "preis": "450 €",
        "beschreibung": "Fast wie neu, mit Originalverpackung.",
        "bilder_liste": ["https://via.placeholder.com/200", "https://via.placeholder.com/200?text=Bild+2"],
        "zeit_erfasst": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "zeit_geändert": datetime.now().strftime("%d.%m.%Y %H:%M"),
    },
    {
        "id": "2",
        "titel": "iPhone 14 Pro mit Display-Schaden",
        "preis": "300 €",
        "beschreibung": "Riss im Display, sonst voll funktionsfähig.",
        "bilder_liste": ["https://via.placeholder.com/200?text=Bild+1"],
        "zeit_erfasst": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "zeit_geändert": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
]

# Anzeige-Funktion
def zeige_anzeige(anzeige):
    with st.container():
        cols = st.columns([1, 2])
        with cols[0]:
            st.image(anzeige["bilder_liste"][0], width=180)
        with cols[1]:
            st.markdown(f"### {anzeige['titel']}")
            st.markdown(f"**Preis:** {anzeige['preis']}")
            st.markdown(f"**Erfasst:** {anzeige['zeit_erfasst']}  \n**Letzte Änderung:** {anzeige['zeit_geändert']}")
            with st.expander("Beschreibung"):
                st.write(anzeige["beschreibung"])

            st.selectbox("Manuelle Bewertung", ["Noch nicht bewertet", "Defekt", "Interessant", "Ignorieren"], key=f"bewertung_{anzeige['id']}")
            st.button("Archivieren", key=f"archiv_{anzeige['id']}")

# Anzeige je nach Navigation
if seite == "Aktive Anzeigen":
    st.title("📢 Aktive Anzeigen")
    for anzeige in anzeigen:
        zeige_anzeige(anzeige)
        st.markdown("---")

elif seite == "Archivierte Anzeigen":
    st.title("📦 Archivierte Anzeigen")
    st.info("Hier werden später die archivierten Anzeigen angezeigt.")