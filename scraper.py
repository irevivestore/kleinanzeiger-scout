# scraper.py

from playwright.sync_api import sync_playwright
import re

# Bewertungsparameter (diese kannst du später anpassen oder über die UI konfigurieren)
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

# Funktion zur Bewertung basierend auf Beschreibung und aktiven Defekt-Checkboxen
def bewerte_anzeige(beschreibung, manuelle_defekte=None):
    gesamt_reparatur = 0
    beschreibung = beschreibung.lower()
    defekte = REPARATURKOSTEN.keys()
    for defekt in defekte:
        if (manuelle_defekte and defekt in manuelle_defekte) or defekt in beschreibung:
            gesamt_reparatur += REPARATURKOSTEN[defekt]
    return gesamt_reparatur

def scrape_ads(modell, min_price=None, max_price=None, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()

    if min_price is not None and max_price is not None:
        url = f"https://www.kleinanzeigen.de/s-preis:{int(min_price)}:{int(max_price)}/{keyword}/k0"
    else:
        url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("article.aditem", timeout=15000)
            ads = page.query_selector_all("article.aditem")

            for index, ad in enumerate(ads[:20]):
                try:
                    title_elem = ad.query_selector("a.ellipsis")
                    title = title_elem.inner_text().strip() if title_elem else "Kein Titel"

                    price_elem = ad.query_selector("p.aditem-main--middle--price-shipping--price")
                    if price_elem:
                        price_raw = price_elem.inner_text().strip()
                        price_clean = re.sub(r"[^\d,]", "", price_raw).replace(",", ".")
                        try:
                            price = float(price_clean)
                        except ValueError:
                            price = 0.0
                    else:
                        price = 0.0

                    description_text = ad.inner_text().lower()
                    versand = any(term in description_text for term in ["versand", "shipping", "versenden"])
                    if nur_versand and not versand:
                        continue

                    reparatur = bewerte_anzeige(description_text)
                    max_ek = VERKAUFSPREIS - reparatur - WUNSCH_MARGE
                    bewertung = "gruen" if price <= max_ek else ("blau" if price <= VERKAUFSPREIS - reparatur - (WUNSCH_MARGE * 0.9) else "rot")

                    link_elem = ad.query_selector("a.ellipsis")
                    href = link_elem.get_attribute("href") if link_elem else ""
                    link = f"https://www.kleinanzeigen.de{href}"

                    img_elem = ad.query_selector("img")
                    img_url = img_elem.get_attribute("src") if img_elem else ""

                    results.append({
                        "title": title,
                        "price": price,
                        "link": link,
                        "image": img_url,
                        "versand": versand,
                        "beschreibung": description_text,
                        "reparaturkosten": reparatur,
                        "max_ek": max_ek,
                        "bewertung": bewertung,
                        "manuelle_defekte": []
                    })

                except Exception as inner_e:
                    print(f"⚠️ Fehler beim Verarbeiten der Anzeige {index + 1}: {inner_e}")
                    continue

        except Exception as e:
            print(f"❌ Fehler beim Seitenabruf: {e}")

        finally:
            context.close()
            browser.close()

    return results
