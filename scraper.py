from playwright.sync_api import sync_playwright
import re

def scrape_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Browser wie ein menschlicher Nutzer konfigurieren
        page.set_viewport_size({"width": 1280, "height": 800})
        page.set_extra_http_headers({
            "Accept-Language": "de-DE,de;q=0.9"
        })

        try:
            # Seite aufrufen und auf Inhalte warten
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("article.aditem", timeout=15000)

            # Durch alle Anzeigen-Elemente iterieren
            ads = page.query_selector_all("article.aditem")
            for ad in ads[:15]:  # Erste 15 Anzeigen
                try:
                    # Titel extrahieren
                    title_element = ad.query_selector("a.ellipsis")
                    title = title_element.inner_text().strip() if title_element else "Kein Titel"
                    
                    # Link extrahieren
                    relative_link = title_element.get_attribute("href") if title_element else ""
                    link = f"https://www.kleinanzeigen.de{relative_link}" if relative_link else ""

                    # Preis-Extraktion mit robusten Selektoren
                    price = 0.0
                    price_element = ad.query_selector("p.aditem-main--middle--price, .price, [class*='price']")
                    
                    if price_element:
                        price
