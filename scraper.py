from playwright.sync_api import sync_playwright
import re
from datetime import datetime

def scrape_ads(modell, min_price=None, max_price=None, nur_versand=False, config=None, debug=False):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    debug_logs = []

    if min_price is not None and max_price is not None:
        url = f"https://www.kleinanzeigen.de/s-preis:{int(min_price)}:{int(max_price)}/{keyword}/k0"

    if debug:
        debug_logs.append(f"🔍 Starte Scraping: {url}")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            if debug:
                debug_logs.append("✅ Seite geladen")

            page.wait_for_selector("article.aditem", timeout=15000)
            cards = page.query_selector_all("article.aditem")
            if debug:
                debug_logs.append(f"📦 Gefundene Anzeigen insgesamt: {len(cards)}")

            for idx, card in enumerate(cards):
                try:
                    title_elem = card.query_selector("a.ellipsis")
                    if not title_elem:
                        continue

                    title = title_elem.inner_text().strip()

                    price_elem = card.query_selector("p.aditem-main--middle--price-shipping--price")
                    if not price_elem:
                        continue

                    raw_price = price_elem.inner_text().strip()
                    price_clean = re.sub(r"[^\d,]", "", raw_price).replace(",", ".")
                    try:
                        price = float(price_clean)
                    except ValueError:
                        if debug:
                            debug_logs.append(f"⚠️ Preis-Parsing-Fehler bei '{raw_price}'")
                        continue

                    description_elem = card.query_selector("p.aditem-main--middle--description")
                    description = description_elem.inner_text().strip() if description_elem else ""

                    versand = "versand" in description.lower()

                    if nur_versand and not versand:
                        continue

                    image_elem = card.query_selector("img")
                    image = image_elem.get_attribute("src") if image_elem else ""

                    link = "https://www.kleinanzeigen.de" + title_elem.get_attribute("href")

                    # Reparaturkosten berechnen
                    reparaturkosten = 0
                    if config and "reparaturkosten" in config:
                        for defekt, kosten in config["reparaturkosten"].items():
                            if defekt.lower() in description.lower():
                                reparaturkosten += kosten

                    verkaufspreis = config.get("verkaufspreis", 0)
                    wunsch_marge = config.get("wunsch_marge", 0)
                    max_ek = verkaufspreis - wunsch_marge - reparaturkosten

                    bewertung = (
                        "gruen" if price <= max_ek else
                        "blau" if price <= verkaufspreis - reparaturkosten - (wunsch_marge * 0.9)
                        else "rot"
                    )

                    results.append({
                        "title": title,
                        "price": price,
                        "beschreibung": description,
                        "versand": versand,
                        "image": image,
                        "link": link,
                        "reparaturkosten": reparaturkosten,
                        "max_ek": max_ek,
                        "bewertung": bewertung,
                        "gefunden_am": datetime.now().strftime("%Y-%m-%d"),
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                except Exception as e:
                    if debug:
                        debug_logs.append(f"⚠️ Fehler bei Anzeige {idx}: {str(e)}")
                    continue

        except Exception as e:
            if debug:
                debug_logs.append(f"❌ Fehler beim Laden der Seite: {str(e)}")
        finally:
            browser.close()

    if debug:
        debug_logs.append(f"✅ Scraping abgeschlossen – {len(results)} gültige Ergebnisse")

    return results, debug_logs
