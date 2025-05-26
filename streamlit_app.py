# Kleinanzeigen Scout – ScraperAPI-Variante mit Streamlit
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Deine ScraperAPI Zugangsdaten
SCRAPERAPI_KEY = "0930d1cea7ce7a64dc09e44c9bf722b6"

# Debug-Modus aktivierbar über Checkbox
DEBUG_MODE = st.sidebar.checkbox("🔧 Debug-Modus aktivieren")

# Caching der Ergebnisse
@st.cache_data(show_spinner=False)
def fetch_ads(modell, min_price=0, max_price=3000, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={url}&render=true"

    if DEBUG_MODE:
        st.write(f"🔗 URL: {url}")

    try:
        res = requests.get(scraper_url, timeout=20)
        if res.status_code != 200:
            if DEBUG_MODE:
                st.error(f"❌ HTTP Statuscode: {res.status_code}")
            return []

        soup = BeautifulSoup(res.content, "html.parser")
        cards = soup.select("article.aditem")
        if DEBUG_MODE:
            st.write(f"🔍 Anzahl gefundener Anzeigen im HTML: {len(cards)}")

        results = []
        gefiltert_preis = 0
        gefiltert_versand = 0

        for card in cards:
            title_tag = card.select_one(".text-module-begin h2")
            title = title_tag.get_text(strip=True) if title_tag else ""

            price_tag = card.select_one(".aditem-main--middle .aditem-main--price")
            price_text = price_tag.get_text(strip=True) if price_tag else "0 €"
            try:
                price = int(re.sub(r"[^0-9]", "", price_text))
            except:
                continue

            desc_tag = card.select_one(".aditem-main--middle .aditem-main--description")
            beschreibung = desc_tag.get_text(strip=True).lower() if desc_tag else ""
            versand_moeglich = "versand" in beschreibung or "zustellung" in beschreibung

            if price < min_price or price > max_price:
                gefiltert_preis += 1
                continue

            if nur_versand and not versand_moeglich:
                gefiltert_versand += 1
                continue

            link_tag = card.select_one("a")
            link = "https://www.kleinanzeigen.de" + link_tag["href"] if link_tag else ""

            thumb_tag = card.select_one("img")
            thumbnail = thumb_tag["src"] if thumb_tag and "src" in thumb_tag.attrs else ""

            results.append({
                "title": title,
                "price": price,
                "link": link,
                "thumbnail": thumbnail,
                "beschreibung": beschreibung,
                "versand": versand_moeglich
            })

        if DEBUG_MODE:
            st.write(f"🧮 Gefiltert wegen Preis: {gefiltert_preis}")
            st.write(f"📦 Gefiltert wegen fehlendem Versand: {gefiltert_versand}")

        return results

    except Exception as e:
        st.error(f"Fehler beim Abrufen: {e}")
        return []


# Streamlit App Interface
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("🔎 Kleinanzeigen Scout")

modell = st.text_input("🔍 iPhone-Modell", value="iPhone 14 Pro")
min_preis = st.number_input("💶 Mindestpreis", value=100)
max_preis = st.number_input("💶 Maximalpreis", value=500)
nur_versand = st.checkbox("📦 Nur Angebote mit Versand")

start_search = st.button("Anzeigen abrufen")

if start_search:
    with st.spinner("Suche läuft..."):
        anzeigen = fetch_ads(modell, min_preis, max_preis, nur_versand)

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
                    <p style='margin:0;font-size:0.9em;'>📦 Versand: {'✅' if anzeige['versand'] else '❌'}</p>
                    <a href="{anzeige['link']}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.caption("Version: ScraperAPI + BeautifulSoup | Debug-Ready @2025")
