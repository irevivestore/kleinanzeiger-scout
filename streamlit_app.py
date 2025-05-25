import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# ScraperAPI Key
SCRAPER_API_KEY = "0930d1cea7ce7a64dc09e44c9bf722b6"

st.set_page_config(page_title="📱 Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout")

modell = st.sidebar.text_input("🔍 Modell eingeben", value="iPhone 14 Pro")
max_preis = st.sidebar.number_input("💰 Maximaler Preis (€)", min_value=0, value=1000)
min_preis = st.sidebar.number_input("💰 Minimaler Preis (€)", min_value=0, value=100)
anzeigen_limit = st.sidebar.slider("🔢 Anzahl der Ergebnisse", min_value=1, max_value=50, value=10)

start_suche = st.sidebar.button("🔎 Anzeigen abrufen")

def scrape_kleinanzeigen(modell, min_preis, max_preis, limit):
    st.info("⏳ Lade Anzeigen von Kleinanzeigen...")
    keyword = modell.replace(" ", "-").lower()
    base_url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"

    params = {
        "api_key": SCRAPER_API_KEY,
        "url": base_url,
        "country_code": "de"
    }

    try:
        response = requests.get("http://api.scraperapi.com", params=params)
        if response.status_code != 200:
            st.error(f"❌ Fehler beim Abrufen: Statuscode {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        anzeigen = []

        for item in soup.select(".aditem")[:limit]:
            title_tag = item.select_one(".text-module-begin > a")
            title = title_tag.text.strip() if title_tag else "Kein Titel"
            link = "https://www.kleinanzeigen.de" + title_tag['href'] if title_tag else ""
            price_tag = item.select_one(".aditem-main--middle .aditem-main--middle--price")
            price_text = price_tag.text.strip().replace("€", "").replace(".", "").strip() if price_tag else "0"
            try:
                price = int(price_text.split()[0])
            except:
                price = 0

            if min_preis <= price <= max_preis:
                anzeigen.append({
                    "title": title,
                    "price": price,
                    "link": link
                })

        return anzeigen

    except Exception as e:
        st.error(f"❌ Fehler: {e}")
        return []

if start_suche:
    daten = scrape_kleinanzeigen(modell, min_preis, max_preis, anzeigen_limit)

    if daten:
        st.success(f"✅ {len(daten)} Anzeigen gefunden")
        df = pd.DataFrame(daten)
        for _, row in df.iterrows():
            st.markdown(
                f"""
                <div style='border:1px solid #ccc; padding:10px; margin-bottom:10px; border-radius:5px;'>
                    <strong>{row['title']}</strong><br/>
                    💶 Preis: {row['price']} €<br/>
                    🔗 <a href="{row['link']}" target="_blank">Anzeige öffnen</a>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("⚠️ Keine passenden Anzeigen gefunden.")