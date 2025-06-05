from playwright.sync_api import sync_playwright

def scrape_ads(modell, min_price=0, max_price=1500, nur_versand=False, nur_angebote=True, debug=False, config=None, log=None):
    if log is None:
        log = print

    log(f"[scrape_ads] Starte Suche nach '{modell}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")

    modell_url = modell.lower().replace(" ", "-")

    base_url = "https://www.kleinanzeigen.de"

    # Kategorie: Handy & Telekom (wie du vorgeschlagen hast)
    kategorie = "s-handy-telekom"

    # Preisfilter in URL: preis:min:max
    preis_filter = f"preis:{min_price}:{max_price}"

    # Angebote oder keine Filter
    if nur_angebote:
        angebote_filter = "anzeige:angebote"
    else:
        angebote_filter = ""

    # Versandfilter in URL
    versand_filter = ""
    if nur_versand:
        # Filter für Versand aktivieren
        versand_filter = "versand_s:ja"

    # Konstruiere URL Bestandteile für Filter, nur diejenigen, die nicht leer sind
    filter_teile = [kategorie]
    if angebote_filter:
        filter_teile.append(angebote_filter)
    filter_teile.append(preis_filter)
    filter_teile.append(modell_url)
    if versand_filter:
        filter_teile.append(versand_filter)

    url = base_url + "/s-" + "/".join(filter_teile) + "/k0"

    log(f"[scrape_ads] URL: {url}")

    ergebnisse = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url, timeout=15000)
            page.wait_for_selector("li.ad-listitem", timeout=10000)
            log(f"[scrape_ads] Seite geladen, Anzeigen werden extrahiert...")

            ads = page.query_selector_all("li.ad-listitem")
            log(f"[scrape_ads] {len(ads)} Anzeigen gefunden.")

            for ad in ads:
                try:
                    title = ad.query_selector("a.ellipsis").inner_text().strip()
                    price_str = ad.query_selector("p.price").inner_text().strip()
                    # Preis aus String extrahieren, z.B. "200 €"
                    price = int(''.join(filter(str.isdigit, price_str)))
                    image = ad.query_selector("img").get_attribute("src")
                    link = base_url + ad.query_selector("a.ellipsis").get_attribute("href")
                    versand = "versand_s:ja" in url
                    created_at = updated_at = "unbekannt"  # Für einfaches Beispiel

                    # Einfaches Beispiel für Beschreibung (kann erweitert werden)
                    beschreibung = title

                    ergebnisse.append({
                        "title": title,
                        "price": price,
                        "image": image,
                        "link": link,
                        "versand": versand,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "beschreibung": beschreibung,
                        "reparaturkosten": 0,  # später berechnen
                    })

                except Exception as e:
                    log(f"[scrape_ads] Fehler beim Parsen einer Anzeige: {e}")

        except Exception as e:
            log(f"[scrape_ads] Fehler beim Abruf der Seite: {e}")
        finally:
            context.close()
            browser.close()

    log(f"[scrape_ads] Fertig, {len(ergebnisse)} Anzeigen zurückgegeben")

    return ergebnisse
