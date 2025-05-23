import streamlit as st
import pandas as pd

# Demo-Datenstruktur für Kleinanzeigen-Ergebnisse (wird durch echten Scraper ersetzt)
demo_data = [
    {
        "titel": "iPhone 14 Pro - Display kaputt",
        "beschreibung": "Das Display ist gesprungen, sonst funktioniert alles.",
        "preis": 280,
        "link": "https://www.kleinanzeigen.de/s-anzeige/iphone-14-pro-display-kaputt/1234567890",
        "thumbnail": "https://via.placeholder.com/150"
    },
    {
        "titel": "iPhone 14 Pro mit Face ID Fehler",
        "beschreibung": "Face ID funktioniert nicht. Versand möglich.",
        "preis": 310,
        "link": "https://www.kleinanzeigen.de/s-anzeige/iphone-14-pro-face-id-defekt/0987654321",
        "thumbnail": "https://via.placeholder.com/150"
    },
]

# Funktion zum Abrufen der Anzeigen mittels Playwright
import asyncio
from playwright.async_api import async_playwright

@st.cache_data
def fetch_anzeigen(modell, preis_min, preis_max):
    # Asynchrone Scraper-Logik
    async def scrape():
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            # URL anpassen für Modell und Preisfilter
            base = "https://www.kleinanzeigen.de/s-anzeige/"
            # Beispiel: Handy-Telekom URL mit parametern
            url = f"https://www.kleinanzeigen.de/s-handy-telekom/anzeige:angebote/preis:{preis_min}:{preis_max}/{modell.replace(' ', '-').lower()}/k0c173+handy_telekom.device_equipment_s:only_device+handy_telekom.versand_s:ja"
            await page.goto(url)
            await page.wait_for_selector("article.aditem")
            items = await page.query_selector_all("article.aditem")
            for item in items:
                titel = (await item.query_selector("a.ellipsis")).inner_text() if await item.query_selector("a.ellipsis") else ""
                preis_text = (await item.query_selector("p.aditem-main--middle--price-shipping--price")).inner_text() if await item.query_selector("p.aditem-main--middle--price-shipping--price") else "0"
                preis = int(''.join(filter(str.isdigit, preis_text))) if preis_text else 0
                link_rel = await item.query_selector("a.ellipsis").get_attribute("href") if await item.query_selector("a.ellipsis") else None
                link = f"https://www.kleinanzeigen.de{link_rel}" if link_rel else ""
                thumb_elem = await item.query_selector("img")
                thumbnail = await thumb_elem.get_attribute("src") if thumb_elem else ""
                beschr = ""
                # Detailseite für Beschreibung
                if link:
                    detail = await browser.new_page()
                    await detail.goto(link)
                    try:
                        beschr_elem = await detail.query_selector("section#viewad-description, div#ad-description, div#viewad-description, div#viewad-content")
                        beschr = await beschr_elem.inner_text() if beschr_elem else ""
                    except:
                        beschr = ""
                    await detail.close()
                results.append({
                    "titel": titel.strip(),
                    "beschreibung": beschr.strip(),
                    "preis": preis,
                    "link": link,
                    "thumbnail": thumbnail
                })
            await browser.close()
        return results
    # Führe den async Scraper synchron aus
    return asyncio.run(scrape())

# Streamlit App-Konfiguration
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout – iPhone-Angebotsbewertung")

# Sidebar für Parameter
st.sidebar.header("🔧 Einstellungen")
modell = st.sidebar.selectbox(
    "Wähle Modell", ["iPhone 14 Pro", "iPhone 14", "iPhone 13 Pro", "iPhone 13"]
)
preis_min = st.sidebar.number_input(
    "Min. Preis (€)", min_value=0, max_value=5000, value=100, step=10
)
preis_max = st.sidebar.number_input(
    "Max. Preis (€)", min_value=0, max_value=5000, value=300, step=10
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Reparaturkosten (€)")

defekte_kosten = {
    "display": 80,
    "akku": 30,
    "backcover": 60,
    "kamera": 100,
    "lautsprecher": 60,
    "mikrofon": 50,
    "face id": 80,
    "wasserschaden": 250,
    "kein bild": 80,
    "defekt": 0,
}

verkaufspreis = 500
wunsch_marge = 120

# Button zum Abrufen der Anzeigen
if 'anzeigen' not in st.session_state:
    st.session_state.anzeigen = []

if st.sidebar.button("🔍 Anzeigen abrufen"):
    st.session_state.anzeigen = fetch_anzeigen(modell, preis_min, preis_max)

# Hauptbereich: Ergebnisse
st.markdown("## Analyse-Ergebnisse")
if not st.session_state.anzeigen:
    st.info("Klicke in der Seitenleiste auf 'Anzeigen abrufen', um die Angebote zu laden.")
else:
    for idx, anzeige in enumerate(st.session_state.anzeigen):
        # Bewertung berechnen
        defekte = st.session_state.get(f"defekte_{idx}", [])
        gesamt_reparatur = sum(defekte_kosten.get(d, 0) for d in defekte)
        maximaler_einkauf = verkaufspreis - wunsch_marge - gesamt_reparatur
        preis_angebot = anzeige['preis']
        diff = (maximaler_einkauf - preis_angebot) / preis_angebot
        # Farblogik: grün, blau, rot
        if preis_angebot <= maximaler_einkauf:
            bg_color = '#e6ffed'  # grün
            border_color = '#00b33c'
        elif diff >= -0.1:  # maximaler_einkauf ist bis zu 10% unter Angebotspreis
            bg_color = '#e6f0ff'  # blau
            border_color = '#3366ff'
        else:
            bg_color = '#ffe6e6'  # rot
            border_color = '#ff3333'

        # Anzeige-Container mit Hintergrundfarbe und Thumbnail
        thumbnail_url = anzeige.get('thumbnail', 'https://via.placeholder.com/150')
        st.markdown(
            f"<div style='background-color:{bg_color}; padding:15px; margin-bottom:10px; border:2px solid {border_color}; border-radius:10px; display:flex;'>"
            f"<img src='{thumbnail_url}' style='width:120px; height:auto; margin-right:15px; border-radius:5px;'/>"
            f"<div>"
            f"<h4>{anzeige['titel']} - {preis_angebot} €</h4>"
            f"<p><a href='{anzeige['link']}' target='_blank'>Zur Anzeige</a></p>"
            f"<p>{anzeige['beschreibung']}</p>"
            f"<p><strong>Max. Einkaufspreis:</strong> {maximaler_einkauf:.2f} €</p>"
            f"<p><strong>Empfehlung:</strong>"
            f" {'✅ Kauf möglich' if preis_angebot <= maximaler_einkauf else ('💬 Verhandeln' if diff >= -0.1 else '❌ Zu teuer')}"
            f"</p>"
            f"</div></div>", unsafe_allow_html=True
        )
        # Multiselect für Defekte
        st.multiselect(
            "Defekte auswählen:", list(defekte_kosten.keys()), key=f"defekte_{idx}"   
        )

        # Nach Auswahl neu berechnen und anzeigen
        if defekte:
            gesamt_reparatur = sum(defekte_kosten[d] for d in defekte)
            maximaler_einkauf = verkaufspreis - wunsch_marge - gesamt_reparatur
            st.write(f"Aktualisiert - Max. Einkaufspreis: {maximaler_einkauf:.2f} €")
