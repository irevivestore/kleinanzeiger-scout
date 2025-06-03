# scraper.py

from playwright.sync_api import sync_playwright
import re

def scrape_ads(modell, min_price=None, max_price=None, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()

    # URL mit optionalem Preisfilter
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

            for index, ad in enumerate(ads[:20]):  # bis zu 20 Anzeigen
                try:
                    # Titel
                    title_elem = ad.query_selector("a.ellipsis")
                    title = title_elem.inner_text().strip() if title_elem else "Kein Titel"

                    # Preis
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

                    # Versandprüfung
                    description_text = ad.inner_text().lower()
                    versand = any(term in description_text for term in ["versand", "shipping", "versenden"])
                    if nur_versand and not versand:
                        continue

                    # Link zur Anzeige
                    link_elem = ad.query_selector("a.ellipsis")
                    href = link_elem.get_attribute("href") if link_elem else ""
                    link = f"https://www.kleinanzeigen.de{href}"

                    # Bild
                    img_elem = ad.query_selector("img")
                    img_url = img_elem.get_attribute("src") if img_elem else ""

                    # Ergebnis speichern
                    results.append({
                        "title": title,
                        "price": price,
                        "link": link,
                        "image": img_url,
                        "versand": versand
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
