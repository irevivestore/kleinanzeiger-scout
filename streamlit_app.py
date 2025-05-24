import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

# ----------------- Sidebar: Sucheinstellungen ----------------- #
st.sidebar.title("🔍 Kleinanzeigen Scout")
modell = st.sidebar.text_input("Modell", value="iPhone 14 Pro")
min_price = st.sidebar.number_input("Mindestpreis (€)", value=100)
max_price = st.sidebar.number_input("Maximalpreis (€)", value=1000)
start_search = st.sidebar.button("📡 Anzeigen abrufen")

# ----------------- Hauptbereich ----------------- #
st.title("📱 Kleinanzeigen Scout")
status_placeholder = st.empty()

# ----------------- Scraping Funktion mit Playwright ----------------- #
async def scrape_kleinanzeigen(modell, min_price, max_price):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(5000)  # Warten auf JS-Rendering
        html = await page.content()
        await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("article.aditem")
        print(f"🔍 Gefundene Artikel: {len(items)}")

        results = []
        for item in items:
            title_tag = item.select_one("a.ellipsis")
            price_tag = item.select_one(".aditem-main--middle--price-shipping .aditem-main--middle--price")
            img_tag = item.select_one("img")

            if not title_tag or not price_tag:
                continue

            title = title_tag.get_text(strip=True)
            link = "https://www.kleinanzeigen.de" + title_tag["href"]
            price_str = price_tag.get_text(strip=True).replace("€", "").replace(".", "").replace(",", ".")
            thumbnail = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

            try:
                price = float(re.search(r"\d+", price_str).group())
            except:
                continue

            if price < min_price or price > max_price:
                continue

            results.append({
                "title": title,
                "price": price,
                "link": link,
                "thumbnail": thumbnail
            })

        return results

# ----------------- Ergebnisanzeige ----------------- #
def show_results(anzeigen):
    if not anzeigen:
        st.warning("❌ Keine passenden Anzeigen gefunden.")
        return

    for anzeige in anzeigen:
        col1, col2 = st.columns([1, 5])
        with col1:
            if anzeige["thumbnail"]:
                st.image(anzeige["thumbnail"], width=120)
        with col2:
            st.markdown(f"### [{anzeige['title']}]({anzeige['link']})")
            st.markdown(f"💶 **{anzeige['price']} €**")

# ----------------- Steuerung ----------------- #
if start_search:
    status_placeholder.info("🔄 Suche läuft... bitte warten...")
    try:
        anzeigen = asyncio.run(scrape_kleinanzeigen(modell, min_price, max_price))
        status_placeholder.empty()
        show_results(anzeigen)
    except Exception as e:
        status_placeholder.error(f"🚨 Fehler: {e}")