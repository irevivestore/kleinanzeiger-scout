import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

# Streamlit App-Konfiguration
st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")
st.title("📱 Kleinanzeigen Scout – iPhone-Angebotsbewertung")

# Sidebar für Parameter
st.sidebar.header("🔧 Einstellungen")
modell = st.sidebar.selectbox(
    "Wähle Modell", ["iPhone 14 Pro", "iPhone 14", "iPhone 13 Pro", "iPhone 13"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Reparaturkosten (€)")
# Reparaturkosten-Definition
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

verkaufspreis = st.sidebar.number_input("Verkaufspreis (€)", min_value=0, max_value=2000, value=500, step=10)
wunsch_marge = st.sidebar.number_input("Gewünschte Marge (€)", min_value=0, max_value=1000, value=120, step=10)

# Funktion zum Abrufen der Anzeigen ohne Preisfilter
@st.cache_data
def fetch_anzeigen(modell):
    query = modell.replace(' ', '-').lower()
    url = f"https://www.kleinanzeigen.de/s-{query}/k0"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return []
    soup = BeautifulSoup(res.text, 'html.parser')
    items = soup.find_all('article', class_='aditem')
    results = []
    for item in items:
        title_tag = item.find('a', class_='ellipsis')
        price_tag = item.find('p', class_='aditem-main--middle--price-shipping')
        thumb_tag = item.find('img')
        if not title_tag or not price_tag:
            continue
        titel = title_tag.text.strip()
        preis_text = price_tag.text.strip()
        preis_num = int(re.sub(r"[^0-9]", "", preis_text)) if re.search(r"\d", preis_text) else 0
        link = 'https://www.kleinanzeigen.de' + title_tag['href']
        thumbnail = thumb_tag['src'] if thumb_tag and thumb_tag.has_attr('src') else 'https://via.placeholder.com/150'
        results.append({
            'titel': titel,
            'beschreibung': '',
            'preis': preis_num,
            'link': link,
            'thumbnail': thumbnail
        })
    return results

# Anzeigen abrufen Button
if 'anzeigen' not in st.session_state:
    st.session_state.anzeigen = []

if st.sidebar.button("🔍 Anzeigen abrufen"):
    with st.spinner("Lade Anzeigen..."):
        st.session_state.anzeigen = fetch_anzeigen(modell)
    count = len(st.session_state.anzeigen)
    if count:
        st.sidebar.success(f"{count} Anzeigen geladen")
    else:
        st.sidebar.warning("Keine Anzeigen gefunden")

# Hauptbereich: Ergebnisse anzeigen
st.markdown("## Analyse-Ergebnisse")
if not st.session_state.anzeigen:
    st.info("Klicke auf 'Anzeigen abrufen', um Angebote ohne Preisfilter zu laden.")
else:
    for idx, ad in enumerate(st.session_state.anzeigen):
        with st.expander(f"{ad['titel']} – {ad['preis']} €"):
            st.image(ad['thumbnail'], width=120)
            st.write(f"**Link:** [Zur Anzeige]({ad['link']})")
            # Manuelle Defektauswahl
            defekte = st.multiselect("Defekte auswählen:", list(defekte_kosten.keys()), key=f"defekte_{idx}")
            # Bewertung
            gesamt_reparatur = sum(defekte_kosten[d] for d in defekte)
            max_einkauf = verkaufspreis - wunsch_marge - gesamt_reparatur
            st.write(f"**Max. Einkaufspreis:** {max_einkauf:.2f} €")
            st.write(f"**Defekte:** {', '.join(defekte) if defekte else 'Keine'}")
            if ad['preis'] <= max_einkauf:
                st.success("✅ Kauf möglich")
            else:
                st.error("❌ Zu teuer")