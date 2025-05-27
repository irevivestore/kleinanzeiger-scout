# streamlit_serpapi_app.py
import streamlit as st
import requests

# 🔐 SerpApi Key (nur lokal verwenden – NICHT öffentlich!)
SERPAPI_KEY = "7252f6944eaa4137c65a6749de9149ec1a035b49cf79ccbf73b6e2d1c5f6412b"

st.set_page_config(page_title="Kleinanzeigen Scout – SerpApi", layout="wide")
st.title("📱 Kleinanzeigen Scout – SerpApi Edition")

# 🎛️ Sucheinstellungen
modell = st.text_input("🔍 iPhone-Modell", value="iPhone 14 Pro")
max_preis = st.number_input("💰 Maximalpreis (€)", value=800, min_value=0)
nur_versand = st.checkbox("📦 Nur mit Versand", value=False)

if st.button("🔎 Anzeigen suchen"):
    st.info("⏳ SerpApi wird kontaktiert...")

    # 🔗 API-Aufruf vorbereiten
    params = {
        "engine": "ebay_kleinanzeigen",
        "q": modell,
        "api_key": SERPAPI_KEY,
        "num": 20
    }

    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    listings = data.get("ads", [])

    if not listings:
        st.warning("❌ Keine Anzeigen gefunden.")
    else:
        st.success(f"✅ {len(listings)} Anzeigen gefunden:")

        for ad in listings:
            title = ad.get("title", "Kein Titel")
            price = ad.get("price")
            link = ad.get("link")
            thumbnail = ad.get("thumbnail")
            description = ad.get("snippet", "")
            shipping = "versand" in description.lower()

            # Filter anwenden
            if nur_versand and not shipping:
                continue
            if price and price > max_preis:
                continue

            # Anzeige darstellen
            st.markdown(f"""
            <div style="border: 1px solid #ccc; border-radius: 10px; padding: 10px; margin-bottom: 10px; display: flex;">
                <img src="{thumbnail}" width="100" style="border-radius: 5px; margin-right: 15px;" />
                <div>
                    <strong>{title}</strong><br>
                    💰 Preis: {price} €<br>
                    📦 Versand: {"✅ Ja" if shipping else "❌ Nein"}<br>
                    <a href="{link}" target="_blank">🔗 Anzeige öffnen</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.caption("🔒 SerpApi-Integration · Nur für private Nutzung · © 2025")