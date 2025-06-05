from playwright.sync_api import sync_playwright
import re
from datetime import datetime
import hashlib

def scrape_ads(modell, min_price=None, max_price=None, nur_versand=False, debug=False, config=None):
    keyword = modell.replace(" ", "-").lower()
    base_url = "https://www.kleinanzeigen.de"
    url = f"{base_url}/s-{keyword}/k0"

    if min_price is not None and max_price is not None:
        url = f"{base_url}/s-preis:{int(min_price)}:{int(max_price)}/{keyword}/k0"

    results = []

    if debug:
        print(f"🔍 Starte Scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            if debug:
                print("🌐 Lade Seite...")
            page.goto(url, timeout=60000)

            if debug:
                print("✅ Seite geladen")

            if debug:
                print("⏳ Warte auf Anzeigen-Container...")
            page.wait_for_selector("article.aditem", timeout=30000)

            cards = page.query_selector_all("article.aditem")

            if debug:
                print(f"📦 Gefundene Anzeigen: {len(cards)}")

            for idx, card in enumerate(cards):
                try:
                    title_elem = card.query_selector("a.ellipsis")
                    title = title_elem.inner_text().strip() if title_elem else "Kein Titel"

                    price_elem = card.query_selector("p.aditem-main--middle--price-shipping--price")
                    raw_price = price_elem.inner_text().strip() if price_elem else "0"
                    price_clean = re.sub(r"[^\d,.]", "", raw_price).replace(",", ".")
                    try:
                        price = float(price_clean)
                    except ValueError:
                        price = 0.0
                        if debug:
                            print(f"⚠️ Preis-Parsing-Fehler bei Anzeige {idx}: '{raw_price}'")

                    description_elem = card.query_selector("p.aditem-main--middle--description")
                    description = description_elem.inner_text().strip() if description_elem else ""

                    versand = "versand" in description.lower()
                    if nur_versand and not versand:
                        if debug:
                            print(f"ℹ️ Anzeige {idx} übersprungen, kein Versand")
                        continue

                    image_elem = card.query_selector("img")
                    image = image_elem.get_attribute("src") if image_elem else ""

                    link_elem = card.query_selector("a.ellipsis")
                    relative_link = link_elem.get_attribute("href") if link_elem else ""
                    link = base_url + relative_link

                    anzeige_id = hashlib.md5(link.encode()).hexdigest()

                    reparaturkosten = 0
                    if config:
                        for defekt, kosten in config.get("reparaturkosten", {}).items():
                            if defekt in description.lower():
                                reparaturkosten += kosten

                    max_ek = 0
                    bewertung = "rot"
                    if config:
                        max_ek = config.get("verkaufspreis", 0) - config.get("wunsch_marge", 0) - reparaturkosten
                        if price <= max_ek:
                            bewertung = "gruen"
                        elif price <= config.get("verkaufspreis", 0) - reparaturkosten - (config.get("wunsch_marge", 0) * 0.9):
                            bewertung = "blau"

                    results.append({
                        "id": anzeige_id,
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

                    if debug:
                        print(f"✅ Anzeige {idx} hinzugefügt: {title} | Preis: {price} € | Versand: {versand}")

                except Exception as e:
                    if debug:
                        print(f"⚠️ Fehler bei Anzeige {idx}: {e}")

        except Exception as e:
            if debug:
                print(f"❌ Hauptfehler beim Laden der Seite: {e}")

        finally:
            browser.close()
            if debug:
                print("🛑 Browser geschlossen")

    if debug:
        print(f"✅ Scraping abgeschlossen – {len(results)} Ergebnisse")

    return results
