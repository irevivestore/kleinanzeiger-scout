# Kleinanzeigen Scout - Korrigierte Version mit robustem Parsing
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
                        # VERBESSERTE TITEL-EXTRAKTION (aktualisierte Selektoren)
                        title_tag = (card.select_one('a.ellipsis') or 
                                   card.select_one('h2.text-module-begin') or
                                   card.select_one('a[href*="/s-anzeige"]'))
                        title = title_tag.get_text(strip=True) if title_tag else "Kein Titel"
                        
                        # VERBESSERTE PREIS-EXTRAKTION (mehrere Fallbacks)
                        price_tag = (card.select_one('p.aditem-main--middle--price') or
                                    card.select_one('div.aditem-main--middle--price') or
                                    card.select_one('span.price'))
                        price_text = price_tag.get_text(strip=True) if price_tag else "0"
                        
                        # Robustere Preisbereinigung
                        price_clean = re.sub(r"[^\d,]", "", price_text).replace(",", ".")
                        try:
                            price = int(float(price_clean)) if price_clean else 0
                        except:
                            price = 0
                        
                        # Versandprüfung mit mehr Keywords
                        card_text = card.get_text().lower()
                        versand_moeglich = any(word in card_text 
                                            for word in ["versand", "versenden", "shipping", "versand möglich"])
                        
                        if nur_versand and not versand_moeglich:
                            continue
                            
                        # Link-Extraktion mit Fallback
                        link_tag = card.select_one('a[href*="/s-anzeige"]')
                        link = "https://www.kleinanzeigen.de" + link_tag['href'] if link_tag else ""
                        
                        # Bild-Extraktion
                        img_tag = card.select_one('img[src^="https://"]')
                        img = img_tag['src'] if img_tag else ""
                        
                        results.append({
                            "title": title,
                            "price": price,
                            "link": link,
                            "thumbnail": img,
                            "versand": versand_moeglich
                        })
                        
                    except Exception as e:
                        if DEBUG_MODE:
                            st.write(f"⚠️ Anzeigenfehler: {str(e)}")
                        continue
                
                return results
                
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                sleep(2 * (attempt + 1))
                continue
            st.error("⌛ Timeout - Server antwortet nicht")
            return []
        except Exception as e:
            st.error(f"❌ Fehler: {str(e)}")
            return []

# UI mit verbesserter Darstellung
st.title("📱 iPhone Kleinanzeigen Scout")
st.markdown("### Aktuelle Angebote durchsuchen")

with st.form("search_form"):
    col1, col2 = st.columns(2)
    with col1:
        modell = st.text_input("Modell", value="iPhone 15 Pro")
    with col2:
        nur_versand = st.checkbox("Nur mit Versand")
    
    col3, col4 = st.columns(2)
    with col3:
        min_preis = st.number_input("Mindestpreis (€)", min_value=0, value=None, step=1)
    with col4:
        max_preis = st.number_input("Maximalpreis (€)", min_value=0, value=None, step=1)
    
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
        st.success(f"✅ {len(anzeigen)} Angebote gefunden")
        
        for anzeige in anzeigen:
            with st.container():
                cols = st.columns([1, 4])
                with cols[0]:
                    if anzeige["thumbnail"]:
                        st.image(anzeige["thumbnail"], width=120)
                
                with cols[1]:
                    st.markdown(f"""
                    **{anzeige["title"]}**  
                    **Preis:** {anzeige["price"]} € | **Versand:** {'✅ Ja' if anzeige["versand"] else '❌ Nein'}  
                    [🔗 Anzeige öffnen]({anzeige["link"]})
                    """)
                st.divider()

st.markdown("""
<style>
div[data-testid="stExpander"] div[role="button"] p {
    font-size: 1.2rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.caption("ℹ️ Tipp: Für präzisere Ergebnisse spezifische Modelle eingeben (z.B. 'iPhone 15 Pro Max 256GB')")
