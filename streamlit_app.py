
import streamlit as st

# Titel der App
st.title("📱 iPhone Kleinanzeigen Analyzer")

# Seitenleiste für Einstellungen
st.sidebar.header("🔧 Einstellungen")

# Modellauswahl
modell = st.sidebar.selectbox(
    "Wähle ein iPhone Modell:",
    ["iPhone 14 Pro", "iPhone 14", "iPhone 13 Pro", "iPhone 13"]
)

# Preisparameter
verkaufspreis = st.sidebar.number_input("Verkaufspreis (€)", min_value=100, max_value=2000, value=500, step=10)
wunsch_marge = st.sidebar.number_input("Gewünschte Marge (€)", min_value=0, max_value=1000, value=120, step=10)

st.sidebar.markdown("---")
st.sidebar.subheader("Reparaturkosten (€)")

# Reparaturkosten für typische Defekte
reparaturkosten = {
    "display": st.sidebar.number_input("Display", 0, 500, 80, 10),
    "akku": st.sidebar.number_input("Akku", 0, 200, 30, 5),
    "backcover": st.sidebar.number_input("Backcover", 0, 300, 60, 10),
    "kamera": st.sidebar.number_input("Kamera", 0, 300, 100, 10),
    "lautsprecher": st.sidebar.number_input("Lautsprecher", 0, 200, 60, 10),
    "mikrofon": st.sidebar.number_input("Mikrofon", 0, 200, 50, 10),
    "face id": st.sidebar.number_input("Face ID", 0, 300, 80, 10),
    "wasserschaden": st.sidebar.number_input("Wasserschaden", 0, 500, 250, 10),
    "kein bild": st.sidebar.number_input("Kein Bild", 0, 300, 80, 10),
}

st.markdown("### 🔍 Analyse-Ergebnisse")
st.info("Bitte beachte: Die eigentliche Anzeigeanalyse und Websuche sind aktuell deaktiviert – KI-Funktionalität folgt!")

# Platzhalter für spätere Anzeigenergebnisse
st.write("Hier erscheinen später die analysierten Angebote mit Bewertung und Kaufempfehlung.")
