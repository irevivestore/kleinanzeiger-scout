import streamlit as st
import pandas as pd

# Demo-Datenstruktur für Kleinanzeigen-Ergebnisse (wird durch echten Scraper ersetzt)
demo_data = [
    {
        "titel": "iPhone 14 Pro - Display kaputt",
        "beschreibung": "Das Display ist gesprungen, sonst funktioniert alles.",
        "preis": 280,
        "link": "https://www.kleinanzeigen.de/s-anzeige/iphone-14-pro-display-kaputt/1234567890",
        "thumbnail": "https://via.placeholder.com/150"
    },
    {
        "titel": "iPhone 14 Pro mit Face ID Fehler",
        "beschreibung": "Face ID funktioniert nicht. Versand möglich.",
        "preis": 310,
        "link": "https://www.kleinanzeigen.de/s-anzeige/iphone-14-pro-face-id-defekt/0987654321",
        "thumbnail": "https://via.placeholder.com/150"
    },
]

# Funktion zum Abrufen der Anzeigen (Platzhalter für echten Scraper)
@st.cache_data
def fetch_anzeigen(modell, preis_min, preis_max):
    # Später hier Playwright- oder API-Logik einfügen
    return demo_data

# Streamlit App-Konfiguration
st.set_page_config(page_title="Kleinanzeigen Analyzer", layout="wide")
st.title("📱 Kleinanzeigen Analyzer – iPhone-Angebotsbewertung")

# Sidebar für Parameter
st.sidebar.header("🔧 Einstellungen")
modell = st.sidebar.selectbox(
    "Wähle Modell", ["iPhone 14 Pro", "iPhone 14", "iPhone 13 Pro", "iPhone 13"]
)
preis_min = st.sidebar.number_input(
    "Min. Preis (€)", min_value=0, max_value=5000, value=100, step=10
)
preis_max = st.sidebar.number_input(
    "Max. Preis (€)", min_value=0, max_value=5000, value=300, step=10
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Reparaturkosten (€)")

defekte_kosten = {
    "display": 80,
    "akku": 30,
    "backcover": 60,
    "kamera": 100,
    "lautsprecher": 60,
    "mikrofon": 50,
    "face id": 80,
    "wasserschaden": 250,
    "kein bild": 80,
    "defekt": 0,
}

verkaufspreis = 500
wunsch_marge = 120

# Button zum Abrufen der Anzeigen
if 'anzeigen' not in st.session_state:
    st.session_state.anzeigen = []

if st.sidebar.button("🔍 Anzeigen abrufen"):
    st.session_state.anzeigen = fetch_anzeigen(modell, preis_min, preis_max)

# Hauptbereich: Ergebnisse
st.markdown("## Analyse-Ergebnisse")
if not st.session_state.anzeigen:
    st.info("Klicke in der Seitenleiste auf 'Anzeigen abrufen', um die Angebote zu laden.")
else:
    for idx, anzeige in enumerate(st.session_state.anzeigen):
        # Bewertung berechnen
        gesamt_reparatur = sum(defekte_kosten.get(d, 0) for d in st.session_state.get(f"defekte_{idx}", []))
        maximaler_einkauf = verkaufspreis - wunsch_marge - gesamt_reparatur
        empfehlung = anzeige['preis'] <= maximaler_einkauf
        # Farbcode
        bg_color = '#e6ffed' if empfehlung else '#ffe6e6'
        border_color = '#00b33c' if empfehlung else '#ff3333'

        # Anzeige-Container mit Hintergrundfarbe und Thumbnail
        st.markdown(
            f"<div style='background-color:{bg_color}; padding:15px; margin-bottom:10px; border:2px solid {border_color}; border-radius:10px; display:flex;'>"
            f"<img src='{anzeige['thumbnail']}' style='width:120px; height:auto; margin-right:15px; border-radius:5px;'/>"
            f"<div>"
            f"<h4>{anzeige['titel']} - {anzeige['preis']} €</h4>"
            f"<p><a href='{anzeige['link']}' target='_blank'>Zur Anzeige</a></p>"
            f"<p>{anzeige['beschreibung']}</p>"
            f"<p><strong>Max. Einkaufspreis:</strong> {maximaler_einkauf:.2f} €</p>"
            f"<p><strong>Empfehlung:</strong> {'✅ Kauf möglich' if empfehlung else '❌ Zu teuer'}</p>"
            f"</div></div>", unsafe_allow_html=True
        )
        # Multiselect für Defekte
        defekte = st.multiselect(
            "Defekte auswählen:", list(defekte_kosten.keys()), key=f"defekte_{idx}"   
        )

        # Nach Auswahl neu berechnen und anzeigen
        if st.session_state.get(f"defekte_{idx}"):
            gesamt_reparatur = sum(defekte_kosten[d] for d in defekte)
            maximaler_einkauf = verkaufspreis - wunsch_marge - gesamt_reparatur
            st.write(f"Aktualisiert - Max. Einkaufspreis: {maximaler_einkauf:.2f} €")
