from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re
import time

def scrape_ads(
    modell,
    min_price=0,
    max_price=1500,
    nur_versand=False,
    debug=False,
    config=None,
    log=None
):
    """
    Scrape Kleinanzeigen based on parameters.

    Args:
        modell (str): Modellbezeichnung (z.B. 'iPhone 14 Pro')
        min_price (int): Mindestpreis
        max_price (int): Maximalpreis
        nur_versand (bool): Nur Angebote mit Versand
        debug (bool): Debug-Ausgaben aktivieren
        config (dict): Bewertungskonfiguration (optional)
        log (callable): Funktion zum Loggen von Debug-Text (optional)

    Returns:
        list of dict: Gefundene Anzeigen
    """
    def _log(msg):
        if debug:
            prefix = "[scrape_ads]"
            message = f"{prefix} {msg}"
            if log:
                log(message)
            else:
                print(message)

    # Kategorie festlegen (optional anpassbar)
    # "s-handy-telekom" ist Kategorie für Handys/Telekommunikation
    kategorie = "s-handy-telekom"

    # Modell für URL anpassen: Kleinbuchstaben, Bindestriche statt Leerzeichen
    modell_url = modell.lower().replace(" ", "-")

    # Preisbereich für URL: kleinanzeigen nutzt ':' als Trennung, kein '-'
    preis_filter = f"preis:{min_price}:{max_price}"

    # Angebotsfilter: nur Angebote
    angebots_filter = "anzeige:angebote"

    # Versandfilter
    versand_filter = ""
    if nur_versand:
        # Filter-Suffix bei Versand nur in Kombination mit Kategorie (bzw. im Pfad)
        # Beispiel: k0c173+handy_telekom.versand_s:ja
        # Hier k0 ist Paginierung?  c173+handy_telekom.versand_s:ja  ist Filter
        versand_filter = "c173+handy_telekom.versand_s:ja"

    # Paginierung Start (k0 = Seite 0)
    pagination = "k0"

    # Baue URL zusammen
    # Basis
    base_url = "https://www.kleinanzeigen.de/"

    # Pfad zusammenbauen
    # Falls Versandfilter gesetzt, hänge diesen an Pagination an
    if versand_filter:
        pagination += versand_filter

    url = (
        f"{base_url}"
        f"{kategorie}/"
        f"{angebots_filter}/"
        f"{preis_filter}/"
        f"{modell_url}/"
        f"{pagination}"
    )

    _log(f"Starte Suche nach '{modell}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}")
    _log(f"URL: {url}")

    ads = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            page.goto(url)
            # Warte bis Anzeigen-Liste sichtbar ist (li.ad-listitem)
            try:
                page.wait_for_selector("li.ad-listitem", timeout=10000)
            except PlaywrightTimeoutError:
                _log("Seite geladen: Fehler | 404 oder keine Anzeigen gefunden")
                return ads

            # Anzeigen auslesen
            ad_elements = page.query_selector_all("li.ad-listitem")

            _log(f"{len(ad_elements)} Anzeigen auf der Seite gefunden")

            for ad in ad_elements:
                # Extrahiere Details
                try:
                    title = ad.query_selector("a.ellipsis").inner_text().strip()
                    link = ad.query_selector("a.ellipsis").get_attribute("href")
                    # Links sind relativ, daher basis-url ergänzen
                    if link and not link.startswith("http"):
                        link = base_url.rstrip("/") + link

                    price_text = ad.query_selector("p.aditem-main--middle--price-shipping").inner_text().strip()
                    # Preis extrahieren, z.B. "350 €"
                    price_match = re.search(r"(\d+[\.,]?\d*)\s*€", price_text)
                    price = float(price_match.group(1).replace(",", ".")) if price_match else 0

                    image_el = ad.query_selector("img")
                    image = image_el.get_attribute("src") if image_el else ""

                    created_at = ad.query_selector("time").get_attribute("datetime") if ad.query_selector("time") else ""

                    # Versandinfo prüfen
                    versand_text = ad.query_selector("p.aditem-main--middle--shipping").inner_text().strip() if ad.query_selector("p.aditem-main--middle--shipping") else ""
                    versand = "Versand" in versand_text

                    # Platzhalter Beschreibung, da Detailseite extra geladen werden müsste (für Performance erstmal leer)
                    beschreibung = ""

                    # Reparaturkosten initial 0, können später gesetzt werden
                    reparaturkosten = 0

                    ads.append({
                        "title": title,
                        "link": link,
                        "price": price,
                        "image": image,
                        "created_at": created_at,
                        "updated_at": created_at,
                        "versand": versand,
                        "beschreibung": beschreibung,
                        "reparaturkosten": reparaturkosten,
                    })

                except Exception as e:
                    _log(f"Fehler beim Verarbeiten einer Anzeige: {e}")

            browser.close()

    except Exception as e:
        _log(f"Fehler beim Abruf der Seite: {e}")

    _log(f"Fertig, {len(ads)} Anzeigen zurückgegeben")
    return ads
