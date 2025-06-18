import asyncio
import re
import json
from playwright.async_api import async_playwright
import db  # Deine bestehende db.py wird hier importiert

async def scrape_kleinanzeigen(modell, verkaufspreis, wunsch_marge, reparaturkosten, debug=False):
    scraped_ads = []
    existing_ids = db.get_all_ad_ids_for_model(modell, include_archived=True)

    url = f"https://www.kleinanzeigen.de/s-suchanfrage.html?keywords={modell}&categoryId=195"
    
    if debug:
        print(f"[DEBUG] Starte Scraping für URL: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        await page.wait_for_timeout(2000)

        ad_elements = await page.query_selector_all("article.aditem")

        for ad in ad_elements:
            try:
                ad_id = await ad.get_attribute("data-adid")
                if ad_id in existing_ids:
                    if debug:
                        print(f"[DEBUG] Anzeige {ad_id} bereits bekannt, wird übersprungen.")
                    continue

                title = (await ad.query_selector("a.aditem-main--middle--title")).inner_text()
                link_element = await ad.query_selector("a.aditem-main--middle--title")
                link = await link_element.get_attribute("href")
                if not link.startswith("https://"):
                    link = "https://www.kleinanzeigen.de" + link

                image_element = await ad.query_selector("img")
                image = await image_element.get_attribute("src") if image_element else ""

                price_text = await ad.query_selector("p.aditem-main--middle--price-shipping").inner_text()
                price = parse_price(price_text)

                versand = 1 if "Versand möglich" in price_text else 0

                # Gehe auf die Artikelseite um Beschreibung und alle Bilder zu holen
                detail_page = await browser.new_page()
                await detail_page.goto(link)
                await detail_page.wait_for_timeout(1500)

                beschreibung_element = await detail_page.query_selector("p[class*='text-module-begin']")
                beschreibung = await beschreibung_element.inner_text() if beschreibung_element else ""

                # Zusätzliche Bilder sammeln
                bilder_liste = []
                image_elements = await detail_page.query_selector_all("div[class*='picture-gallery'] img")
                for img_el in image_elements:
                    img_src = await img_el.get_attribute("src")
                    if img_src:
                        bilder_liste.append(img_src)

                await detail_page.close()

                ad_data = {
                    "id": ad_id,
                    "modell": modell,
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": image,
                    "versand": versand,
                    "beschreibung": beschreibung,
                    "bilder_liste": bilder_liste
                }

                db.save_advert(ad_data)
                scraped_ads.append(ad_data)

                if debug:
                    print(f"[DEBUG] Anzeige {ad_id} gespeichert: {title} ({price} €)")
            except Exception as e:
                print(f"[ERROR] Fehler beim Verarbeiten einer Anzeige: {e}")

        await browser.close()

    return scraped_ads

def parse_price(price_str):
    # Beispiel: "450 € VB" oder "450499 €" 
    try:
        # Entferne alles außer Ziffern
        cleaned = re.sub(r"[^\d]", "", price_str)
        if cleaned:
            return int(cleaned)
    except:
        pass
    return 0

if __name__ == "__main__":
    # Beispielhafter Testlauf
    import sys

    modell = "iPhone 14 Pro"
    verkaufspreis = 800
    wunsch_marge = 150
    reparaturkosten = {
        "display": 200,
        "akku": 80
    }

    db.init_db()

    asyncio.run(scrape_kleinanzeigen(modell, verkaufspreis, wunsch_marge, reparaturkosten, debug=True))
