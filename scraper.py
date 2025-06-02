from playwright.sync_api import sync_playwright
import re
import time

def scrape_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        # Browser mit langsamerer Ausführung starten (simuliert menschliches Verhalten)
        browser = p.chromium.launch(
            headless=True,
            slow_mo=100  # Verlangsamt die Ausführung um 100ms pro Aktion
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 1024}
        )
        page = context.new_page()

        try:
            # Seite mit vollständigem Load und Netzwerk-Idle aufrufen
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Scrollen um Lazy Loading zu triggern
            for _ in range(3):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                time.sleep(1)  # Wartezeit zwischen Scrolls
            
            # Direkt mit Playwright die Elemente finden (ohne BeautifulSoup)
            ads = page.query_selector_all("article.aditem")
            
            for ad in ads[:10]:  # Begrenzung auf 10 Anzeigen
                try:
                    # Titel extrahieren
                    title_element = ad.query_selector("h2")
                    title = title_element.inner_text().strip() if title_element else "Kein Titel"
                    
                    # Preis extrahieren - mehrere Versuche mit verschiedenen Selektoren
                    price = 0.0
                    price_selectors = [
                        "p.aditem-main--middle--price",
                        "p.aditem-main--middle--price-shipping",
                        "div.aditem-main--middle--price"
                    ]
                    
                    for selector in price_selectors:
                        price_element = ad.query_selector(selector)
                        if price_element:
                            price_text = price_element.inner_text().strip()
                            if "VB" in price_text:  # Fall "Verhandlungsbasis"
                                price = -1.0
                            else:
                                price_match = re.search(r"[\d,.]+", price_text)
                                if price_match:
                                    price_str = price_match.group(0).replace(".", "").replace(",", ".")
                                    try:
                                        price = float(price_str)
                                    except ValueError:
                                        pass
                            if price != 0.0:
                                break
                    
                    # Link extrahieren
                    link_element = ad.query_selector("a.ellipsis")
                    link = "https://www.kleinanzeigen.de" + link_element.get_attribute("href") if link_element else ""
                    
                    # Bild-URL extrahieren
                    img_element = ad.query_selector("img")
                    img = img_element.get_attribute("src") if img_element else ""
                    
                    results.append({
                        "title": title,
                        "price": price,
                        "link": link,
                        "image": img
                    })
                    
                except Exception as e:
                    print(f"Fehler bei Anzeige: {e}")
                    continue
                    
        finally:
            context.close()
            browser.close()
    
    return results
