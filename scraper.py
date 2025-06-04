# scraper.py

from playwright.sync_api import sync_playwright
import re

# Bewertungsparameter
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
    "defekt": 0
}

def scrape_ads(modell, min_price=0, max_price=10000, nur_versand=False, debug=False):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-preis:{min_price}:{max_price}/{keyword}/k0"
    if debug:
        print(f"[DEBUG] URL: {url}")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector("article.aditem", timeout=10000)
            cards = page.query_selector_all("article.aditem")

            for card in cards:
                try:
                    title = card.query_selector("a.ellipsis").inner_text().strip()
                    preis_element = card.query_selector("p.aditem-main--middle--price-shipping--price")
                    preis_text = preis_element.inner_text().strip() if preis_element else "0"
                    preis_clean = re.sub(r"[^\d,]", "", preis_text).replace(",", ".")
                    preis = float(preis_clean) if preis_clean else 0.0

                    beschreibung_element = card.query_selector("p.aditem-main--middle--description")
                    beschreibung = beschreibung_element.inner_text().strip() if beschreibung_element else ""

                    versand = "versand" in card.inner_text().lower()
                    if nur_versand and not versand:
                        continue

                    bild = card.query_selector("img")
                    bild_url = bild.get_attribute("src") if bild else ""
                    link = "https://www.kleinanzeigen.de" + card.query_selector("a.ellipsis").get_attribute("href")

                    # Standardbewertung
                    defekte = []
                    reparatur_summe = 0
                    max_ek = VERKAUFSPREIS - reparatur_summe - WUNSCH_MARGE
                    bewertung = (
                        "gruen" if preis <= max_ek else
                        "blau" if preis <= VERKAUFSPREIS - reparatur_summe - (WUNSCH_MARGE * 0.9) else
                        "rot"
                    )

                    results.append({
                        "title": title,
                        "price": preis,
                        "beschreibung": beschreibung,
                        "versand": versand,
                        "image": bild_url,
                        "link": link,
                        "reparaturkosten": reparatur_summe,
                        "max_ek": max_ek,
                        "bewertung": bewertung
                    })

                except Exception as e:
                    if debug:
                        print(f"[DEBUG] Fehler bei Anzeige: {e}")

        except Exception as e:
            if debug:
                print(f"[DEBUG] Fehler beim Seitenabruf: {e}")

        finally:
            browser.close()

    return results

# Export der Konstanten für die App
__all__ = ["scrape_ads", "REPARATURKOSTEN", "VERKAUFSPREIS", "WUNSCH_MARGE"]