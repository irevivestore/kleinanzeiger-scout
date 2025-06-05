# scraper.py
import asyncio
from playwright.async_api import async_playwright

async def scrape_ads(query, min_price, max_price, nur_versand=False, nur_angebote=True, debug=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Kategorie-Teil für URL
        kategorie = "s-handy-telekom"

        # Preisfilter
        preisfilter = f"preis:{min_price}:{max_price}"

        # Angebotsfilter
        angebotsfilter = "anzeige:angebote" if nur_angebote else ""

        # Versandfilter (Teil von Kategorie-Parametern)
        versandfilter = "+handy_telekom.versand_s:ja" if nur_versand else ""

        # URL zusammenbauen
        pfadteile = [teil for teil in [kategorie, angebotsfilter, preisfilter, query.replace(" ", "-"), "k0"] if teil]
        url_pfad = "/".join(pfadteile)
        url = f"https://www.kleinanzeigen.de/{url_pfad}{versandfilter}"

        if debug:
            print(f"[scrape_ads] Starte Suche nach '{query}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")
            print(f"[scrape_ads] URL: {url}")

        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_selector("li.ad-listitem", timeout=10000)
            if debug:
                print("[scrape_ads] Seite geladen, Anzeigen werden extrahiert...")
        except Exception as e:
            if debug:
                print(f"[scrape_ads] Fehler beim Abruf der Seite: {e}")
            await browser.close()
            return []

        # Anzeigen parsen
        anzeigenelemente = await page.query_selector_all("li.ad-listitem")
        anzeigen = []

        for element in anzeigenelemente:
            try:
                title_el = await element.query_selector("h2")
                preis_el = await element.query_selector(".aditem-main--middle--price-shipping .aditem-main--middle--price")
                link_el = await element.query_selector("a")

                title = await title_el.inner_text() if title_el else "Kein Titel"
                preis = await preis_el.inner_text() if preis_el else "Kein Preis"
                link = await link_el.get_attribute("href") if link_el else None
                if link and not link.startswith("http"):
                    link = f"https://www.kleinanzeigen.de{link}"

                anzeigen.append({
                    "titel": title.strip(),
                    "preis": preis.strip(),
                    "link": link.strip() if link else "Kein Link"
                })

            except Exception as e:
                if debug:
                    print(f"[scrape_ads] Fehler beim Parsen einer Anzeige: {e}")
                continue

        await browser.close()

        if debug:
            print(f"[scrape_ads] Fertig, {len(anzeigen)} Anzeigen zurückgegeben")

        return anzeigen

# Optional zum Testen
# if __name__ == "__main__":
#     asyncio.run(scrape_ads("iPhone 14 Pro", 0, 1500, nur_versand=True, nur_angebote=True, debug=True))
