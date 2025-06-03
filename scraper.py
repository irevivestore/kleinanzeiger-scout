from playwright.sync_api import sync_playwright

def get_prices_only(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    prices = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector("article.aditem", timeout=10000)
            cards = page.query_selector_all("article.aditem")

            for card in cards:
                price_elem = card.query_selector("p.aditem-main--middle--price")
                if price_elem:
                    raw_price = price_elem.inner_text().strip()
                    clean = ''.join(c for c in raw_price if c.isdigit() or c in ',.')
                    prices.append(clean)
        except Exception as e:
            print(f"FEHLER: {str(e)}")
        finally:
            browser.close()

    return prices
