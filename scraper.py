# scraper.py

from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import re

def scrape_ads(modell, min_price=0, max_price=1500, nur_versand=False, nur_angebote=True, debug=False, config=None, log=None):
    def dbg(msg):
        if debug and log:
            log(f"[scrape_ads] {msg}")

    dbg(f"Starte Suche nach '{modell}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")

    base_url = "https://www.kleinanzeigen.de"
    kategorie_slug = "s-handy-telekom" if nur_versand else "s"
    angebote_slug = "anzeige:angebote" if nur_angebote else ""
    versand_suffix = "+handy_telekom.versand_s:ja" if nur_versand else ""
    preis_filter = f"preis:{min_price}:{max_price}"

    url_parts = [base_url, kategorie_slug]
    if angebote_slug:
        url_parts.append(angebote_slug)
    url_parts.append(preis_filter)
    url_parts.append(modell.replace(" ", "-").lower())
    url_parts.append(f"k0{'c173' if nur_versand else ''}{versand_suffix}")

    full_url = "/".join(part.strip("/") for part in url_parts if part)
    dbg(f"URL: {full_url}")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(full_url, timeout=15000)
            page.wait_for_selector("li.ad-listitem", timeout=10000)
            dbg("Seite geladen, Anzeigen werden extrahiert...")
        except Exception as e:
            dbg(f"Fehler beim Abruf der Seite: {e}")
            browser.close()
            return []

        ad_elements = page.query_selector_all("li.ad-listitem")
        dbg(f"{len(ad_elements)} Anzeigen gefunden.")

        for ad in ad_elements:
            try:
                title_el = ad.query_selector("a.ellipsis")
                title = title_el.inner_text().strip() if title_el else "Kein Titel"
                link = title_el.get_attribute("href") if title_el else ""
                link = base_url + link if link.startswith("/") else link

                image_el = ad.query_selector("img")
                image = image_el.get_attribute("src") if image_el else ""

                price_el = ad.query_selector("p.aditem-main--middle--price-shipping--price")
                raw_price = price_el.inner_text().strip() if price_el else "0"
                price = int(re.sub(r"[^\d]", "", raw_price)) if raw_price else 0

                desc_el = ad.query_selector("p.aditem-main--middle--description")
                beschreibung = desc_el.inner_text().strip() if desc_el else ""

                versand = "versand" in beschreibung.lower()

                # Bewertung der Anzeige basierend auf Konfiguration
                reparatur_summe = 0
                if config:
                    for defekt, kosten in config["reparaturkosten"].items():
                        if defekt.lower() in beschreibung.lower():
                            reparatur_summe += kosten

                    max_ek = config["verkaufspreis"] - config["wunsch_marge"] - reparatur_summe
                else:
                    max_ek = None

                results.append({
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
                dbg(f"Fehler beim Parsen einer Anzeige: {e}")
                continue

        browser.close()

    dbg(f"Fertig, {len(results)} Anzeigen zurückgegeben")
    return results