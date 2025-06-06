import re
import asyncio
from datetime import datetime
from urllib.parse import quote_plus
from playwright.async_api import async_playwright


async def scrape_ads(suchbegriff, min_price=0, max_price=1500, nur_versand=False, nur_angebote=True, debug=False):
    if debug:
        print(f"[DEBUG] scrape_ads wurde mit Parametern aufgerufen: suchbegriff='{suchbegriff}', min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")

    base_url = "https://www.kleinanzeigen.de/s/"
    filters = []

    if nur_angebote:
        filters.append("anzeige:angebote")

    if min_price is not None and max_price is not None:
        filters.append(f"preis:{min_price}:{max_price}")

    filter_string = "/".join(filters)
    encoded_query = quote_plus(suchbegriff)
    url = f"{base_url}{filter_string}/{encoded_query}/k0"

    if debug:
        print(f"[scrape_ads] URL: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(3000)

        ad_elements = await page.query_selector_all("li.aditem")

        if debug:
            print(f"[scrape_ads] {len(ad_elements)} Anzeigen gefunden.")

        anzeigen = []

        for ad in ad_elements:
            try:
                link_element = await ad.query_selector("a.ellipsis")
                if not link_element:
                    continue

                relative_url = await link_element.get_attribute("href")
                if not relative_url:
                    continue

                ad_url = f"https://www.kleinanzeigen.de{relative_url}"

                # Detailseite laden für Titel und Beschreibung
                detail_page = await browser.new_page()
                await detail_page.goto(ad_url)
                await detail_page.wait_for_timeout(2000)

                # Titel auslesen
                title_element = await detail_page.query_selector("h1")
                title = await title_element.inner_text() if title_element else "Unbekannter Titel"

                # Beschreibung auslesen
                beschreibung_element = await detail_page.query_selector("#viewad-description")
                beschreibung = await beschreibung_element.inner_text() if beschreibung_element else ""

                await detail_page.close()

                # Preis aus Listing
                price_element = await ad.query_selector(".aditem-main--middle .aditem-main--middle--price")
                price_raw = await price_element.inner_text() if price_element else "0 €"
                price_raw = price_raw.replace(".", "").replace(" €", "").strip()

                # Preis und alter Preis extrahieren
                price_match = re.match(r"(\\d{2,5})(\\d{2,5})?", price_raw)
                price = int(price_match.group(1)) if price_match else 0
                price_alt = int(price_match.group(2)) if price_match and price_match.group(2) else None

                # Zeitstempel formatieren
                now = datetime.now()
                timestamp = now.strftime("%d.%m.%Y %H:%M")

                anzeigen.append({
                    "id": relative_url.split("/")[-1],
                    "titel": title.strip(),
                    "url": ad_url,
                    "preis": price,
                    "preis_alt": price_alt,
                    "beschreibung": beschreibung.strip(),
                    "erfasst_am": timestamp,
                    "aktualisiert_am": timestamp,
                    "modell": suchbegriff,
                })

            except Exception as e:
                if debug:
                    print(f"[scrape_ads] Fehler beim Parsen einer Anzeige: {e}")
                continue

        await browser.close()

        if debug:
            print(f"[scrape_ads] Fertig, {len(anzeigen)} Anzeigen zurückgegeben")

        return anzeigen


if __name__ == "__main__":
    ergebnisse = asyncio.run(scrape_ads("iPhone 14 Pro", min_price=0, max_price=1500, nur_versand=False, nur_angebote=True, debug=True))
    for ad in ergebnisse:
        print(ad)
