from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time

def scrape_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        time.sleep(1)
        page.wait_for_selector("article.aditem", timeout=10000)
        html = page.inner_html("body")
        browser.close()

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("article.aditem")

        for card in cards:
            try:
                title = card.select_one("h2").get_text(strip=True) if card.select_one("h2") else "Kein Titel"
                
                # Verbesserte Preis-Extraktion
                price_element = card.select_one("p.aditem-main--middle--price")
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    # Entfernt alle Nicht-Ziffern außer dem Dezimalpunkt
                    price_clean = re.sub(r"[^\d,.]", "", price_text)
                    # Ersetzt Komma durch Punkt für float-Konvertierung
                    price_clean = price_clean.replace(",", ".").replace("€", "")
                    try:
                        price = float(price_clean) if price_clean else 0.0
                    except ValueError:
                        price = 0.0
                else:
                    price = 0.0
                
                link = "https://www.kleinanzeigen.de" + card.select_one("a")["href"] if card.select_one("a") else ""
                img = card.select_one("img")["src"] if card.select_one("img") else ""
                
                results.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": img
                })
            except Exception as e:
                print(f"Fehler bei der Verarbeitung einer Anzeige: {e}")
                continue
    return results
