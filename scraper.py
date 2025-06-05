# scraper.py

from playwright.sync_api import sync_playwright
import re
import time
from db import save_advert, get_existing_advert
from datetime import datetime

def scrape_ads(modell, min_price=None, max_price=None, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
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
                    title = card.query_selector("a.ellipsis").inner_text().strip() if card.query_selector("a.ellipsis") else "Kein Titel"
                    description = card.query_selector("p.aditem-main--middle--description").inner_text().strip() if card.query_selector("p.aditem-main--middle--description") else ""
                    price_text = card.query_selector("p.aditem-main--middle--price-shipping--price")
                    price_raw = price_text.inner_text().strip() if price_text else "0"
                    price = int(re.sub(r"[^\d]", "", price_raw)) if price_raw else 0
                    link = "https://www.kleinanzeigen.de" + card.query_selector("a.ellipsis").get_attribute("href") if card.query_selector("a.ellipsis") else ""
                    image = card.query_selector("img").get_attribute("src") if card.query_selector("img") else ""
                    card_text = card.inner_text().lower()
                    versand = any(word in card_text for word in ["versand", "shipping", "versenden"])

                    if nur_versand and not versand:
                        continue

                    # Preisfilter beachten
                    if min_price and price < min_price:
                        continue
                    if max_price and price > max_price:
                        continue

                    # Check, ob Anzeige bereits gespeichert ist
                    bestehende = get_existing_advert(link)
                    jetzt = datetime.utcnow().isoformat()

                    if bestehende:
                        save_advert(
                            title=title,
                            price=price,
                            link=link,
                            image=image,
                            beschreibung=description,
                            versand=versand,
                            modell=modell,
                            erfasst_am=bestehende["erfasst_am"],
                            zuletzt_aktualisiert=jetzt
                        )
                    else:
                        save_advert(
                            title=title,
                            price=price,
                            link=link,
                            image=image,
                            beschreibung=description,
                            versand=versand,
                            modell=modell,
                            erfasst_am=jetzt,
                            zuletzt_aktualisiert=jetzt
                        )

                    results.append({
                        "title": title,
                        "price": price,
                        "link": link,
                        "image": image,
                        "beschreibung": description,
                        "versand": versand
                    })

                except Exception as e:
                    print(f"❌ Fehler bei Anzeige: {e}")
                    continue

        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Seite: {e}")
        finally:
            browser.close()

    return results
