import streamlit as st
from datetime import datetime

# Diese Zeile muss als ERSTE Streamlit-Zeile stehen!
st.set_page_config(page_title="📱 Kleinanzeigen Scout", layout="wide")

# Modernes Design: Farben, Card-Stil und Buttons
st.markdown("""
<style>
body {
    background-color: #F4F4F4;
    font-family: "Segoe UI", sans-serif;
}
.card {
    background-color: white;
    padding: 1.5rem;
    border-radius: 1.5rem;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    margin-bottom: 2rem;
}
.card-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #333;
    margin-bottom: 0.5rem;
}
.card-subtitle {
    font-size: 1rem;
    color: #666;
    margin-bottom: 1rem;
}
.primary-button {
    background-color: #4B6FFF;
    color: white;
    border: none;
    padding: 0.6rem 1.2rem;
    border-radius: 0.75rem;
    font-weight: bold;
    cursor: pointer;
    text-decoration: none;
}
.primary-button:hover {
    background-color: #3a56d6;
}
.price {
    font-size: 1.2rem;
    color: #00D1B2;
    font-weight: bold;
}
.timestamp {
    font-size: 0.85rem;
    color: #999;
}
</style>
""", unsafe_allow_html=True)

# Überschrift
st.title("📱 Kleinanzeigen Scout")

# Dummy-Daten als Platzhalter
anzeigen_liste = [
    {
        "titel": "iPhone 14 Pro 128 GB - Space Schwarz",
        "preis": "320 €",
        "beschreibung": "Display gesprungen, funktioniert aber einwandfrei. Versand möglich.",
        "zeitstempel": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "url": "https://example.com/anzeige1"
    },
    {
        "titel": "iPhone 14 Pro mit Wasserschaden",
        "preis": "280 €",
        "beschreibung": "Nach Wasserschaden startet nicht mehr. Für Bastler.",
        "zeitstempel": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "url": "https://example.com/anzeige2"
    }
]

# Anzeigen als Karten rendern
for anzeige in anzeigen_liste:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{anzeige['titel']}</div>
        <div class="price">{anzeige['preis']}</div>
        <div class="card-subtitle">{anzeige['beschreibung']}</div>
        <div class="timestamp">Letzte Änderung: {anzeige['zeitstempel']}</div>
        <a href="{anzeige['url']}" class="primary-button" target="_blank">Zur Anzeige</a>
    </div>
    """, unsafe_allow_html=True)
