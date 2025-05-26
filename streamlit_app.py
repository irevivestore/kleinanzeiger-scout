# Kleinanzeigen Scout – Robust mit ScraperAPI
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from time import sleep

# Konfiguration
SCRAPERAPI_KEY = "0930d1cea7ce7a64dc09e44c9bf722b6"
MAX_RETRIES = 3  # Anzahl Wiederholungsversuche
TIMEOUT = 30     # Timeout in Sekunden

# Streamlit Setup
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
DEBUG_MODE = st.sidebar.checkbox("🔧 Debug-Modus aktivieren")

@st.cache_data(show_spinner=False)
def fetch_ads(modell, min_price=None, max_price=None, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()
    
    # URL-Konstruktion mit Integer-Preisen
    if min_price is not None and max_price is not None:
        url = f"https://www.kleinanzeigen.de/s-preis:{int(min_price)}:{int(max_price)}/{keyword}/k0"
    else:
        url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={url}&render=true"

    if DEBUG_MODE:
        st.write(f"🔗 Anfrage-URL: {scraper_url}")

    for attempt in range(MAX_RETRIES):
        try:
            res = requests.get(scraper_url, timeout=TIMEOUT)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "html.parser")
                cards = soup.select("article.aditem")
                
                if DEBUG_MODE:
                    st.write(f"🔍 Gefundene Anzeigen: {len(cards)}")
                
                results = []
                gefiltert_versand = 0

                for card in cards:
                    try:
                        # Titel extrahieren
                        title_tag = card.select_one(".text-module-begin h2")
                        title = title_tag.get_text(strip=True) if title_tag else ""
                        
                        # Preis extrahieren
                        price_tag = card.select_one(".aditem-main--middle .aditem-main--price")
                        price_text = price_tag.get_text(strip=True) if price_tag else "0 €"
                        price = int(re.sub(r"[^0-9]", "", price_text))
                        
                        # Beschreibung und Versand prüfen
                        desc_tag = card.select_one(".aditem-main--middle .aditem-main--description")
                        beschreibung = desc_tag.get_text(strip=True).lower() if desc_tag else ""
                        versand_moeglich = "versand" in beschreibung or "versenden" in beschreibung
                        
                        # Versand-Filterung
                        if nur_versand and not versand_moeglich:
                            gefiltert_versand += 1
                            continue
                            
                        # Link und Thumbnail
                        link_tag = card.select_one("a")
                        link = "https://www.kleinanzeigen.de" + link_tag["href"] if link_tag else ""
                        
                        thumb_tag = card.select_one("img")
                        thumbnail = thumb_tag["src"] if thumb_tag and "src" in thumb_tag.attrs else ""
                        
                        results.append({
                            "title": title,
                            "price": price,
                            "link": link,
                            "thumbnail": thumbnail,
                            "versand": versand_moeglich
                        })
                        
                    except Exception as card_error:
                        if DEBUG_MODE:
                            st.write(f"⚠️ Fehler bei Anzeigenverarbeitung: {card_error}")
                        continue
                
                if DEBUG_MODE:
                    st.write(f"📦 Gefiltert (Versand): {gefiltert_versand}")
                
                return results
                
            else:
                st.error(f"API-Fehler: Statuscode {res.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                sleep(2 * (attempt + 1))  # Exponentielle Backoff
                continue
            st.error("⌛ Timeout nach mehreren Versuchen. Bitte später erneut probieren.")
            return []
            
        except Exception as e:
            st.error(f"❌ Kritischer Fehler: {str(e)}")
            return []

# UI Interface
st.title("🔎 Kleinanzeigen Scout")
st.markdown("### iPhone-Angebote durchsuchen")

with st.form("search_form"):
    col1, col2 = st.columns(2)
    with col1:
        modell = st.text_input("Modell", value="iPhone 14 Pro")
    with col2:
        nur_versand = st.checkbox("Nur mit Versand")
    
    col3, col4 = st.columns(2)
    with col3:
        min_preis = st.number_input("Mindestpreis (€)", min_value=0, value=None, step=1, placeholder="Optional")
    with col4:
        max_preis = st.number_input("Maximalpreis (€)", min_value=0, value=None, step=1, placeholder="Optional")
    
    submitted = st.form_submit_button("🔍 Suche starten")

if submitted:
    with st.spinner("Durchsuche Kleinanzeigen..."):
        anzeigen = fetch_ads(
            modell=modell,
            min_price=min_preis,
            max_price=max_preis,
            nur_versand=nur_versand
        )
    
    if not anzeigen:
        st.warning("Keine passenden Angebote gefunden. Bitte Filter anpassen.")
    else:
        st.success(f"🏆 {len(anzeigen)} Angebote gefunden")
        
        for anzeige in anzeigen:
            col_img, col_info = st.columns([1, 4])
            with col_img:
                if anzeige["thumbnail"]:
                    st.image(anzeige["thumbnail"], width=100)
            
            with col_info:
                # Preisbewertung
                price_rating = "💎 Guter Preis" if anzeige["price"] < 500 else "💸 Teurer"
                
                st.markdown(f"""
                **{anzeige["title"]}**  
                💶 **{anzeige["price"]}€** | {price_rating} | 📦 {'Ja' if anzeige["versand"] else 'Nein'}  
                [🔗 Zur Anzeige]({anzeige["link"]})
                """)
                
                st.divider()

st.caption("""
ℹ️ Tipp: Für bessere Ergebnisse spezifische Modelle eingeben (z.B. "iPhone 15 Pro Max 256GB")  
🛡️ Daten werden über ScraperAPI bezogen | v2.1 | Fehlerhaft? Debug-Modus aktivieren
""")
