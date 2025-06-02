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
                price_text = card.select_one("p.aditem-main--middle--price").get_text(strip=True) if card.select_one("p.aditem-main--middle--price") else "0"
                price = int(re.sub(r"[^\d]", "", price_text)) if price_text else 0
                link = "https://www.kleinanzeigen.de" + card.select_one("a")["href"] if card.select_one("a") else ""
                img = card.select_one("img")["src"] if card.select_one("img") else ""
                results.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": img
                })
            except Exception:
                continue
    return results