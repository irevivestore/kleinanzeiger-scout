from playwright.sync_api import sync_playwright
import re

def scrape_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Realistische Browser-Einstellungen
        page.set_viewport_size({"width": 1280, "height": 800})
        page.set_extra_http_headers({
            "Accept-Language": "de-DE,de;q=0.9",
            "Accept": "text/html,application/xhtml+xml"
        })

        try:
            # Seite mit vollständigem Load aufrufen
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Explizit auf Preiselemente warten
            page.wait_for_selector("p.aditem-main--middle--price-shipping--price", timeout=10000)
            
            # Scrollen um Lazy Loading zu triggern
            page.evaluate("window.scrollBy(0, 500)")
            time.sleep(1)

            # Alle Anzeigen sammeln
            ads = page.query_selector_all("article.aditem")
            
            for ad in ads[:15]:  # Begrenzung für Performance
                try:
                    # Titel extrahieren
                    title = ad.query_selector("a.ellipsis").inner_text().strip()
                    
                    # PREIS mit dem jetzt bekannten Selektor
                    price_element = ad.query_selector("p.aditem-main--middle--price-shipping--price")
                    price = 0.0
                    
                    if price_element:
                        price_text = price_element.inner_text().strip()
                        # Bereinigung des Preis-Textes
                        price_clean = re.sub(r"[^\d,.]", "", price_text).replace(",", ".")
                        try:
                            price = float(price_clean) if price_clean else 0.0
                        except ValueError:
                            price = 0.0
                    
                    # Link
                    relative_link = ad.query_selector("a.ellipsis").get_attribute("href")
                    link = f"https://www.kleinanzeigen.de{relative_link}"
                    
                    # Bild (priorisiert data-src falls vorhanden)
                    img_element = ad.query_selector("img")
                    img = (img_element.get_attribute("data-src") or 
                           img_element.get_attribute("src")) if img_element else ""
                    
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
            print(f"Seitenfehler: {str(e)}")
        finally:
            browser.close()
    
    return results
