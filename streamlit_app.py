import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

SCRAPER_API_KEY = "0930d1cea7ce7a64dc09e44c9bf722b6"
SCRAPER_API_URL = "http://api.scraperapi.com/"

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")

st.title("🔎 Kleinanzeigen Scout")

# Seitenleiste für Benutzereingaben
st.sidebar.header("Suchkriterien")

modell = st.sidebar.text_input("📱 iPhone-Modell", value="iPhone 14 Pro")

min_preis = st.sidebar.number_input("🔽 Mindestpreis (€)", value=0)
max_preis = st.sidebar.number_input("🔼 Maximalpreis (€)", value=2000)

nur_versand = st.sidebar.checkbox("📦 Nur Angebote mit Versand", value=False)

verkaufspreis = st.sidebar.number_input("💰 Erwarteter Verkaufspreis (€)", value=750)
wunsch_marge = st.sidebar.number_input("📈 Wunschmarge (€)", value=100)

st.sidebar.subheader("🔧 Reparaturkosten (€)")
display_defekt = st.sidebar.number_input("Display", value=150)
akku_defekt = st.sidebar.number_input("Akku", value=80)
rückseite_defekt = st.sidebar.number_input("Rückseite", value=100)

reparaturkosten = {
    "display": display_defekt,
    "akku": akku_defekt,
    "rückseite": rückseite_defekt
}

def berechne_max_einkaufspreis():
    return verkaufspreis - wunsch_marge - sum(reparaturkosten.values())

max_einkaufspreis = berechne_max_einkaufspreis()

st.markdown(f"**📌 Maximaler Einkaufspreis:** `{max_einkaufspreis} €`")

# Anzeige abrufen
if st.button("🔍 Anzeigen abrufen"):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"

    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "render": "true"
    }

    try:
        response = requests.get(SCRAPER_API_URL, params=params)
        response.raise_for_status()
    except Exception as e:
        st.error(f"Fehler beim Abrufen: {e}")
    else:
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("article.aditem")

        anzeigen = []

        for card in cards:
            title_el = card.select_one(".aditem-main--middle--title")
            price_el = card.select_one(".aditem-main--middle--price")
            desc_el = card.select_one(".aditem-main--middle--description")
            link_el = card.select_one("a")
            thumb_el = card.select_one("img")

            if not (title_el and price_el and link_el):
                continue

            try:
                preis = int(re.sub(r"[^\d]", "", price_el.text))
            except:
                continue

            beschreibung = desc_el.text.strip().lower() if desc_el else ""
            versand_moeglich = "versand" in beschreibung or "zustellung" in beschreibung

            if preis < min_preis or preis > max_preis:
                continue

            if nur_versand and not versand_moeglich:
                continue

            anzeige = {
                "titel": title_el.text.strip(),
                "preis": preis,
                "beschreibung": beschreibung,
                "link": f"https://www.kleinanzeigen.de{link_el['href']}",
                "thumbnail": thumb_el["src"] if thumb_el else "",
                "versand": versand_moeglich
            }

            anzeigen.append(anzeige)

        if not anzeigen:
            st.warning("❌ Keine passenden Anzeigen gefunden.")
        else:
            st.success(f"✅ {len(anzeigen)} passende Anzeigen gefunden:")

            for anzeige in anzeigen:
                farbe = "#d4edda"  # Grün
                if anzeige["preis"] > max_einkaufspreis:
                    if anzeige["preis"] <= max_einkaufspreis * 1.1:
                        farbe = "#d0e7ff"  # Blau (Verhandlungsbasis)
                    else:
                        farbe = "#f8d7da"  # Rot

                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color:{farbe};padding:15px;margin-bottom:10px;border-radius:10px;display:flex;">
                            <img src="{anzeige['thumbnail']}" style="width:120px;height:auto;margin-right:15px;border-radius:8px;" />
                            <div>
                                <h4 style="margin-bottom:5px;">{anzeige['titel']}</h4>
                                <p style="margin:0;">💶 <strong>{anzeige['preis']} €</strong></p>
                                <p style="margin:0;font-size:0.9em;">📦 Versand: {"✅" if anzeige["versand"] else "❌"}</p>
                                <a href="{anzeige['link']}" target="_blank">🔗 Zur Anzeige</a>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
