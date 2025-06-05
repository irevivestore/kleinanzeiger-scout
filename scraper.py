import re
from datetime import datetime
from urllib.parse import quote
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
    if config is None:
        config = {
            "verkaufspreis": 0,
            "wunsch_marge": 0,
            "reparaturkosten": {}
        }

    def debug_log(msg):
        if debug and log:
            log(f"[scrape_ads] {msg}")

    # Basis-URL
    base_url = "https://www.kleinanzeigen.de"

    # Kategorie (optional bei Versandfilter nötig)
    kategorie = "handy-telekom" if nur_versand else ""

    # Query-Bestandteile
    pfadteile = ["s"]
    if kategorie:
        pfadteile.append(f"-{kategorie}")
    if nur_angebote:
        pfadteile.append("anzeige:angebote")
    pfadteile.append(f"preis:{min_price}:{max_price}")
    pfadteile.append(quote(modell))
    pfadteile.append("k0")

    url = f"{base_url}/{'/'.join(pfadteile)}"
    if nur_versand:
        url += "c173+handy_telekom.versand_s:ja"

    debug_log(f"Starte Suche nach '{modell}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")
    debug_log(f"URL: {url}")

    anzeigen = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)

        items = page.query_selector_all("article.aditem")
        debug_log(f"{len(items)} Anzeigen gefunden.")

        for item in items:
            try:
                link_el = item.query_selector("a")
                if not link_el:
                    continue
                link = link_el.get_attribute("href")
                if not link or not link.startswith("/s-anzeige/"):
                    continue
                full_url = base_url + link

                # ID extrahieren aus der URL
                match = re.search(r"/s-anzeige/.*?/(\d+)", link)
                ad_id = match.group(1) if match else None
                if not ad_id:
                    continue

                title_el = item.query_selector("a h2")
                title = title_el.inner_text().strip() if title_el else "Unbekannter Titel"

                preis_el = item.query_selector(".aditem-main--middle .aditem-main--middle--price")
                preis_text = preis_el.inner_text().strip().replace("€", "").replace(".", "").replace(",", "").strip() if preis_el else ""
                try:
                    price = int(re.findall(r"\d+", preis_text)[0])
                except (IndexError, ValueError):
                    price = 0

                image_el = item.query_selector("img")
                image_url = image_el.get_attribute("src") if image_el else ""

                # Bewertung
                reparaturkosten = 0  # Wird standardmäßig auf 0 gesetzt
                max_einkaufspreis = config["verkaufspreis"] - config["wunsch_marge"] - reparaturkosten

                if price <= max_einkaufspreis:
                    farbe = "grün"
                elif price <= max_einkaufspreis + (config["wunsch_marge"] * 0.1):
                    farbe = "blau"
                else:
                    farbe = "rot"

                anzeigen.append({
                    "id": ad_id,
                    "title": title,
                    "price": price,
                    "link": full_url,
                    "image": image_url,
                    "beschreibung": "",  # Wird ggf. später ergänzt
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "versand": nur_versand,
                    "reparaturkosten": reparaturkosten,
                    "bewertung": farbe,
                })

            except Exception as e:
                debug_log(f"Fehler beim Parsen einer Anzeige: {e}")
                continue

        browser.close()

    debug_log(f"Fertig, {len(anzeigen)} Anzeigen zurückgegeben")
    return anzeigen