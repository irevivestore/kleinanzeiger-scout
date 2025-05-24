import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(page_title="📦 Kleinanzeigen Scout", layout="wide")
st.title("📦 Kleinanzeigen Scout")

# Seitenleiste mit Filteroptionen
st.sidebar.header("🔍 Filter")
modell = st.sidebar.text_input("iPhone Modell", "iPhone 14 Pro")

st.sidebar.subheader("💰 Preisfilter (€)")
preis_min = st.sidebar.number_input("Mindestpreis", value=100, step=10)
preis_max = st.sidebar.number_input("Maximalpreis", value=1400, step=10)

st.sidebar.markdown("---")

# Button zum Abrufen
if st.sidebar.button("🔄 Anzeigen abrufen"):
    with st.spinner("Lade Anzeigen..."):
        try:
            keyword = modell.replace(" ", "-").lower()
            url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                st.error(f"❌ Fehler beim Abrufen der Seite: Statuscode {response.status_code}")
            else:
                soup = BeautifulSoup(response.text, "html.parser")
                items = soup.select(".aditem")

                anzeigen = []
                for item in items:
                    title_tag = item.select_one(".aditem-main--middle--title")
                    price_tag = item.select_one(".aditem-main--middle--price-shipping--price")
                    href_tag = item.select_one("a")
                    image_tag = item.select_one("img")

                    if not title_tag or not price_tag:
                        continue

                    title = title_tag.get_text(strip=True)
                    price_str = price_tag.get_text(strip=True).replace("€", "").replace(".", "").replace(",", ".")

                    try:
                        price = float(price_str)
                    except:
                        continue

                    if preis_min <= price <= preis_max:
                        anzeigen.append({
                            "Titel": title,
                            "Preis": price,
                            "Link": "https://www.kleinanzeigen.de" + href_tag['href'] if href_tag else "",
                            "Thumbnail": image_tag['src'] if image_tag and 'src' in image_tag.attrs else ""
                        })

                if not anzeigen:
                    st.warning("⚠️ Keine passenden Anzeigen gefunden.")
                else:
                    st.success(f"✅ {len(anzeigen)} Anzeige(n) gefunden.")
                    for anzeige in anzeigen:
                        farbe = "#e0f7e9"  # Grün als Standard
                        with st.container():
                            st.markdown(
                                f"""
                                <div style='background-color:{farbe}; padding:10px; border-radius:10px; margin-bottom:10px; display:flex; align-items:center;'>
                                    <img src='{anzeige["Thumbnail"]}' style='width:100px; height:auto; margin-right:15px; border-radius:5px;'>
                                    <div>
                                        <a href='{anzeige["Link"]}' target='_blank'><strong>{anzeige["Titel"]}</strong></a><br>
                                        💶 <strong>{anzeige["Preis"]:.2f} €</strong>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
        except Exception as e:
            st.error(f"🚨 Fehler: {e}")

else:
    st.info("⬅️ Gib links ein Modell an und klicke auf 'Anzeigen abrufen'.")