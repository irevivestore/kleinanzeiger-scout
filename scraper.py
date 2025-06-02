from playwright.sync_api import sync_playwright
import re
import time

def scrape_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 1024}
        )
        page = context.new_page()

        try:
            # Seite mit vollständigem Load aufrufen
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)  # Wartezeit für JavaScript
            
            # Scrollen um Lazy Loading zu triggern
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            # Debug: Screenshot zur Überprüfung
            page.screenshot(path="debug_screenshot.png", full_page=True)
            
            # Alle Anzeigen-Elemente finden
            ads = page.query_selector_all("article.aditem")
            
            for ad in ads[:15]:  # Begrenzung auf 15 Anzeigen
                try:
                    # Titel extrahieren
                    title = ad.query_selector("h2").inner_text().strip()
                    
                    # Preis mit mehreren Methoden extrahieren
                    price = 0.0
                    price_element = None
                    
                    # Methode 1: Standard-Preis-Element
                    price_element = ad.query_selector("p.aditem-main--middle--price")
                    
                    # Methode 2: Alternative Preis-Elemente
                    if not price_element:
                        price_element = ad.query_selector("p.aditem-main--middle--price-shipping")
                    
                    # Methode 3: Suche nach Preis im gesamten Element
                    if not price_element:
                        ad_html = ad.inner_html()
                        price_match = re.search(r"(\d[\d\.,]+\s*€)", ad_html)
                        if price_match:
                            price_text = price_match.group(1)
                            price = float(re.sub(r"[^\d,.]", "", price_text).replace(",", "."))
                    
                    # Wenn Preis-Element gefunden wurde
                    if price_element:
                        price_text = price_element.inner_text().strip()
                        # Behandlung von "VB" oder "Zu verschenken"
                        if "VB" in price_text or "zu verschenken" in price_text.lower():
                            price = -1.0
                        else:
                            # Extrahiere numerischen Wert
                            price_match = re.search(r"(\d[\d\.,]+)", price_text)
                            if price_match:
                                price_str = price_match.group(1).replace(".", "").replace(",", ".")
                                try:
                                    price = float(price_str)
                                except ValueError:
                                    price = 0.0
                    
                    # Link extrahieren
                    link = "https://www.kleinanzeigen.de" + ad.query_selector("a").get_attribute("href")
                    
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
                    print(f"Fehler bei Anzeige: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Hauptfehler: {str(e)}")
        finally:
            context.close()
            browser.close()
    
    return results
