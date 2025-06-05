import asyncio
from playwright.async_api import async_playwright
import re

async def scrape_ads(suchbegriff, min_price, max_price, nur_versand=False, nur_angebote=False):
    print(f"[scrape_ads] Starte Suche nach '{suchbegriff}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")

    # Basiskomponenten der URL
    base = "https://www.kleinanzeigen.de"
    kategorie = "s-handy-telekom"
    preisfilter = f"preis:{min_price}:{max_price}"
    angebotfilter = "anzeige:angebote" if nur_angebote else ""
    versandfilter = "+handy_telekom.versand_s:ja" if nur_versand else ""

    # Baue URL
    filter_parts = "/".join(filter(None, [angebotfilter, preisfilter, suchbegriff]))
    url = f"{base}/{kategorie}/{filter_parts}/k0c173{versandfilter}"

    print(f"[scrape_ads] URL: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url)
            await page.wait_for_selector("li.ad-listitem", timeout=10000)
            print("[scrape_ads] Seite geladen, Anzeigen werden extrahiert...")

            ads = await page.locator("li.ad-listitem").all()
            print(f"[scrape_ads] {len(ads)} Anzeigen gefunden.")

            results = []
            for ad in ads:
                try:
                    # Titel
                    title_el = ad.locator(".ad-listitem-main--title")
                    title = await title_el.inner_text() if await title_el.count() > 0 else None

                    # Preis
                    price_el = ad.locator(".aditem-main--middle--price-shipping .aditem-main--middle--price")
                    price_text = await price_el.inner_text() if await price_el.count() > 0 else None
                    price_match = re.search(r"(\d{1,3}(?:\.\d{3})*|\d+)", price_text.replace(".", "").replace("€", "")) if price_text else None
                    price = int(price_match.group().replace(".", "")) if price_match else None

                    # Ort
                    ort_el = ad.locator(".aditem-main--bottom--left")
                    ort = await ort_el.inner_text() if await ort_el.count() > 0 else "Unbekannt"

                    # Link
                    link_el = ad.locator("a.ad-listitem")
                    relative_url = await link_el.get_attribute("href") if await link_el.count() > 0 else None
                    full_url = base + relative_url if relative_url else None

                    if not all([title, price, full_url]):
                        continue  # unvollständige Anzeige überspringen

                    results.append({
                        "titel": title.strip(),
                        "preis": price,
                        "ort": ort.strip(),
                        "url": full_url,
                    })

                except Exception as e:
                    print(f"[scrape_ads] Fehler beim Parsen einer Anzeige: {e}")
                    continue

        except Exception as e:
            print(f"[scrape_ads] Fehler beim Abruf der Seite: {e}")
            results = []

        await browser.close()

    print(f"[scrape_ads] Fertig, {len(results)} Anzeigen zurückgegeben")
    return results
