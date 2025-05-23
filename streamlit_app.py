
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
import streamlit as st
import pandas as pd

# Beispiel-Datenstruktur für Kleinanzeigen-Ergebnisse
demo_data = [
    {
        "titel": "iPhone 14 Pro - Display kaputt",
        "beschreibung": "Das Display ist gesprungen, sonst funktioniert alles.",
        "preis": 280,
        "link": "https://www.kleinanzeigen.de/s-anzeige/iphone-14-pro-display-kaputt/1234567890"
    },
    {
        "titel": "iPhone 14 Pro mit Face ID Fehler",
        "beschreibung": "Face ID funktioniert nicht. Versand möglich.",
        "preis": 310,
        "link": "https://www.kleinanzeigen.de/s-anzeige/iphone-14-pro-face-id-defekt/0987654321"
    },
]

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

st.set_page_config(page_title="Kleinanzeigen Analyzer", layout="wide")
st.title("📱 Kleinanzeigen Analyzer – iPhone-Angebotsbewertung")

if "anzeigen" not in st.session_state:
    st.session_state.anzeigen = demo_data

st.markdown("Wähle für jede Anzeige aus, welche Defekte vorhanden sind. Die Bewertung wird automatisch neu berechnet.")

for idx, anzeige in enumerate(st.session_state.anzeigen):
    with st.expander(f"{anzeige['titel']} – {anzeige['preis']} €"):
        st.markdown(f"**Link:** [Anzeigenlink]({anzeige['link']})")
        st.markdown(f"**Beschreibung:** {anzeige['beschreibung']}")

        defektauswahl = st.multiselect(
            f"Defekte für Anzeige {idx + 1} auswählen:",
            options=list(defekte_kosten.keys()),
            key=f"defekte_{idx}"
        )

        gesamt_reparatur = sum(defekte_kosten[d] for d in defektauswahl)
        maximaler_einkaufspreis = verkaufspreis - wunsch_marge - gesamt_reparatur

        farbe = "green" if anzeige['preis'] <= maximaler_einkaufspreis else "red"

        st.markdown(
            f"**Reparaturkosten:** {gesamt_reparatur} €  <br>"
            f"**Max. Einkaufspreis:** <span style='color:{farbe}'>{maximaler_einkaufspreis:.2f} €</span>",
            unsafe_allow_html=True
        )

        if anzeige['preis'] <= maximaler_einkaufspreis:
            st.success("Diese Anzeige erfüllt deine Preis-/Margenvorgaben.")
        else:
            st.warning("Preis zu hoch für gewünschte Marge.")
