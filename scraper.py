from playwright.sync_api import sync_playwright
from datetime import datetime
import re

def scrape_ads(
    modell: str,
    min_price: int = 0,
    max_price: int = 1500,
    nur_versand: bool = False,
    debug: bool = False,
    config: dict | None = None,
    log=None
):
    def _log(msg):
        if debug:
            if log:
                log(msg)
            else:
                print(msg)

    _log(f"[scrape_ads] Starte Suche nach '{modell}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}")

    BASE_URL = "https://www.ebay-kleinanzeigen.de"
    # URL passend zum Suchfilter bauen
    url = (
        f"{BASE_URL}/s-suchanfrage:angebote/{modell.replace(' ', '-')}/"
        f"preis:{min_price}--{max_price}/"
    )
    if nur_versand:
        url += "versand:1/"

    _log(f"[scrape_ads] URL: {url}")

    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url)
            _log(f"[scrape_ads] Seite geladen: {page.title()}")

            page.wait_for_selector("li.ad-listitem", timeout=10000)
            ads = page.query_selector_all("li.ad-listitem")
            _log(f"[scrape_ads] Gefundene Anzeigen: {len(ads)}")

            for i, ad in enumerate(ads):
                try:
                    title_el = ad.query_selector("a.ellipsis")
                    title = title_el.inner_text().strip() if title_el else "Kein Titel"

                    link = title_el.get_attribute("href") if title_el else ""
                    if link and not link.startswith("http"):
                        link = BASE_URL + link

                    price_el = ad.query_selector("p.aditem-main--middle--price")
                    price_text = price_el.inner_text().strip() if price_el else "0 €"
                    price = _parse_price(price_text)

                    image_el = ad.query_selector("img")
                    image_url = image_el.get_attribute("src") if image_el else ""

                    versand = False
                    versand_el = ad.query_selector("p.aditem-main--middle--shipping")
                    if versand_el:
                        versand = "Versand" in versand_el.inner_text()

                    zeit_el = ad.query_selector("div.aditem-main--bottom--left")
                    created_at = None
                    if zeit_el:
                        zeit_text = zeit_el.inner_text()
                        created_at = _parse_date_from_text(zeit_text)

                    # Kurzbeschreibung wird nicht geladen, da auf Detailseite

                    # Reparaturkosten schätzen mit config
                    rep_kosten = 0
                    if config and "reparaturkosten" in config:
                        rep_kosten = _estimate_repair_costs("", config["reparaturkosten"])

                    ad_data = {
                        "title": title,
                        "link": link,
                        "price": price,
                        "image": image_url,
                        "versand": versand,
                        "created_at": created_at or "",
                        "updated_at": "",
                        "beschreibung": "",
                        "reparaturkosten": rep_kosten,
                    }

                    _log(f"[scrape_ads] Anzeige {i+1}: {title} - {price}€ - Versand: {versand}")

                    results.append(ad_data)

                except Exception as e:
                    _log(f"[scrape_ads] Fehler bei Anzeige {i+1}: {e}")

            browser.close()
    except Exception as e:
        _log(f"[scrape_ads] Fehler beim Abruf der Seite: {e}")

    _log(f"[scrape_ads] Fertig, {len(results)} Anzeigen zurückgegeben")
    return results


def _parse_price(text: str) -> int:
    # Preis extrahieren z.B. "120 €" -> 120
    match = re.search(r"(\d+)", text.replace(".", ""))
    if match:
        return int(match.group(1))
    return 0

def _parse_date_from_text(text: str) -> str:
    # Einfacher Platzhalter: heutiges Datum
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def _estimate_repair_costs(beschreibung: str, reparaturkosten_dict: dict) -> int:
    # Sehr einfache Heuristik: keine Beschreibung, daher 0
    # Kann bei Bedarf erweitert werden
    kosten = 0
    beschreibung_lower = beschreibung.lower()
    for defekt, preis in reparaturkosten_dict.items():
        if defekt.lower() in beschreibung_lower:
            kosten += preis
    return kosten
