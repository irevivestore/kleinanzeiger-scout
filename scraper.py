# scraper.py
from playwright.sync_api import sync_playwright
import re

def scrape_ads(modell, min_price=None, max_price=None, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()
    base_url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    if min_price and max_price:
        base_url = f"https://www.kleinanzeigen.de/s-preis:{min_price}:{max_price}/{keyword}/k0"

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(base_url, timeout=60000)
            page.wait_for_selector("article.aditem", timeout=15000)
            ads = page.query_selector_all("article.aditem")

            for ad in ads:
                try:
                    # Titel
                    title_elem = ad.query_selector("a.ellipsis")
                    title = title_elem.inner_text().strip() if title_elem else "Unbekannt"

                    # Preis
                    price_elem = ad.query_selector("p.aditem-main--middle--price-shipping--price")
                    if price_elem:
                        price_text = price_elem.inner_text().strip()
                        price_clean = re.sub(r"[^\d]", "", price_text)
                        price = int(price_clean) if price_clean else 0
                    else:
                        price = 0

                    # Link
                    href = title_elem.get_attribute("href") if title_elem else ""
                    link = f"https://www.kleinanzeigen.de{href}"

                    # ID aus Link
                    ad_id = href.split("/")[-1].split("-")[0] if href else ""

                    # Bild
                    img_elem = ad.query_selector("img")
                    image = img_elem.get_attribute("src") if img_elem else ""

                    # Versand
                    text = ad.inner_text().lower()
                    versand = any(v in text for v in ["versand", "shipping", "versenden"])

                    # Beschreibung (ausklappbar)
                    desc_elem = ad.query_selector("p.aditem-main--middle--description")
                    beschreibung = desc_elem.inner_text().strip() if desc_elem else ""

                    results.append({
                        "id": ad_id,
                        "modell": modell,
                        "title": title,
                        "price": price,
                        "link": link,
                        "image": image,
                        "versand": versand,
                        "beschreibung": beschreibung
                    })
                except Exception as e:
                    print(f"⚠️ Fehler beim Parsen einer Anzeige: {e}")
                    continue

        except Exception as e:
            print(f"❌ Fehler beim Scraping: {e}")
        finally:
            browser.close()

    return results
