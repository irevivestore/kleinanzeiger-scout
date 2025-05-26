# Kleinanzeigen Scout – Korrigierte Version
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from time import sleep

# Konfiguration
SCRAPERAPI_KEY = "0930d1cea7ce7a64dc09e44c9bf722b6"
MAX_RETRIES = 3
TIMEOUT = 30

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
DEBUG_MODE = st.sidebar.checkbox("🔧 Debug-Modus aktivieren")

@st.cache_data(show_spinner=False)
def fetch_ads(modell, min_price=None, max_price=None, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()
    
    if min_price is not None and max_price is not None:
        url = f"https://www.kleinanzeigen.de/s-preis:{int(min_price)}:{int(max_price)}/{keyword}/k0"
    else:
        url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={url}&render=true"

    if DEBUG_MODE:
        st.write(f"🔗 Ziel-URL: {url}")

    for attempt in range(MAX_RETRIES):
        try:
            res = requests.get(scraper_url, timeout=TIMEOUT)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "html.parser")
                cards = soup.select("article.aditem")
                results = []
                
                for card in cards:
                    try:
                        # VERBESSERTE TITEL-EXTRAKTION
                        title_tag = card.select_one('a[class*="ellipsis"]') or card.select_one('h2')
                        title = title_tag.get_text(strip=True) if title_tag else "Kein Titel"
                        
                        # VERBESSERTE PREIS-EXTRAKTION
                        price_tag = card.select_one('p[class*="price"]') or \
                                  card.select_one('.aditem-main--middle--price') or \
                                  card.select_one('.price')
                        price_text = price_tag.get_text(strip=True) if price_tag else "0"
                        price_match = re.search(r'\d+[\.,]?\d*', price_text.replace('.', ''))
                        price = int(float(price_match.group().replace(',', '.'))) if price_match else 0
                        
                        # Versandprüfung
                        versand_moeglich = any(word in card.get_text().lower() 
                                            for word in ["versand", "versenden", "shipping"])
                        
                        if nur_versand and not versand_moeglich:
                            continue
                            
                        # Link und Bild
                        link = "https://www.kleinanzeigen.de" + card.find('a')['href'] if card.find('a') else ""
                        img = card.find('img')['src'] if card.find('img') else ""
                        
                        results.append({
                            "title": title,
                            "price": price,
                            "link": link,
                            "thumbnail": img,
                            "versand": versand_moeglich
                        })
                        
                    except Exception as e:
                        if DEBUG_MODE:
                            st.write(f"⚠️ Anzeigenfehler: {e}")
                        continue
                
                return results
                
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                sleep(2)
                continue
            st.error("Timeout - Bitte später versuchen")
            return []
            
    return []

# UI-Code (wie zuvor)
st.title("🔎 Kleinanzeigen Scout")
# [...] (Rest des UI-Codes bleibt gleich)
