# Kleinanzeigen Scout – ScraperAPI-Variante mit Streamlit
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Deine ScraperAPI Zugangsdaten
SCRAPERAPI_KEY = "0930d1cea7ce7a64dc09e44c9bf722b6"

# Caching der Ergebnisse
@st.cache_data(show_spinner=False)
def fetch_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={url}"

    try:
        res = requests.get(scraper_url, timeout=20)
        if res.status_code != 200:
            return []
        soup = BeautifulSoup(res.content, "html.parser")
        results = []

        for card in soup.select("article.aditem"):
            title_tag = card.select_one(".text-module-begin h2")
            title = title_tag.get_text(strip=True) if title_tag else ""

            price_tag = card.select_one(".aditem-main--middle .aditem-main--price")
            price_text = price_tag.get_text(strip=True) if price_tag else "0 €"
            price = int(price_text.replace("€", "").replace(".", "").strip() or 0)

            link_tag = card.select_one("a")
            link = "https://www.kleinanzeigen.de" + link_tag["href"] if link_tag else ""

            thumb_tag = card.select_one("img")
            thumbnail = thumb_tag["src"] if thumb_tag and "src" in thumb_tag.attrs else ""

            results.append({
                "title": title,
                "price": price,
                "link": link,
                "thumbnail": thumbnail
            })
        return results
    except Exception as e:
        st.error(f"Fehler beim Abrufen: {e}")
        return []


# Streamlit App Interface
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("🔎 Kleinanzeigen Scout")

modell = st.text_input("🔍 iPhone-Modell", value="iPhone 14 Pro")
start_search = st.button("Anzeigen abrufen")

if start_search:
    with st.spinner("Suche läuft..."):
        anzeigen = fetch_ads(modell)

    if not anzeigen:
        st.warning("Keine Anzeigen gefunden. Bitte Modell oder API Key prüfen.")
    else:
        for anzeige in anzeigen:
            bewertung = "💬 Verhandelbar" if anzeige["price"] < 1000 else "❌ Zu teuer"
            farbe = "#d0ebff" if "Verhandelbar" in bewertung else "#ffe3e3"

            st.markdown(f"""
            <div style='background-color: {farbe}; padding: 10px; border-radius: 10px; display: flex; align-items: center; margin-bottom: 10px;'>
                <img src="{anzeige['thumbnail']}" style="width: 100px; height: auto; margin-right: 15px; border-radius: 5px;" />
                <div>
                    <h4 style='margin-bottom:5px;'>{anzeige['title']}</h4>
                    <p style='margin:0;'>💰 <strong>{anzeige['price']} €</strong> | {bewertung}</p>
                    <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.caption("Version: ScraperAPI + BeautifulSoup | @2025")