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
import streamlit as st
import pandas as pd
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

# Funktion zum Abrufen der Anzeigen über Desktop-URL
@st.cache_data
def fetch_anzeigen(modell, preis_min, preis_max):
    # Desktop-URL: Modell direkt im Pfad
    query = modell.replace(' ', '-').lower()
    url = (
        f"https://www.kleinanzeigen.de/s-{query}/k0"
        f"?price={preis_min}-{preis_max}&isSearchRequest=true"
    )
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
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
        thumbnail = thumb_tag['src'] if thumb_tag and thumb_tag.has_attr('src') else ''
        # Beschreibung leer, manuell editierbar
        beschreibung = ''
        results.append({
            'titel': titel,
            'beschreibung': beschreibung,
            'preis': preis_num,
            'link': link,
            'thumbnail': thumbnail
        })
    return results

# Button zum Abrufen der Anzeigen
if 'anzeigen' not in st.session_state:
    st.session_state.anzeigen = []

abfragen = st.sidebar.button("🔍 Anzeigen abrufen")
if abfragen:
    with st.spinner("Suche Anzeigen auf Kleinanzeigen..."):
        st.session_state.anzeigen = fetch_anzeigen(modell, preis_min, preis_max)
    anzahl = len(st.session_state.anzeigen)
    if anzahl:
        st.sidebar.success(f"{anzahl} Anzeigen geladen")
    else:
        st.sidebar.warning("Keine Anzeigen gefunden")

# Hauptbereich: Ergebnisse
st.markdown("## Analyse-Ergebnisse")
if not st.session_state.anzeigen:
    st.info("Klicke in der Seitenleiste auf 'Anzeigen abrufen', um die Angebote zu laden.")
else:
    for idx, anzeige in enumerate(st.session_state.anzeigen):
        # Manuelle Defektauswahl
        defekte = st.multiselect(
            "Defekte auswählen:", list(defekte_kosten.keys()), key=f"defekte_{idx}"   
        )
        # Bewertung berechnen
        gesamt_reparatur = sum(defekte_kosten.get(d, 0) for d in defekte)
        maximaler_einkauf = verkaufspreis - wunsch_marge - gesamt_reparatur
        preis_angebot = anzeige['preis']
        diff = (maximaler_einkauf - preis_angebot) / preis_angebot if preis_angebot else 0
        # Farblogik: grün, blau, rot
        if preis_angebot <= maximaler_einkauf:
            bg_color, border_color = '#e6ffed', '#00b33c'
            recommendation = '✅ Kauf möglich'
        elif diff >= -0.1:
            bg_color, border_color = '#e6f0ff', '#3366ff'
            recommendation = '💬 Verhandeln'
        else:
            bg_color, border_color = '#ffe6e6', '#ff3333'
            recommendation = '❌ Zu teuer'
        # Anzeige-Container
        thumbnail_url = anzeige.get('thumbnail', 'https://via.placeholder.com/150')
        st.markdown(
            f"<div style='background-color:{bg_color}; padding:15px; margin-bottom:10px; border:2px solid {border_color}; border-radius:10px; display:flex;'>"
            f"<img src='{thumbnail_url}' style='width:120px; margin-right:15px; border-radius:5px;'/>"
            f"<div>"
            f"<h4>{anzeige['titel']} - {preis_angebot} €</h4>"
            f"<p><a href='{anzeige['link']}' target='_blank'>Zur Anzeige</a></p>"
            f"<p>{anzeige.get('beschreibung', '')}</p>"
            f"<p><strong>Max. Einkaufspreis:</strong> {maximaler_einkauf:.2f} €</p>"
            f"<p><strong>Empfehlung:</strong> {recommendation}</p>"
            f"</div></div>", unsafe_allow_html=True
        )
