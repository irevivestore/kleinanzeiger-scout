import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Titel
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("🔍 Kleinanzeigen Scout")

# Eingabeparameter
modell = st.sidebar.text_input("📱 iPhone Modell", value="iPhone 14 Pro")
verkaufspreis = st.sidebar.number_input("💶 Erwarteter Verkaufspreis (€)", value=700)
wunschmarge = st.sidebar.number_input("📈 Wunschmarge (€)", value=100)
reparaturkosten = {
    "Display": st.sidebar.number_input("🔧 Display (€)", value=100),
    "Akku": st.sidebar.number_input("🔋 Akku (€)", value=50),
    "Backcover": st.sidebar.number_input("📱 Backcover (€)", value=60)
}

# Anzeigen abrufen
if st.button("🔄 Anzeigen abrufen"):
    with st.spinner("Anzeigen werden geladen..."):

        keyword = modell.replace(" ", "-").lower()
        base_url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"

        # ScraperAPI
        api_key = "0930d1cea7ce7a64dc09e44c9bf722b6"
        params = {
            "api_key": api_key,
            "url": base_url,
            "render": "true"  # <<< WICHTIG
        }

        response = requests.get("http://api.scraperapi.com", params=params)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            anzeigen = []

            for item in soup.find_all("article"):
                title_tag = item.find("a")
                title = title_tag.get_text(strip=True) if title_tag else "Kein Titel"
                link = "https://www.kleinanzeigen.de" + title_tag["href"] if title_tag else "#"

                price_tag = item.find(class_="aditem-main--middle")
                price_text = price_tag.get_text(strip=True) if price_tag else ""
                preis = 0
                for p in price_text.split():
                    if "€" in p:
                        try:
                            preis = int(p.replace("€", "").replace(".", "").strip())
                            break
                        except:
                            continue

                thumbnail_tag = item.find("img")
                thumbnail = thumbnail_tag["src"] if thumbnail_tag and "src" in thumbnail_tag.attrs else ""

                anzeigen.append({
                    "title": title,
                    "link": link,
                    "preis": preis,
                    "thumbnail": thumbnail
                })

            if not anzeigen:
                st.warning("⚠️ Es wurden keine passenden Anzeigen gefunden.")
            else:
                for i, anzeige in enumerate(anzeigen):
                    col1, col2 = st.columns([1, 4])

                    # Bewertung
                    gesamt_reparatur = sum(reparaturkosten.values())
                    max_einkaufspreis = verkaufspreis - wunschmarge - gesamt_reparatur

                    if anzeige["preis"] <= max_einkaufspreis:
                        farbe = "#d4edda"  # grün
                    elif anzeige["preis"] <= max_einkaufspreis * 1.1:
                        farbe = "#d0e7ff"  # blau
                    else:
                        farbe = "#f8d7da"  # rot

                    with col1:
                        if anzeige["thumbnail"]:
                            st.markdown(
                                f"<img src='{anzeige['thumbnail']}' style='width:120px; height:auto; border-radius:5px;'>",
                                unsafe_allow_html=True
                            )
                    with col2:
                        st.markdown(
                            f"<div style='background-color:{farbe}; padding:10px; border-radius:10px;'>"
                            f"<strong>{anzeige['title']}</strong><br>"
                            f"💰 Preis: {anzeige['preis']} €<br>"
                            f"🔗 <a href='{anzeige['link']}' target='_blank'>Zur Anzeige</a>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

        else:
            st.error(f"Fehler beim Abrufen der Seite. Statuscode: {response.status_code}")
