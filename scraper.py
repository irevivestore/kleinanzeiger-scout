# scraper.py

from playwright.sync_api import sync_playwright
from urllib.parse import quote_plus
from datetime import datetime
import re

def scrape_ads(modell, min_price=0, max_price=1500, nur_versand=False, nur_angebote=True, debug=False, config=None, log=print):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        base_url = "https://www.kleinanzeigen.de/s"
        suchbegriff = quote_plus(modell)
        pfadteile = []

        if nur_angebote:
            pfadteile.append("anzeige:angebote")

        pfadteile.append(f"preis:{min_price}:{max_price}")
        pfadteile.append(suchbegriff)
        pfadteile.append("k0")  # Kategorie Handy & Telekom

        url = f"{base_url}/{'/'.join(pfadteile)}"
        log(f"[scrape_ads] Starte Suche nach '{modell}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")
        log(f"[scrape_ads] URL: {url}")

        page.goto(url)
        page.wait_for_selector("article.aditem")

        anzeigenelemente = page.query_selector_all("article.aditem")
        log(f"[scrape_ads] {len(anzeigenelemente)} Anzeigen gefunden.")

        anzeigen = []
        for ad in anzeigenelemente:
            try:
                link_element = ad.query_selector("a")
                if not link_element:
                    continue
                href = link_element.get_attribute("href")
                ad_id = re.search(r"/s-anzeige/[^/]+/(\d+)", href)
                if not ad_id:
                    continue
                ad_id = ad_id.group(1)

                title = ad.query_selector(".text-module-begin h2").inner_text().strip()
                price_text = ad.query_selector(".aditem-main--middle .aditem-main--middle--price-shipping").inner_text()
                price = int(re.sub(r"[^\d]", "", price_text))

                image_el = ad.query_selector("img")
                image_url = image_el.get_attribute("src") if image_el else ""

                full_url = f"https://www.kleinanzeigen.de{href}"

                reparaturkosten = 0
                farbe = "#ffffff"
                if config:
                    rep_kosten = config["reparaturkosten"]
                    verkaufspreis = config["verkaufspreis"]
                    wunsch_marge = config["wunsch_marge"]

                    max_einkaufspreis = verkaufspreis - wunsch_marge
                    farbe = (
                        "#d4edda" if price <= max_einkaufspreis else
                        "#d1ecf1" if price <= max_einkaufspreis + (wunsch_marge * 0.1) else
                        "#f8d7da"
                    )

                anzeigen.append({
                    "id": ad_id,
                    "title": title,
                    "price": price,
                    "link": full_url,
                    "image": image_url,
                    "beschreibung": "",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "versand": nur_versand,
                    "reparaturkosten": reparaturkosten,
                    "bewertung": farbe,
                    "modell": modell  # <-- Wichtig: Modell-Feld ergänzt
                })

            except Exception as e:
                log(f"[scrape_ads] Fehler beim Parsen einer Anzeige: {e}")
                continue

        browser.close()
        log(f"[scrape_ads] Fertig, {len(anzeigen)} Anzeigen zurückgegeben")
        return anzeigen