# scraper.py

from playwright.sync_api import sync_playwright
from datetime import datetime
import re
import sqlite3

DB_PATH = "anzeigen.db"

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
            page.wait_for_selector("article.aditem", timeout=15000)
            cards = page.query_selector_all("article.aditem")

            for card in cards:
                try:
                    title = card.query_selector("a.ellipsis").inner_text().strip()
                    link = "https://www.kleinanzeigen.de" + card.query_selector("a.ellipsis").get_attribute("href")
                    image = card.query_selector("img").get_attribute("src") if card.query_selector("img") else ""
                    beschreibung = card.inner_text().strip()
                    
                    price_elem = card.query_selector("p.aditem-main--middle--price-shipping--price") or card.query_selector("p.aditem-main--middle--price")
                    raw_price = price_elem.inner_text().strip() if price_elem else ""
                    price_clean = re.sub(r"[^\d]", "", raw_price)
                    price = int(price_clean) if price_clean else 0

                    versand = "versand" in beschreibung.lower()

                    if nur_versand and not versand:
                        continue
                    if min_price and price < min_price:
                        continue
                    if max_price and price > max_price:
                        continue

                    eintrag = {
                        "title": title,
                        "price": price,
                        "link": link,
                        "image": image,
                        "beschreibung": beschreibung,
                        "versand": versand,
                        "erstellt_am": datetime.now().strftime("%Y-%m-%d"),
                        "aktualisiert_am": datetime.now().strftime("%Y-%m-%d")
                    }

                    results.append(eintrag)

                except Exception as e:
                    print(f"Fehler bei Anzeige: {e}")
                    continue

        except Exception as e:
            print(f"Scrape-Fehler: {e}")
        finally:
            browser.close()

    return results