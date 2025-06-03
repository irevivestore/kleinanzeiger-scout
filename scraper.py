# scraper.py

from playwright.sync_api import sync_playwright
import re

# Konfiguration
VERKAUFSPREIS = 500
WUNSCH_MARGE = 120
REPARATURKOSTEN = {
    "display": 80,
    "akku": 30,
    "backcover": 60,
    "kamera": 100,
    "lautsprecher": 60,
    "mikrofon": 50,
    "face id": 80,
    "wasserschaden": 250,
    "kein bild": 80,
    "defekt": 0,
}

def scrape_ads(modell, min_price=None, max_price=None, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector("article.aditem", timeout=10000)
            cards = page.query_selector_all("article.aditem")

            for card in cards:
                try:
                    title = card.query_selector("h2").inner_text().strip()
                    price_text = card.query_selector("p.aditem-main--middle--price-shipping--price")
                    price_raw = price_text.inner_text().strip() if price_text else "0"
                    price_clean = re.sub(r"[^\d]", "", price_raw)
                    price = int(price_clean) if price_clean.isdigit() else 0

                    if min_price and price < min_price:
                        continue
                    if max_price and price > max_price:
                        continue

                    description = card.inner_text().lower()
                    versand = any(w in description for w in ["versand", "versenden", "shipping"])
                    if nur_versand and not versand:
                        continue

                    link_tag = card.query_selector("a.ellipsis")
                    link = "https://www.kleinanzeigen.de" + link_tag.get_attribute("href") if link_tag else ""

                    image_tag = card.query_selector("img")
                    image = image_tag.get_attribute("src") if image_tag else ""

                    # 💬 Vollständige Beschreibung von der Detailseite abrufen
                    if link:
                        try:
                            detail_page = context.new_page()
                            detail_page.goto(link, timeout=10000)
                            detail_page.wait_for_selector("p[itemprop='description']", timeout=5000)
                            beschreibung = detail_page.locator("p[itemprop='description']").inner_text().strip()
                            detail_page.close()
                        except:
                            beschreibung = "❌ Konnte vollständige Beschreibung nicht laden"
                    else:
                        beschreibung = "Keine Beschreibung"

                    # Bewertung berechnen
                    reparaturkosten = 0
                    max_ek = VERKAUFSPREIS - reparaturkosten - WUNSCH_MARGE

                    if price <= max_ek:
                        bewertung = "gruen"
                    elif price <= VERKAUFSPREIS - reparaturkosten - (WUNSCH_MARGE * 0.9):
                        bewertung = "blau"
                    else:
                        bewertung = "rot"

                    results.append({
                        "title": title,
                        "price": price,
                        "link": link,
                        "image": image,
                        "versand": versand,
                        "beschreibung": beschreibung,
                        "reparaturkosten": reparaturkosten,
                        "max_ek": max_ek,
                        "bewertung": bewertung,
                    })

                except Exception as e:
                    print(f"Fehler bei Anzeige: {str(e)}")
                    continue

        except Exception as e:
            print(f"❌ Hauptfehler beim Laden der Seite: {str(e)}")
        finally:
            browser.close()

    return results

# Diese Konstanten werden von app.py importiert
__all__ = ["scrape_ads", "REPARATURKOSTEN", "VERKAUFSPREIS", "WUNSCH_MARGE"]
