# scraper.py

import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright


def scrape_ads(
    modell,
    min_price=0,
    max_price=1500,
    nur_versand=False,
    nur_angebote=True,
    debug=False,
    config=None,
    log=print
):
    def debug_log(msg):
        if debug:
            log(f"[scrape_ads] {msg}")

    debug_log(f"Starte Suche nach '{modell}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")

    base_url = "https://www.kleinanzeigen.de/s-"
    category = "handy-telekom"  # optional je nach Modelltyp anpassbar

    filters = []
    if nur_angebote:
        filters.append("anzeige:angebote")
    if min_price is not None and max_price is not None:
        filters.append(f"preis:{min_price}:{max_price}")

    filter_part = "/".join(filters)
    search_term = modell.replace(" ", "-").lower()
    url = f"{base_url}{category}/{filter_part}/{search_term}/k0"

    debug_log(f"URL: {url}")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        time.sleep(3)

        debug_log("Seite geladen, Anzeigen werden extrahiert...")

        ads = page.query_selector_all("article.aditem")
        debug_log(f"{len(ads)} Anzeigen gefunden.")

        for ad in ads:
            try:
                title_el = ad.query_selector("a.aditem-main--title")
                price_el = ad.query_selector(".aditem-main--middle--price-shipping--price")
                image_el = ad.query_selector("img")
                link_el = ad.query_selector("a.aditem-main--title")
                desc_el = ad.query_selector(".aditem-main--middle")

                title = title_el.inner_text().strip()
                price_str = price_el.inner_text().strip().replace("€", "").replace(".", "").replace("VB", "").strip()
                price = int(re.sub(r"[^\d]", "", price_str)) if price_str else 0
                image = image_el.get_attribute("src") if image_el else ""
                link = "https://www.kleinanzeigen.de" + link_el.get_attribute("href")
                beschreibung = desc_el.inner_text().strip() if desc_el else ""

                versand = "versand" in beschreibung.lower()

                # ID aus Link extrahieren
                match = re.search(r"/(\d+)-", link)
                ad_id = match.group(1) if match else None

                # Bewertung durchführen
                reparatur_summe = 0
                if config:
                    for defekt, kosten in config["reparaturkosten"].items():
                        if defekt.lower() in beschreibung.lower():
                            reparatur_summe += kosten

                    max_ek = config["verkaufspreis"] - config["wunsch_marge"] - reparatur_summe
                else:
                    max_ek = 0

                results.append({
                    "id": ad_id,
                    "title": title,
                    "price": price,
                    "image": image,
                    "link": link,
                    "beschreibung": beschreibung,
                    "versand": versand,
                    "reparaturkosten": reparatur_summe,
                    "max_einkaufspreis": max_ek,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })

            except Exception as e:
                debug_log(f"Fehler beim Parsen einer Anzeige: {e}")

        browser.close()

    debug_log(f"Fertig, {len(results)} Anzeigen zurückgegeben")
    return results