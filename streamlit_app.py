# Kleinanzeigen Scout – ScraperAPI-Variante mit Streamlit
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Streamlit Page Config muss als erstes kommen
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")

# Deine ScraperAPI Zugangsdaten
SCRAPERAPI_KEY = "0930d1cea7ce7a64dc09e44c9bf722b6"

# Debug-Modus aktivierbar über Checkbox
DEBUG_MODE = st.sidebar.checkbox("🔧 Debug-Modus aktivieren")

# Caching der Ergebnisse
@st.cache_data(show_spinner=False)
def fetch_ads(modell, min_price=None, max_price=None, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()
    
    # NEUE URL-Logik mit Integer-Preisen
    if min_price is not None and max_price is not None:
        # Umwandlung in Integer für URL (entfernt Dezimalstellen)
        min_price_int = int(min_price)
        max_price_int = int(max_price)
        url = f"https://www.kleinanzeigen.de/s-preis:{min_price_int}:{max_price_int}/{keyword}/k0"
    else:
        url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={url}&render=true"

    if DEBUG_MODE:
        st.write(f"🔗 Finale URL: {url}")

    try:
        res = requests.get(scraper_url, timeout=20)
        if res.status_code != 200:
            if DEBUG_MODE:
                st.error(f"❌ HTTP Statuscode: {res.status_code}")
            return []

        soup = BeautifulSoup(res.content, "html.parser")
        cards = soup.select("article.aditem")
        if DEBUG_MODE:
            st.write(f"🔍 Anzahl gefundener Anzeigen: {len(cards)}")

        results = []
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
            st.write(f"📦 Gefiltert wegen fehlendem Versand: {gefiltert_versand}")

        return results

    except Exception as e:
        st.error(f"Fehler beim Abrufen: {e}")
        return []


# Streamlit App Interface
st.title("🔎 Kleinanzeigen Scout")

modell = st.text_input("🔍 iPhone-Modell", value="iPhone 14 Pro")
col1, col2 = st.columns(2)
with col1:
    min_preis = st.number_input("💶 Mindestpreis (€)", value=None, placeholder="Optional", step=1)
with col2:
    max_preis = st.number_input("💶 Maximalpreis (€)", value=None, placeholder="Optional", step=1)
nur_versand = st.checkbox("📦 Nur Angebote mit Versand")

start_search = st.button("Anzeigen abrufen")

if start_search:
    with st.spinner("Suche läuft..."):
        anzeigen = fetch_ads(modell, min_preis, max_preis, nur_versand)

    if not anzeigen:
        st.warning("Keine Anzeigen gefunden. Bitte Modell oder Filter anpassen.")
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
