from playwright.sync_api import sync_playwright
import re

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
                title_elem = card.query_selector("h2")
                price_elem = card.query_selector("p.aditem-main--middle--price")
                img_elem = card.query_selector("img")
                link_elem = card.query_selector("a")

                if not title_elem or not price_elem:
                    continue

                title = title_elem.inner_text().strip()
                raw_price = price_elem.inner_text().strip()
                clean_price = re.sub(r"[^\d]", "", raw_price)
                price = int(clean_price) if clean_price else 0

                if min_price and price < min_price:
                    continue
                if max_price and price > max_price:
                    continue

                text = card.inner_text().lower()
                if nur_versand and not any(x in text for x in ["versand", "versenden", "shipping"]):
                    continue

                results.append({
                    "title": title,
                    "price": price,
                    "image": img_elem.get_attribute("src") if img_elem else "",
                    "link": "https://www.kleinanzeigen.de" + link_elem.get_attribute("href") if link_elem else ""
                })
        except Exception as e:
            print(f"❌ Fehler: {e}")
        finally:
            browser.close()

    return results
