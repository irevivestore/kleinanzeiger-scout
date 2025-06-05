from playwright.sync_api import sync_playwright
import re
from datetime import datetime

def scrape_ads(modell, min_price=None, max_price=None, nur_versand=False, config=None, debug=False):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    if min_price and max_price:
        url = f"https://www.kleinanzeigen.de/s-preis:{int(min_price)}:{int(max_price)}/{keyword}/k0"

    if debug:
        print(f"🔍 Starte Scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            if debug:
                print("✅ Seite geladen")

            page.wait_for_selector("article.aditem", timeout=15000)
            cards = page.query_selector_all("article.aditem")
            if debug:
                print(f"📦 Gefundene Anzeigen: {len(cards)}")

            for idx, card in enumerate(cards):
                try:
                    title = card.query_selector("a.ellipsis").inner_text().strip()
                    price_elem = card.query_selector("p.aditem-main--middle--price-shipping--price")
                    price = 0.0

                    if price_elem:
                        raw_price = price_elem.inner_text().strip()
                        price_clean = re.sub(r"[^\d,.]", "", raw_price).replace(",", ".")
                        try:
                            price = float(price_clean)
                        except ValueError:
                            if debug:
                                print(f"⚠️ Preis-Parsing-Fehler: {raw_price}")

                    description_elem = card.query_selector("p.aditem-main--middle--description")
                    description = description_elem.inner_text().strip() if description_elem else ""

                    versand = "versand" in description.lower()

                    image_elem = card.query_selector("img")
                    image = image_elem.get_attribute("src") if image_elem else ""

                    link_elem = card.query_selector("a.ellipsis")
                    link = "https://www.kleinanzeigen.de" + link_elem.get_attribute("href") if link_elem else ""

                    reparaturkosten = 0
                    if config:
                        for defekt, kosten in config["reparaturkosten"].items():
                            if defekt in description.lower():
                                reparaturkosten += kosten

                    max_ek = config["verkaufspreis"] - config["wunsch_marge"] - reparaturkosten

                    bewertung = (
                        "gruen" if price <= max_ek else
                        "blau" if price <= config["verkaufspreis"] - reparaturkosten - (config["wunsch_marge"] * 0.9)
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
                        print(f"⚠️ Fehler bei Anzeige {idx}: {str(e)}")
                    continue

        except Exception as e:
            if debug:
                print(f"❌ Hauptfehler: {str(e)}")
        finally:
            browser.close()

    if debug:
        print(f"✅ Scraping abgeschlossen – {len(results)} Ergebnisse")

    return results