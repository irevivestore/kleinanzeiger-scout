import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Titel der App
st.title("📱 Kleinanzeigen Scout")

# Seitenleiste für Eingaben
modell = st.sidebar.text_input("iPhone-Modell", "iPhone 14 Pro")
standort = st.sidebar.text_input("Standort (optional)", "")
max_preis = st.sidebar.number_input("Maximaler Preis (€)", value=800)
min_preis = st.sidebar.number_input("Minimaler Preis (€)", value=100)

if st.sidebar.button("🔍 Anzeigen abrufen"):
    st.subheader("🔄 Suche wird ausgeführt...")

    suchbegriff = modell.replace(" ", "-").lower()
    base_url = f"https://www.kleinanzeigen.de/s-{suchbegriff}/k0"
    params = {
        "api_key": "0930d1cea7ce7a64dc09e44c9bf722b6",
        "url": base_url
    }

    try:
        response = requests.get("http://api.scraperapi.com", params=params)

        # Debug-Ausgabe
        st.markdown("### 🧪 Debug-Info")
        st.text(f"Statuscode: {response.status_code}")
        st.code(response.text[:1500], language="html")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            anzeigen = soup.find_all("li", class_="aditem")

            if not anzeigen:
                st.warning("⚠️ Keine passenden Anzeigen gefunden.")
            else:
                daten = []
                for anzeige in anzeigen:
                    titel = anzeige.find("a", class_="ellipsis")
                    preis = anzeige.find("p", class_="aditem-main--middle--price-shipping")

                    if titel and preis:
                        daten.append({
                            "Titel": titel.text.strip(),
                            "Link": "https://www.kleinanzeigen.de" + titel["href"],
                            "Preis": preis.text.strip()
                        })

                df = pd.DataFrame(daten)
                st.subheader("📋 Gefundene Anzeigen")
                st.dataframe(df)
        else:
            st.error("❌ Fehler beim Abrufen der Seite")

    except Exception as e:
        st.error(f"❌ Fehler beim Abruf: {e}")
