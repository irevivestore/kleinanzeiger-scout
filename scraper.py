import re
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_ads(config):
    suchbegriff = config.get("suchbegriff", "")
    min_price = config.get("min_price", 0)
    max_price = config.get("max_price", 1500)
    nur_versand = config.get("nur_versand", False)
    nur_angebote = config.get("nur_angebote", True)
    debug = config.get("debug", False)

    print(f"[scrape_ads] Starte Suche nach '{suchbegriff}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")

    base_url = "https://www.kleinanzeigen.de/s/"
    filter_path = ""

    if nur_angebote:
        filter_path += "anzeige:angebote/"
    filter_path += f"preis:{min_price}:{max_price}/"
    suchbegriff_encoded = suchbegriff.replace(" ", "+")
    final_url = f"{base_url}{filter_path}{suchbegriff_encoded}/k0"

    print(f"[scrape_ads] URL: {final_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(final_url)
        page.wait_for_timeout(3000)

        items = page.query_selector_all("article.aditem")

        anzeigen = []
        print(f"[scrape_ads] {len(items)} Anzeigen gefunden.")

        for item in items:
            try:
                title_el = item.query_selector("a.ellipsis")
                title = title_el.inner_text().strip() if title_el else "Unbekannter Titel"

                url_el = item.query_selector("a.ellipsis")
                url = url_el.get_attribute("href") if url_el else None
                full_url = f"https://www.kleinanzeigen.de{url}" if url else None

                preis_el = item.query_selector("p.aditem-main--middle--price-shipping")
                raw_preis = preis_el.inner_text().strip() if preis_el else "0 €"
                preis = parse_price(raw_preis)

                altpreis = extract_alt_price(raw_preis)
                preis_anzeige = format_price_display(preis, altpreis)

                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

                beschreibung = ""
                if full_url:
                    detail_page = browser.new_page()
                    detail_page.goto(full_url)
                    detail_page.wait_for_timeout(1500)
                    desc_el = detail_page.query_selector("p[class*='text-module']")
                    beschreibung = desc_el.inner_text().strip() if desc_el else ""
                    detail_page.close()

                anzeigen.append({
                    "id": extract_id_from_url(full_url),
                    "titel": title,
                    "url": full_url,
                    "preis": preis,
                    "preis_anzeige": preis_anzeige,
                    "beschreibung": beschreibung,
                    "modell": suchbegriff,
                    "zeit_erfasst": timestamp,
                    "zeit_aktualisiert": timestamp,
                })

            except Exception as e:
                if debug:
                    print(f"[scrape_ads] Fehler beim Parsen einer Anzeige: {e}")
                continue

        browser.close()

    print(f"[scrape_ads] Fertig, {len(anzeigen)} Anzeigen zurückgegeben")
    return anzeigen


def parse_price(preis_text):
    match = re.search(r"(\d{2,6})\s?€", preis_text.replace(".", ""))
    if match:
        return int(match.group(1))
    return 0


def extract_alt_price(preis_text):
    match = re.findall(r"(\d{2,6})\s?€?", preis_text.replace(".", ""))
    if len(match) == 2:
        return int(match[1])
    return None


def format_price_display(preis, altpreis=None):
    if altpreis and altpreis != preis:
        return f"{preis} € (~~{altpreis} €~~)"
    return f"{preis} €"


def extract_id_from_url(url):
    if not url:
        return "unbekannt"
    match = re.search(r"/s-anzeige/.*?/(\d+)", url)
    return match.group(1) if match else "unbekannt"
